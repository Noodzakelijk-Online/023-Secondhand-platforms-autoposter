import csv
import io
import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, Header, HTTPException, Query, Request, Response, UploadFile
from pydantic import ValidationError
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from app.adapters import get_adapter, list_platforms
from app.config import get_settings
from app.database import SessionLocal, get_db
from app.demo import demo_mode_enabled, ensure_demo_user
from app.doctor import run_checks
from app.models import (
    AuditEvent,
    CategoryMapping,
    Listing,
    ListingDraft,
    ListingImage,
    ListingTemplate,
    PlatformAccount,
    PlatformListingMapping,
    PlatformOAuthState,
    PublicationAttempt,
    PublishingJob,
    PublishingJobLog,
    User,
    UserSession,
)
from app.query import apply_pagination, apply_sort, listing_search_filter
from app.rate_limit import check_login_rate_limit, record_failed_login, record_successful_login
from app.schemas import (
    AccountReadiness,
    AccountUsage,
    AnalyticsResult,
    AuditEventOut,
    AuthLogin,
    AuthRegister,
    AuthToken,
    CategoryMappingCreate,
    CategoryMappingOut,
    CategoryMappingUpdate,
    DataExportBundle,
    DataImportBundle,
    DataImportResult,
    ImageOrderUpdate,
    ListingCreate,
    ListingOut,
    ListingQualityResult,
    ListingUpdate,
    OAuthStartResponse,
    PlatformAccountCreate,
    PlatformAccountOut,
    PlatformAccountUpdate,
    PlatformMappingOut,
    PlatformOverrideUpdate,
    PublishingJobOut,
    PublishRequest,
    TemplateCreate,
    TemplateOut,
    TemplateUpdate,
    UserOut,
    ValidationResult,
)
from app.security import (
    create_session,
    hash_password,
    hash_token,
    password_needs_rehash,
    revoke_session,
    verify_password,
)
from app.services.analytics import build_user_analytics
from app.services.audit import record_audit_event
from app.services.jobs import enqueue_publish_job, get_or_create_mapping, process_job, retry_job
from app.services.localization import localization_metadata
from app.services.oauth import consume_ebay_authorization_callback, create_ebay_authorization_url
from app.services.quality import analyze_listing_quality
from app.storage import StoredFile, read_validated_image, safe_filename, store_validated_image

router = APIRouter(prefix="/api")
SENSITIVE_CONNECTION_KEYS = ("password", "secret", "token", "api_key", "apikey", "access_key", "private_key")
LISTING_CSV_FIELDS = [
    "title",
    "description",
    "price_cents",
    "currency",
    "condition",
    "category",
    "location",
    "pickup_allowed",
    "shipping_allowed",
    "shipping_cost_cents",
    "weight_grams",
    "brand",
    "model",
    "color",
    "material",
    "category_attributes_json",
    "notes",
    "internal_notes",
    "tags",
    "status",
    "delivery_options_json",
    "dimensions_json",
]


def get_current_session(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> UserSession:
    settings = get_settings()
    if settings.dev_auto_login:
        if not demo_mode_enabled(settings):
            raise HTTPException(status_code=403, detail="Demo auto-login is only allowed in development")
        user = ensure_demo_user(db)
        return UserSession(
            user_id=user.id,
            token_hash="dev-auto-login",
            expires_at=datetime.now(UTC),
            user=user,
        )

    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    session = (
        db.query(UserSession)
        .options(selectinload(UserSession.user))
        .filter(UserSession.token_hash == hash_token(token))
        .one_or_none()
    )
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    if session.revoked_at is not None:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    expires_at = session.expires_at
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at < datetime.now(UTC):
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    if not session.user.is_active:
        raise HTTPException(status_code=403, detail="User is disabled")
    return session


def get_current_user(session: UserSession = Depends(get_current_session)) -> User:
    return session.user


@router.get("/health", tags=["Health"])
def health() -> dict:
    return {"status": "ok", "time": datetime.now(UTC).isoformat()}


@router.get("/diagnostics", tags=["Diagnostics"])
def diagnostics(db: Session = Depends(get_db)) -> dict:
    doctor = run_checks()
    return {
        "status": doctor["status"],
        "listings": db.query(Listing).count(),
        "jobs": db.query(PublishingJob).count(),
        "platforms": [platform["key"] for platform in list_platforms()],
        "doctor": doctor,
    }


@router.get("/metrics", tags=["Diagnostics"])
def metrics(db: Session = Depends(get_db)) -> dict:
    listing_statuses = dict(db.query(Listing.status, func.count(Listing.id)).group_by(Listing.status).all())
    job_statuses = dict(
        db.query(PublishingJob.status, func.count(PublishingJob.id)).group_by(PublishingJob.status).all()
    )
    return {
        "listings_total": db.query(Listing).count(),
        "publishing_jobs_total": db.query(PublishingJob).count(),
        "users_total": db.query(User).count(),
        "platform_accounts_total": db.query(PlatformAccount).count(),
        "listing_statuses": listing_statuses,
        "publishing_job_statuses": job_statuses,
    }


@router.get("/localization", tags=["Diagnostics"])
def localization() -> dict:
    return localization_metadata(get_settings())


@router.get("/analytics", response_model=AnalyticsResult, tags=["Diagnostics"])
def analytics(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return build_user_analytics(db, user.id)


@router.get("/account/readiness", response_model=AccountReadiness, tags=["Account"])
def account_readiness(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> AccountReadiness:
    listing_ids = [id_ for (id_,) in db.query(Listing.id).filter(Listing.owner_id == user.id).all()]
    job_count = 0
    if listing_ids:
        job_count = db.query(PublishingJob).filter(PublishingJob.listing_id.in_(listing_ids)).count()
    return AccountReadiness(
        user=UserOut.model_validate(user),
        usage=AccountUsage(
            listings=len(listing_ids),
            publishing_jobs=job_count,
            platform_accounts=db.query(PlatformAccount).filter(PlatformAccount.owner_id == user.id).count(),
            templates=db.query(ListingTemplate).filter(ListingTemplate.owner_id == user.id).count(),
            category_mappings=db.query(CategoryMapping).filter(CategoryMapping.owner_id == user.id).count(),
        ),
    )


@router.post("/auth/register", response_model=AuthToken, tags=["Auth"])
def register(payload: AuthRegister, db: Session = Depends(get_db)) -> AuthToken:
    existing = db.query(User).filter(User.email == payload.email.lower()).one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Email is already registered")
    user = User(
        email=payload.email.lower(),
        name=payload.name,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_session(db, user)
    return AuthToken(token=token, user=UserOut.model_validate(user))


@router.post("/auth/login", response_model=AuthToken, tags=["Auth"])
def login(payload: AuthLogin, request: Request, db: Session = Depends(get_db)) -> AuthToken:
    identifier = f"{request.client.host if request.client else 'unknown'}:{payload.email.lower()}"
    check_login_rate_limit(db, identifier)
    user = db.query(User).filter(User.email == payload.email.lower()).one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        record_failed_login(db, identifier)
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if password_needs_rehash(user.password_hash):
        user.password_hash = hash_password(payload.password)
        db.commit()
    record_successful_login(db, identifier)
    token = create_session(db, user)
    return AuthToken(token=token, user=UserOut.model_validate(user))


@router.post("/auth/logout", status_code=204, tags=["Auth"])
def logout(session: UserSession = Depends(get_current_session), db: Session = Depends(get_db)):
    if session.token_hash != "dev-auto-login":
        revoke_session(db, session)
    return None


@router.get("/auth/me", response_model=UserOut, tags=["Auth"])
def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.delete("/auth/me", status_code=204, tags=["Auth"])
def delete_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    delete_user_data(db, user)
    return None


def delete_user_data(db: Session, user: User) -> None:
    user_id = user.id
    listing_ids = [id_ for (id_,) in db.query(Listing.id).filter(Listing.owner_id == user_id).all()]
    job_ids = []
    image_paths = []
    if listing_ids:
        job_ids = [id_ for (id_,) in db.query(PublishingJob.id).filter(PublishingJob.listing_id.in_(listing_ids)).all()]
        image_paths = [
            path
            for (path,) in db.query(ListingImage.storage_path)
            .filter(ListingImage.listing_id.in_(listing_ids))
            .all()
        ]
    record_audit_event(
        db,
        user,
        "account_deleted",
        {
            "listings_deleted": len(listing_ids),
            "jobs_deleted": len(job_ids),
            "images_deleted": len(image_paths),
            "templates_deleted": db.query(ListingTemplate).filter(ListingTemplate.owner_id == user_id).count(),
            "category_mappings_deleted": db.query(CategoryMapping).filter(CategoryMapping.owner_id == user_id).count(),
            "platform_accounts_deleted": db.query(PlatformAccount).filter(PlatformAccount.owner_id == user_id).count(),
            "oauth_states_deleted": db.query(PlatformOAuthState).filter(PlatformOAuthState.user_id == user_id).count(),
        },
    )
    if listing_ids:
        if job_ids:
            db.query(PublicationAttempt).filter(PublicationAttempt.job_id.in_(job_ids)).delete(synchronize_session=False)
            db.query(PublishingJobLog).filter(PublishingJobLog.job_id.in_(job_ids)).delete(synchronize_session=False)
            db.query(PublishingJob).filter(PublishingJob.id.in_(job_ids)).delete(synchronize_session=False)
        db.query(ListingDraft).filter(ListingDraft.listing_id.in_(listing_ids)).delete(synchronize_session=False)
        db.query(PlatformListingMapping).filter(PlatformListingMapping.listing_id.in_(listing_ids)).delete(
            synchronize_session=False
        )
        db.query(ListingImage).filter(ListingImage.listing_id.in_(listing_ids)).delete(synchronize_session=False)
        db.query(Listing).filter(Listing.id.in_(listing_ids)).delete(synchronize_session=False)
        for image_path in image_paths:
            remove_local_file(image_path)
    db.query(ListingTemplate).filter(ListingTemplate.owner_id == user_id).delete(synchronize_session=False)
    db.query(CategoryMapping).filter(CategoryMapping.owner_id == user_id).delete(synchronize_session=False)
    db.query(PlatformAccount).filter(PlatformAccount.owner_id == user_id).delete(synchronize_session=False)
    db.query(PlatformOAuthState).filter(PlatformOAuthState.user_id == user_id).delete(synchronize_session=False)
    db.query(UserSession).filter(UserSession.user_id == user_id).delete(synchronize_session=False)
    db.query(User).filter(User.id == user_id).delete(synchronize_session=False)
    db.commit()


def remove_local_file(path: str) -> None:
    if not path:
        return
    try:
        target = Path(path)
        target.unlink(missing_ok=True)
        parent = target.parent
        if parent.exists() and not any(parent.iterdir()):
            parent.rmdir()
    except OSError:
        return


@router.get("/platforms", tags=["Platforms"])
def platforms() -> list[dict]:
    return list_platforms()


@router.get("/listings", response_model=list[ListingOut], tags=["Listings"])
def list_listings(
    response: Response,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    search: str | None = Query(default=None, max_length=120),
    status: str | None = Query(default=None, max_length=40),
    sort: str = Query(default="-updated_at", pattern="^-?(updated_at|created_at|title|price_cents|status)$"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = (
        db.query(Listing)
        .options(selectinload(Listing.images), selectinload(Listing.platform_mappings))
        .filter(Listing.owner_id == user.id)
    )
    query = listing_search_filter(query, Listing, search)
    if status:
        query = query.filter(Listing.status == status)
    query = apply_sort(
        query,
        Listing,
        sort,
        {
            "updated_at": "updated_at",
            "created_at": "created_at",
            "title": "title",
            "price_cents": "price_cents",
            "status": "status",
            "default": "updated_at",
        },
    )
    return apply_pagination(query, response, limit, offset).all()


@router.post("/listings", response_model=ListingOut, tags=["Listings"])
def create_listing(
    payload: ListingCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    listing = Listing(owner_id=user.id, **payload.model_dump())
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return _load_listing(db, user.id, listing.id)


def _load_listing(db: Session, owner_id: int, listing_id: int) -> Listing:
    listing = (
        db.query(Listing)
        .options(selectinload(Listing.images), selectinload(Listing.platform_mappings))
        .filter(Listing.id == listing_id, Listing.owner_id == owner_id)
        .one_or_none()
    )
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing


@router.get("/listings/{listing_id}", response_model=ListingOut, tags=["Listings"])
def get_listing(
    listing_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _load_listing(db, user.id, listing_id)


@router.patch("/listings/{listing_id}", response_model=ListingOut, tags=["Listings"])
def update_listing(
    listing_id: int,
    payload: ListingUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    listing = _load_listing(db, user.id, listing_id)
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(listing, key, value)
    if data:
        listing.revision += 1
    db.add(ListingDraft(listing_id=listing.id, payload=data, source="manual_save"))
    db.commit()
    return _load_listing(db, user.id, listing_id)


@router.delete("/listings/{listing_id}", status_code=204, tags=["Listings"])
def delete_listing(
    listing_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    listing = _load_listing(db, user.id, listing_id)
    db.delete(listing)
    db.commit()


@router.post("/listings/{listing_id}/duplicate", response_model=ListingOut, tags=["Listings"])
def duplicate_listing(
    listing_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    source = _load_listing(db, user.id, listing_id)
    clone = Listing(
        owner_id=user.id,
        title=f"{source.title} copy".strip(),
        description=source.description,
        price_cents=source.price_cents,
        currency=source.currency,
        condition=source.condition,
        category=source.category,
        location=source.location,
        delivery_options=source.delivery_options,
        pickup_allowed=source.pickup_allowed,
        shipping_allowed=source.shipping_allowed,
        shipping_cost_cents=source.shipping_cost_cents,
        dimensions=source.dimensions,
        weight_grams=source.weight_grams,
        brand=source.brand,
        model=source.model,
        color=source.color,
        material=source.material,
        notes=source.notes,
        internal_notes=source.internal_notes,
        tags=source.tags,
        status="draft",
    )
    db.add(clone)
    db.flush()
    for image in source.images:
        db.add(
            ListingImage(
                listing_id=clone.id,
                filename=image.filename,
                storage_path=image.storage_path,
                content_type=image.content_type,
                file_size=image.file_size,
                checksum_sha256=image.checksum_sha256,
                position=image.position,
            )
        )
    db.commit()
    return _load_listing(db, user.id, clone.id)


@router.post("/listings/{listing_id}/images", response_model=ListingOut, tags=["Images"])
async def upload_image(
    listing_id: int,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    listing = _load_listing(db, user.id, listing_id)
    validated = await read_validated_image(file)
    duplicate = (
        db.query(ListingImage)
        .filter(
            ListingImage.listing_id == listing.id,
            ListingImage.checksum_sha256 == validated.checksum_sha256,
        )
        .one_or_none()
    )
    if duplicate:
        return _load_listing(db, user.id, listing.id)
    target = store_validated_image(validated, listing.id)
    stored_file = StoredFile(
        original_filename=validated.original_filename,
        storage_path=str(target),
        content_type=validated.content_type,
        file_size=validated.file_size,
        checksum_sha256=validated.checksum_sha256,
    )
    position = len(listing.images)
    db.add(
        ListingImage(
            listing_id=listing.id,
            filename=stored_file.original_filename,
            storage_path=stored_file.storage_path,
            content_type=stored_file.content_type,
            file_size=stored_file.file_size,
            checksum_sha256=stored_file.checksum_sha256,
            position=position,
        )
    )
    db.commit()
    return _load_listing(db, user.id, listing.id)


@router.patch("/listings/{listing_id}/images/order", response_model=ListingOut, tags=["Images"])
def reorder_images(
    listing_id: int,
    payload: ImageOrderUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    listing = _load_listing(db, user.id, listing_id)
    images = {image.id: image for image in listing.images}
    for position, image_id in enumerate(payload.image_ids):
        if image_id in images:
            images[image_id].position = position
    db.commit()
    return _load_listing(db, user.id, listing.id)


@router.delete("/listings/{listing_id}/images/{image_id}", response_model=ListingOut, tags=["Images"])
def delete_image(
    listing_id: int,
    image_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    listing = _load_listing(db, user.id, listing_id)
    image = next((item for item in listing.images if item.id == image_id), None)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    db.delete(image)
    db.commit()
    return _load_listing(db, user.id, listing.id)


@router.post("/listings/{listing_id}/platforms", response_model=PlatformMappingOut, tags=["Platform mappings"])
def save_platform_override(
    listing_id: int,
    payload: PlatformOverrideUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _load_listing(db, user.id, listing_id)
    get_adapter(payload.platform)
    mapping = get_or_create_mapping(db, listing_id, payload.platform)
    mapping.overrides = payload.overrides
    mapping.status = "draft" if payload.selected else "skipped"
    db.commit()
    db.refresh(mapping)
    return mapping


@router.get("/listings/{listing_id}/validate", response_model=list[ValidationResult], tags=["Publishing"])
def validate_listing(
    listing_id: int,
    platform: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    listing = _load_listing(db, user.id, listing_id)
    platforms_to_validate = [platform] if platform else [item["key"] for item in list_platforms()]
    results = []
    for platform_key in platforms_to_validate:
        adapter = get_adapter(platform_key)
        mapping = get_or_create_mapping(db, listing.id, platform_key)
        overrides = effective_platform_overrides(db, user.id, listing, platform_key, mapping.overrides)
        outcome = adapter.validate_listing(listing, overrides)
        mapping.validation_errors = outcome.missing_fields
        mapping.status = "draft" if outcome.ready else "needs_user_action"
        results.append(
            ValidationResult(
                platform=platform_key,
                ready=outcome.ready,
                missing_fields=outcome.missing_fields,
                warnings=outcome.warnings,
                mapped_fields=outcome.mapped_fields,
            )
        )
    db.commit()
    return results


@router.get("/listings/{listing_id}/quality", response_model=ListingQualityResult, tags=["Listings"])
def listing_quality(
    listing_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    listing = _load_listing(db, user.id, listing_id)
    return analyze_listing_quality(listing)


def effective_platform_overrides(
    db: Session,
    owner_id: int,
    listing: Listing,
    platform: str,
    overrides: dict,
) -> dict:
    effective = dict(overrides or {})
    if "category" in effective and effective["category"]:
        return effective
    category_mapping = (
        db.query(CategoryMapping)
        .filter(
            CategoryMapping.owner_id == owner_id,
            CategoryMapping.source_category == listing.category,
            CategoryMapping.platform == platform,
        )
        .one_or_none()
    )
    if category_mapping:
        effective["category"] = category_mapping.platform_category
    return effective


@router.post("/listings/{listing_id}/publish", response_model=list[PublishingJobOut], tags=["Publishing"])
def publish_listing(
    listing_id: int,
    payload: PublishRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    listing = _load_listing(db, user.id, listing_id)
    if payload.force_new_revision:
        listing.revision += 1
        db.add(ListingDraft(listing_id=listing.id, payload={"force_new_revision": True}, source="regenerate_package"))
        db.commit()
        listing = _load_listing(db, user.id, listing_id)
    jobs = []
    for platform_key in payload.platforms:
        get_adapter(platform_key)
        account_id = payload.account_ids.get(platform_key)
        job = enqueue_publish_job(db, listing, platform_key, account_id)
        if payload.process_now and get_settings().job_process_inline:
            job = process_job(db, job.id)
        jobs.append(job)
    return jobs


def process_job_task(job_id: int) -> None:
    db = SessionLocal()
    try:
        process_job(db, job_id)
    finally:
        db.close()


@router.get("/jobs", response_model=list[PublishingJobOut], tags=["Jobs"])
def list_jobs(
    response: Response,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    platform: str | None = Query(default=None, max_length=80),
    status: str | None = Query(default=None, max_length=40),
    sort: str = Query(default="-created_at", pattern="^-?(created_at|started_at|finished_at|status|platform)$"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    listing_ids = [id_ for (id_,) in db.query(Listing.id).filter(Listing.owner_id == user.id).all()]
    query = (
        db.query(PublishingJob)
        .options(selectinload(PublishingJob.logs))
        .filter(PublishingJob.listing_id.in_(listing_ids))
    )
    if platform:
        query = query.filter(PublishingJob.platform == platform)
    if status:
        query = query.filter(PublishingJob.status == status)
    query = apply_sort(
        query,
        PublishingJob,
        sort,
        {
            "created_at": "created_at",
            "started_at": "started_at",
            "finished_at": "finished_at",
            "status": "status",
            "platform": "platform",
            "default": "created_at",
        },
    )
    return apply_pagination(query, response, limit, offset).all()


@router.get("/jobs/{job_id}", response_model=PublishingJobOut, tags=["Jobs"])
def get_job(job_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    job = (
        db.query(PublishingJob)
        .options(selectinload(PublishingJob.logs), selectinload(PublishingJob.listing))
        .filter(PublishingJob.id == job_id)
        .one_or_none()
    )
    if not job or job.listing.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/jobs/{job_id}/retry", response_model=PublishingJobOut, tags=["Jobs"])
def retry_publish_job(job_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    job = (
        db.query(PublishingJob)
        .options(selectinload(PublishingJob.listing))
        .filter(PublishingJob.id == job_id)
        .one_or_none()
    )
    if not job or job.listing.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Job not found")
    return retry_job(db, job)


@router.get("/accounts", response_model=list[PlatformAccountOut], tags=["Accounts"])
def list_accounts(
    response: Response,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    platform: str | None = Query(default=None, max_length=80),
    status: str | None = Query(default=None, max_length=40),
    sort: str = Query(default="-created_at", pattern="^-?(created_at|updated_at|display_name|platform|status)$"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(PlatformAccount).filter(PlatformAccount.owner_id == user.id)
    if platform:
        query = query.filter(PlatformAccount.platform == platform)
    if status:
        query = query.filter(PlatformAccount.status == status)
    query = apply_sort(
        query,
        PlatformAccount,
        sort,
        {
            "created_at": "created_at",
            "updated_at": "updated_at",
            "display_name": "display_name",
            "platform": "platform",
            "status": "status",
            "default": "created_at",
        },
    )
    return apply_pagination(query, response, limit, offset).all()


@router.post("/accounts", response_model=PlatformAccountOut, tags=["Accounts"])
def create_account(
    payload: PlatformAccountCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_adapter(payload.platform)
    account_data = payload.model_dump()
    account_data["connection_data"] = _sanitize_connection_data(account_data["connection_data"])
    account = PlatformAccount(owner_id=user.id, **account_data)
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@router.patch("/accounts/{account_id}", response_model=PlatformAccountOut, tags=["Accounts"])
def update_account(
    account_id: int,
    payload: PlatformAccountUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    account = (
        db.query(PlatformAccount)
        .filter(PlatformAccount.id == account_id, PlatformAccount.owner_id == user.id)
        .one_or_none()
    )
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    data = payload.model_dump(exclude_unset=True)
    if "platform" in data:
        get_adapter(data["platform"])
    if "connection_data" in data:
        data["connection_data"] = _sanitize_connection_data(data["connection_data"] or {})
    for key, value in data.items():
        setattr(account, key, value)
    db.commit()
    db.refresh(account)
    return account


@router.delete("/accounts/{account_id}", status_code=204, tags=["Accounts"])
def delete_account(account_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    account = (
        db.query(PlatformAccount)
        .filter(PlatformAccount.id == account_id, PlatformAccount.owner_id == user.id)
        .one_or_none()
    )
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    db.delete(account)
    db.commit()


@router.post("/accounts/ebay/oauth/start", response_model=OAuthStartResponse, tags=["Accounts"])
def start_ebay_oauth(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    authorization_url, expires_at = create_ebay_authorization_url(db, user, get_settings())
    return OAuthStartResponse(authorization_url=authorization_url, expires_at=expires_at)


@router.get("/accounts/ebay/oauth/callback", response_model=PlatformAccountOut, tags=["Accounts"])
def ebay_oauth_callback(
    state: str = Query(..., min_length=1),
    code: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    return consume_ebay_authorization_callback(db, state, code, get_settings())


@router.get("/templates", response_model=list[TemplateOut], tags=["Templates"])
def list_templates(
    response: Response,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    platform: str | None = Query(default=None, max_length=80),
    variant: str | None = Query(default=None, max_length=80),
    search: str | None = Query(default=None, max_length=120),
    sort: str = Query(default="name", pattern="^-?(name|variant|platform|created_at|updated_at)$"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(ListingTemplate).filter(ListingTemplate.owner_id == user.id)
    if platform:
        query = query.filter(ListingTemplate.platform == platform)
    if variant:
        query = query.filter(ListingTemplate.variant == variant)
    if search:
        term = f"%{search.strip()}%"
        query = query.filter((ListingTemplate.name.ilike(term)) | (ListingTemplate.variant.ilike(term)))
    query = apply_sort(
        query,
        ListingTemplate,
        sort,
        {
            "name": "name",
            "variant": "variant",
            "platform": "platform",
            "created_at": "created_at",
            "updated_at": "updated_at",
            "default": "name",
        },
    )
    return apply_pagination(query, response, limit, offset).all()


@router.post("/templates", response_model=TemplateOut, tags=["Templates"])
def create_template(
    payload: TemplateCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    template = ListingTemplate(owner_id=user.id, **payload.model_dump())
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@router.patch("/templates/{template_id}", response_model=TemplateOut, tags=["Templates"])
def update_template(
    template_id: int,
    payload: TemplateUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    template = (
        db.query(ListingTemplate)
        .filter(ListingTemplate.id == template_id, ListingTemplate.owner_id == user.id)
        .one_or_none()
    )
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    for field_name, value in payload.model_dump(exclude_unset=True).items():
        setattr(template, field_name, value)
    db.commit()
    db.refresh(template)
    return template


@router.delete("/templates/{template_id}", status_code=204, tags=["Templates"])
def delete_template(template_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    template = (
        db.query(ListingTemplate)
        .filter(ListingTemplate.id == template_id, ListingTemplate.owner_id == user.id)
        .one_or_none()
    )
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    db.delete(template)
    db.commit()


@router.get("/category-mappings", response_model=list[CategoryMappingOut], tags=["Category mappings"])
def list_category_mappings(
    response: Response,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    platform: str | None = Query(default=None, max_length=80),
    source_category: str | None = Query(default=None, max_length=120),
    sort: str = Query(
        default="source_category",
        pattern="^-?(source_category|platform|platform_category|created_at|updated_at)$",
    ),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(CategoryMapping).filter(CategoryMapping.owner_id == user.id)
    if platform:
        query = query.filter(CategoryMapping.platform == platform)
    if source_category:
        query = query.filter(CategoryMapping.source_category.ilike(f"%{source_category.strip()}%"))
    query = apply_sort(
        query,
        CategoryMapping,
        sort,
        {
            "source_category": "source_category",
            "platform": "platform",
            "platform_category": "platform_category",
            "created_at": "created_at",
            "updated_at": "updated_at",
            "default": "source_category",
        },
    )
    return apply_pagination(query, response, limit, offset).all()


@router.post("/category-mappings", response_model=CategoryMappingOut, tags=["Category mappings"])
def create_category_mapping(
    payload: CategoryMappingCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_adapter(payload.platform)
    existing = (
        db.query(CategoryMapping)
        .filter(
            CategoryMapping.owner_id == user.id,
            CategoryMapping.source_category == payload.source_category,
            CategoryMapping.platform == payload.platform,
        )
        .one_or_none()
    )
    if existing:
        existing.platform_category = payload.platform_category
        db.commit()
        db.refresh(existing)
        return existing
    category_mapping = CategoryMapping(owner_id=user.id, **payload.model_dump())
    db.add(category_mapping)
    db.commit()
    db.refresh(category_mapping)
    return category_mapping


@router.patch("/category-mappings/{mapping_id}", response_model=CategoryMappingOut, tags=["Category mappings"])
def update_category_mapping(
    mapping_id: int,
    payload: CategoryMappingUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    category_mapping = (
        db.query(CategoryMapping)
        .filter(CategoryMapping.id == mapping_id, CategoryMapping.owner_id == user.id)
        .one_or_none()
    )
    if not category_mapping:
        raise HTTPException(status_code=404, detail="Category mapping not found")
    data = payload.model_dump(exclude_unset=True)
    if "platform" in data:
        get_adapter(data["platform"])
    for key, value in data.items():
        setattr(category_mapping, key, value)
    db.commit()
    db.refresh(category_mapping)
    return category_mapping


@router.delete("/category-mappings/{mapping_id}", status_code=204, tags=["Category mappings"])
def delete_category_mapping(
    mapping_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    category_mapping = (
        db.query(CategoryMapping)
        .filter(CategoryMapping.id == mapping_id, CategoryMapping.owner_id == user.id)
        .one_or_none()
    )
    if not category_mapping:
        raise HTTPException(status_code=404, detail="Category mapping not found")
    db.delete(category_mapping)
    db.commit()


@router.get("/audit-events", response_model=list[AuditEventOut], tags=["Privacy"])
def list_audit_events(
    response: Response,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    action: str | None = Query(default=None, max_length=80),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(AuditEvent).filter(AuditEvent.user_id == user.id)
    if action:
        query = query.filter(AuditEvent.action == action)
    query = query.order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc())
    return apply_pagination(query, response, limit, offset).all()


def _adapter_available(platform: str) -> bool:
    try:
        get_adapter(platform)
    except ValueError:
        return False
    return True


def _sanitize_connection_data(value):
    if isinstance(value, dict):
        clean = {}
        for key, nested_value in value.items():
            normalized = key.lower().replace("-", "_")
            if any(secret_key in normalized for secret_key in SENSITIVE_CONNECTION_KEYS):
                continue
            clean[key] = _sanitize_connection_data(nested_value)
        return clean
    if isinstance(value, list):
        return [_sanitize_connection_data(item) for item in value]
    return value


def _export_listing(listing: Listing) -> dict:
    payload = {field: getattr(listing, field) for field in ListingCreate.model_fields}
    payload["revision"] = listing.revision
    payload["images"] = [
        {
            "filename": image.filename,
            "storage_path": image.storage_path,
            "content_type": image.content_type,
            "file_size": image.file_size,
            "checksum_sha256": image.checksum_sha256,
            "position": image.position,
        }
        for image in listing.images
    ]
    payload["platform_mappings"] = [
        {
            "platform": mapping.platform,
            "platform_listing_id": mapping.platform_listing_id,
            "status": mapping.status,
            "platform_url": mapping.platform_url,
            "overrides": mapping.overrides or {},
            "validation_errors": mapping.validation_errors or [],
            "last_published_at": mapping.last_published_at,
        }
        for mapping in listing.platform_mappings
    ]
    return payload


def _listing_csv_row(listing: Listing) -> dict[str, str]:
    return {
        "title": listing.title or "",
        "description": listing.description or "",
        "price_cents": str(listing.price_cents or 0),
        "currency": listing.currency or "EUR",
        "condition": listing.condition or "used",
        "category": listing.category or "",
        "location": listing.location or "",
        "pickup_allowed": _format_csv_bool(listing.pickup_allowed),
        "shipping_allowed": _format_csv_bool(listing.shipping_allowed),
        "shipping_cost_cents": str(listing.shipping_cost_cents or 0),
        "weight_grams": str(listing.weight_grams or 0),
        "brand": listing.brand or "",
        "model": listing.model or "",
        "color": listing.color or "",
        "material": listing.material or "",
        "category_attributes_json": json.dumps(listing.category_attributes or {}, sort_keys=True),
        "notes": listing.notes or "",
        "internal_notes": listing.internal_notes or "",
        "tags": ", ".join(listing.tags or []),
        "status": listing.status or "draft",
        "delivery_options_json": json.dumps(listing.delivery_options or {}, sort_keys=True),
        "dimensions_json": json.dumps(listing.dimensions or {}, sort_keys=True),
    }


def _format_csv_bool(value: bool) -> str:
    return "true" if value else "false"


def _parse_csv_bool(value: str) -> bool:
    normalized = (value or "").strip().casefold()
    return normalized in {"1", "true", "yes", "y", "on"}


def _parse_csv_int(value: str, field: str) -> int:
    if value is None or value == "":
        return 0
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{field} must be an integer") from exc


def _parse_csv_json_object(value: str, field: str) -> dict:
    if not value:
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{field} must contain valid JSON") from exc
    if not isinstance(parsed, dict):
        raise ValueError(f"{field} must contain a JSON object")
    return parsed


def _parse_csv_tags(value: str) -> list[str]:
    return [tag.strip() for tag in (value or "").split(",") if tag.strip()]


def _listing_from_csv_row(row: dict[str, str]) -> ListingCreate:
    payload = {
        "title": row.get("title", ""),
        "description": row.get("description", ""),
        "price_cents": _parse_csv_int(row.get("price_cents", ""), "price_cents"),
        "currency": row.get("currency") or "EUR",
        "condition": row.get("condition") or "used",
        "category": row.get("category", ""),
        "location": row.get("location", ""),
        "pickup_allowed": _parse_csv_bool(row.get("pickup_allowed", "true")),
        "shipping_allowed": _parse_csv_bool(row.get("shipping_allowed", "false")),
        "shipping_cost_cents": _parse_csv_int(row.get("shipping_cost_cents", ""), "shipping_cost_cents"),
        "weight_grams": _parse_csv_int(row.get("weight_grams", ""), "weight_grams"),
        "brand": row.get("brand", ""),
        "model": row.get("model", ""),
        "color": row.get("color", ""),
        "material": row.get("material", ""),
        "category_attributes": _parse_csv_json_object(
            row.get("category_attributes_json", ""),
            "category_attributes_json",
        ),
        "notes": row.get("notes", ""),
        "internal_notes": row.get("internal_notes", ""),
        "tags": _parse_csv_tags(row.get("tags", "")),
        "status": row.get("status") or "draft",
        "delivery_options": _parse_csv_json_object(row.get("delivery_options_json", ""), "delivery_options_json"),
        "dimensions": _parse_csv_json_object(row.get("dimensions_json", ""), "dimensions_json"),
    }
    return ListingCreate.model_validate(payload)


def _image_export_archive(listings: list[Listing]) -> tuple[bytes, dict]:
    settings = get_settings()
    upload_root = settings.upload_path.resolve()
    manifest = {
        "version": "1",
        "exported_at": datetime.now(UTC).isoformat(),
        "images": [],
        "missing": [],
    }
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for listing in listings:
            for image in listing.images:
                resolved_path = Path(image.storage_path).resolve()
                entry = {
                    "listing_id": listing.id,
                    "listing_title": listing.title,
                    "filename": image.filename,
                    "content_type": image.content_type,
                    "file_size": image.file_size,
                    "checksum_sha256": image.checksum_sha256,
                    "position": image.position,
                }
                try:
                    resolved_path.relative_to(upload_root)
                except ValueError:
                    manifest["missing"].append({**entry, "reason": "outside_upload_directory"})
                    continue
                if not resolved_path.exists():
                    manifest["missing"].append({**entry, "reason": "file_missing"})
                    continue
                archive_name = (
                    f"listing-{listing.id}/"
                    f"{image.position:03d}-{image.id}-{safe_filename(image.filename or resolved_path.name)}"
                )
                archive.write(resolved_path, archive_name)
                manifest["images"].append({**entry, "archive_path": archive_name})
        archive.writestr("manifest.json", json.dumps(manifest, indent=2, sort_keys=True))
    return buffer.getvalue(), manifest


@router.get("/export", response_model=DataExportBundle, tags=["Data portability"])
def export_data(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    listings = (
        db.query(Listing)
        .options(selectinload(Listing.images), selectinload(Listing.platform_mappings))
        .filter(Listing.owner_id == user.id)
        .order_by(Listing.created_at.asc())
        .all()
    )
    accounts = db.query(PlatformAccount).filter(PlatformAccount.owner_id == user.id).order_by(PlatformAccount.id).all()
    templates = db.query(ListingTemplate).filter(ListingTemplate.owner_id == user.id).order_by(ListingTemplate.id).all()
    category_mappings = (
        db.query(CategoryMapping).filter(CategoryMapping.owner_id == user.id).order_by(CategoryMapping.id).all()
    )
    bundle = {
        "version": "1",
        "exported_at": datetime.now(UTC),
        "user": user,
        "listings": [_export_listing(listing) for listing in listings],
        "platform_accounts": [
            {
                "platform": account.platform,
                "display_name": account.display_name,
                "mode": account.mode,
                "status": account.status,
                "connection_data": _sanitize_connection_data(account.connection_data or {}),
            }
            for account in accounts
        ],
        "templates": [
            {"name": template.name, "variant": template.variant, "platform": template.platform, "body": template.body}
            for template in templates
        ],
        "category_mappings": [
            {
                "source_category": category_mapping.source_category,
                "platform": category_mapping.platform,
                "platform_category": category_mapping.platform_category,
            }
            for category_mapping in category_mappings
        ],
    }
    record_audit_event(
        db,
        user,
        "data_exported",
        {
            "listings": len(listings),
            "platform_accounts": len(accounts),
            "templates": len(templates),
            "category_mappings": len(category_mappings),
        },
    )
    db.commit()
    return bundle


@router.get("/export/listings.csv", tags=["Data portability"])
def export_listings_csv(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    listings = (
        db.query(Listing)
        .filter(Listing.owner_id == user.id)
        .order_by(Listing.created_at.asc())
        .all()
    )
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=LISTING_CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    for listing in listings:
        writer.writerow(_listing_csv_row(listing))
    record_audit_event(db, user, "listings_csv_exported", {"listings": len(listings)})
    db.commit()
    return Response(
        content=output.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="autoposter-listings.csv"'},
    )


@router.post("/import/listings.csv", response_model=DataImportResult, tags=["Data portability"])
async def import_listings_csv(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    content = await file.read(2_000_000)
    if not content:
        raise HTTPException(status_code=422, detail="CSV file is empty")
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise HTTPException(status_code=422, detail="CSV file must include a header row")
    missing_fields = set(LISTING_CSV_FIELDS) - set(reader.fieldnames)
    if missing_fields:
        raise HTTPException(status_code=422, detail=f"CSV file is missing fields: {', '.join(sorted(missing_fields))}")

    result = DataImportResult()
    for row_number, row in enumerate(reader, start=2):
        try:
            listing_payload = _listing_from_csv_row(row)
        except (ValidationError, ValueError) as exc:
            raise HTTPException(status_code=422, detail=f"CSV row {row_number}: {exc}") from exc
        db.add(Listing(owner_id=user.id, **listing_payload.model_dump()))
        result.listings_created += 1
    record_audit_event(db, user, "listings_csv_imported", {"listings_created": result.listings_created})
    db.commit()
    return result


@router.get("/export/images.zip", tags=["Data portability"])
def export_images_zip(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    listings = (
        db.query(Listing)
        .options(selectinload(Listing.images))
        .filter(Listing.owner_id == user.id)
        .order_by(Listing.created_at.asc())
        .all()
    )
    archive_bytes, manifest = _image_export_archive(listings)
    record_audit_event(
        db,
        user,
        "images_exported",
        {"images": len(manifest["images"]), "missing": len(manifest["missing"])},
    )
    db.commit()
    return Response(
        content=archive_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="autoposter-images.zip"'},
    )


@router.post("/import", response_model=DataImportResult, tags=["Data portability"])
def import_data(
    payload: DataImportBundle,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = DataImportResult()

    for account_payload in payload.platform_accounts:
        if not _adapter_available(account_payload.platform):
            result.skipped += 1
            continue
        account = (
            db.query(PlatformAccount)
            .filter(
                PlatformAccount.owner_id == user.id,
                PlatformAccount.platform == account_payload.platform,
                PlatformAccount.display_name == account_payload.display_name,
            )
            .one_or_none()
        )
        if account:
            account.mode = account_payload.mode
            account.status = account_payload.status
            account.connection_data = _sanitize_connection_data(account_payload.connection_data)
            result.platform_accounts_updated += 1
        else:
            account_data = account_payload.model_dump()
            account_data["connection_data"] = _sanitize_connection_data(account_data["connection_data"])
            db.add(PlatformAccount(owner_id=user.id, **account_data))
            result.platform_accounts_created += 1

    for template_payload in payload.templates:
        template = (
            db.query(ListingTemplate)
            .filter(
                ListingTemplate.owner_id == user.id,
                ListingTemplate.name == template_payload.name,
                ListingTemplate.variant == template_payload.variant,
                ListingTemplate.platform == template_payload.platform,
            )
            .one_or_none()
        )
        if template:
            template.body = template_payload.body
            template.variant = template_payload.variant
            result.templates_updated += 1
        else:
            db.add(ListingTemplate(owner_id=user.id, **template_payload.model_dump()))
            result.templates_created += 1

    for category_payload in payload.category_mappings:
        if not _adapter_available(category_payload.platform):
            result.skipped += 1
            continue
        category_mapping = (
            db.query(CategoryMapping)
            .filter(
                CategoryMapping.owner_id == user.id,
                CategoryMapping.source_category == category_payload.source_category,
                CategoryMapping.platform == category_payload.platform,
            )
            .one_or_none()
        )
        if category_mapping:
            category_mapping.platform_category = category_payload.platform_category
            result.category_mappings_updated += 1
        else:
            db.add(CategoryMapping(owner_id=user.id, **category_payload.model_dump()))
            result.category_mappings_created += 1

    for listing_payload in payload.listings:
        listing_data = listing_payload.model_dump(exclude={"platform_mappings"})
        listing = Listing(owner_id=user.id, **listing_data)
        db.add(listing)
        db.flush()
        result.listings_created += 1
        for mapping_payload in listing_payload.platform_mappings:
            if not _adapter_available(mapping_payload.platform):
                result.skipped += 1
                continue
            db.add(
                PlatformListingMapping(
                    listing_id=listing.id,
                    platform=mapping_payload.platform,
                    status="draft",
                    overrides=mapping_payload.overrides,
                    validation_errors=[],
                )
            )
            result.platform_mappings_created += 1

    record_audit_event(
        db,
        user,
        "data_imported",
        result.model_dump(),
    )
    db.commit()
    return result
