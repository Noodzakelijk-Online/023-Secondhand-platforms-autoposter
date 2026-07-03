from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, Header, HTTPException, Query, Request, Response, UploadFile
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
    PublicationAttempt,
    PublishingJob,
    PublishingJobLog,
    User,
    UserSession,
)
from app.query import apply_pagination, apply_sort, listing_search_filter
from app.rate_limit import check_login_rate_limit, record_failed_login, record_successful_login
from app.schemas import (
    AuthLogin,
    AuthRegister,
    AuthToken,
    AuditEventOut,
    CategoryMappingCreate,
    CategoryMappingOut,
    CategoryMappingUpdate,
    DataExportBundle,
    DataImportBundle,
    DataImportResult,
    ImageOrderUpdate,
    ListingCreate,
    ListingOut,
    ListingUpdate,
    ManualCompletionRequest,
    PlatformAccountCreate,
    PlatformAccountOut,
    PlatformMappingOut,
    PlatformOverrideUpdate,
    PublishingJobOut,
    PublishRequest,
    TemplateCreate,
    TemplateOut,
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
from app.services.jobs import enqueue_publish_job, get_or_create_mapping, process_job, retry_job
from app.storage import StoredFile, read_validated_image, store_validated_image

router = APIRouter(prefix="/api")
SENSITIVE_CONNECTION_KEYS = ("password", "secret", "token", "api_key", "apikey", "access_key", "private_key")


def add_audit_event(
    db: Session,
    *,
    owner_id: int | None,
    actor_id: int | None,
    event_type: str,
    resource_type: str,
    resource_id: str | int | None = None,
    message: str = "",
    details: dict | None = None,
) -> None:
    db.add(
        AuditEvent(
            owner_id=owner_id,
            actor_id=actor_id,
            event_type=event_type,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id is not None else None,
            message=message,
            details=details or {},
        )
    )


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


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "time": datetime.now(UTC).isoformat()}


@router.get("/diagnostics")
def diagnostics(db: Session = Depends(get_db)) -> dict:
    doctor = run_checks()
    return {
        "status": doctor["status"],
        "listings": db.query(Listing).count(),
        "jobs": db.query(PublishingJob).count(),
        "platforms": [platform["key"] for platform in list_platforms()],
        "doctor": doctor,
    }


@router.post("/auth/register", response_model=AuthToken)
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


@router.post("/auth/login", response_model=AuthToken)
def login(payload: AuthLogin, request: Request, db: Session = Depends(get_db)) -> AuthToken:
    identifier = f"{request.client.host if request.client else 'unknown'}:{payload.email.lower()}"
    check_login_rate_limit(identifier)
    user = db.query(User).filter(User.email == payload.email.lower()).one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        record_failed_login(identifier)
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if password_needs_rehash(user.password_hash):
        user.password_hash = hash_password(payload.password)
        db.commit()
    record_successful_login(identifier)
    token = create_session(db, user)
    return AuthToken(token=token, user=UserOut.model_validate(user))


@router.post("/auth/logout", status_code=204)
def logout(session: UserSession = Depends(get_current_session), db: Session = Depends(get_db)):
    if session.token_hash != "dev-auto-login":
        revoke_session(db, session)
    return None


@router.get("/auth/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.get("/audit-events", response_model=list[AuditEventOut])
def list_audit_events(
    response: Response,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    event_type: str | None = Query(default=None, max_length=80),
    resource_type: str | None = Query(default=None, max_length=80),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(AuditEvent).filter(AuditEvent.owner_id == user.id)
    if event_type:
        query = query.filter(AuditEvent.event_type == event_type)
    if resource_type:
        query = query.filter(AuditEvent.resource_type == resource_type)
    query = query.order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc())
    return apply_pagination(query, response, limit, offset).all()


@router.delete("/auth/me", status_code=204)
def delete_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    add_audit_event(
        db,
        owner_id=user.id,
        actor_id=user.id,
        event_type="account_deleted",
        resource_type="user",
        resource_id=user.id,
        message="User requested self-service account deletion.",
        details={"retained_after_delete": True},
    )
    db.flush()
    delete_user_data(db, user.id)
    return None


def delete_user_data(db: Session, user_id: int) -> None:
    listing_ids = [id_ for (id_,) in db.query(Listing.id).filter(Listing.owner_id == user_id).all()]
    job_ids = []
    if listing_ids:
        job_ids = [id_ for (id_,) in db.query(PublishingJob.id).filter(PublishingJob.listing_id.in_(listing_ids)).all()]
        image_paths = [
            path
            for (path,) in db.query(ListingImage.storage_path)
            .filter(ListingImage.listing_id.in_(listing_ids))
            .all()
        ]
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


@router.get("/platforms")
def platforms() -> list[dict]:
    return list_platforms()


@router.get("/listings", response_model=list[ListingOut])
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


@router.post("/listings", response_model=ListingOut)
def create_listing(
    payload: ListingCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    listing = Listing(owner_id=user.id, **payload.model_dump())
    db.add(listing)
    db.flush()
    add_audit_event(
        db,
        owner_id=user.id,
        actor_id=user.id,
        event_type="listing_created",
        resource_type="listing",
        resource_id=listing.id,
        message="Listing created.",
    )
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


@router.get("/listings/{listing_id}", response_model=ListingOut)
def get_listing(
    listing_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _load_listing(db, user.id, listing_id)


@router.patch("/listings/{listing_id}", response_model=ListingOut)
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
    add_audit_event(
        db,
        owner_id=user.id,
        actor_id=user.id,
        event_type="listing_updated",
        resource_type="listing",
        resource_id=listing.id,
        message="Listing updated.",
        details={"fields": sorted(data.keys())},
    )
    db.commit()
    return _load_listing(db, user.id, listing_id)


@router.delete("/listings/{listing_id}", status_code=204)
def delete_listing(
    listing_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    listing = _load_listing(db, user.id, listing_id)
    add_audit_event(
        db,
        owner_id=user.id,
        actor_id=user.id,
        event_type="listing_deleted",
        resource_type="listing",
        resource_id=listing.id,
        message="Listing deleted.",
    )
    db.delete(listing)
    db.commit()


@router.post("/listings/{listing_id}/duplicate", response_model=ListingOut)
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
    add_audit_event(
        db,
        owner_id=user.id,
        actor_id=user.id,
        event_type="listing_duplicated",
        resource_type="listing",
        resource_id=clone.id,
        message="Listing duplicated.",
        details={"source_listing_id": source.id},
    )
    db.commit()
    return _load_listing(db, user.id, clone.id)


@router.post("/listings/{listing_id}/images", response_model=ListingOut)
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
    add_audit_event(
        db,
        owner_id=user.id,
        actor_id=user.id,
        event_type="image_uploaded",
        resource_type="listing",
        resource_id=listing.id,
        message="Listing image uploaded.",
        details={
            "filename": stored_file.original_filename,
            "content_type": stored_file.content_type,
            "file_size": stored_file.file_size,
            "checksum_sha256": stored_file.checksum_sha256,
        },
    )
    db.commit()
    return _load_listing(db, user.id, listing.id)


@router.patch("/listings/{listing_id}/images/order", response_model=ListingOut)
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
    add_audit_event(
        db,
        owner_id=user.id,
        actor_id=user.id,
        event_type="images_reordered",
        resource_type="listing",
        resource_id=listing.id,
        message="Listing images reordered.",
        details={"image_ids": payload.image_ids},
    )
    db.commit()
    return _load_listing(db, user.id, listing.id)


@router.delete("/listings/{listing_id}/images/{image_id}", response_model=ListingOut)
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
    add_audit_event(
        db,
        owner_id=user.id,
        actor_id=user.id,
        event_type="image_deleted",
        resource_type="listing",
        resource_id=listing.id,
        message="Listing image deleted.",
        details={"image_id": image.id, "filename": image.filename},
    )
    db.delete(image)
    db.commit()
    return _load_listing(db, user.id, listing.id)


@router.post("/listings/{listing_id}/platforms", response_model=PlatformMappingOut)
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
    add_audit_event(
        db,
        owner_id=user.id,
        actor_id=user.id,
        event_type="platform_override_saved",
        resource_type="platform_mapping",
        resource_id=mapping.id,
        message="Platform override saved.",
        details={"listing_id": listing_id, "platform": payload.platform, "selected": payload.selected},
    )
    db.commit()
    db.refresh(mapping)
    return mapping


@router.get("/listings/{listing_id}/validate", response_model=list[ValidationResult])
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


@router.post("/listings/{listing_id}/publish", response_model=list[PublishingJobOut])
def publish_listing(
    listing_id: int,
    payload: PublishRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    listing = _load_listing(db, user.id, listing_id)
    jobs = []
    for platform_key in payload.platforms:
        get_adapter(platform_key)
        account_id = payload.account_ids.get(platform_key)
        job = enqueue_publish_job(db, listing, platform_key, account_id)
        add_audit_event(
            db,
            owner_id=user.id,
            actor_id=user.id,
            event_type="publish_job_queued",
            resource_type="publishing_job",
            resource_id=job.id,
            message="Publishing job queued or reused.",
            details={"listing_id": listing.id, "platform": platform_key, "operation_mode": job.operation_mode},
        )
        if payload.process_now and get_settings().job_process_inline:
            job = process_job(db, job.id)
        jobs.append(job)
    db.commit()
    return jobs


def process_job_task(job_id: int) -> None:
    db = SessionLocal()
    try:
        process_job(db, job_id)
    finally:
        db.close()


@router.get("/jobs", response_model=list[PublishingJobOut])
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


@router.get("/jobs/{job_id}", response_model=PublishingJobOut)
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


@router.post("/jobs/{job_id}/retry", response_model=PublishingJobOut)
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


@router.post("/jobs/{job_id}/confirm-completion", response_model=PublishingJobOut)
def confirm_manual_completion(
    job_id: int,
    payload: ManualCompletionRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = (
        db.query(PublishingJob)
        .options(selectinload(PublishingJob.listing), selectinload(PublishingJob.logs))
        .filter(PublishingJob.id == job_id)
        .one_or_none()
    )
    if not job or job.listing.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.operation_mode != "assisted":
        raise HTTPException(status_code=409, detail="Only assisted jobs can be manually confirmed")
    if job.status != "needs_user_action":
        raise HTTPException(status_code=409, detail="Job is not waiting for manual completion")

    now = datetime.now(timezone.utc)
    platform_url = str(payload.platform_url)
    mapping = get_or_create_mapping(db, job.listing_id, job.platform)
    mapping.status = "published"
    mapping.platform_url = platform_url
    mapping.platform_listing_id = payload.platform_listing_id
    mapping.last_published_at = now
    mapping.validation_errors = []

    result = dict(job.result or {})
    result["manual_completion"] = {
        "confirmed_by_user_id": user.id,
        "confirmed_at": now.isoformat(),
        "platform_url": platform_url,
        "platform_listing_id": payload.platform_listing_id,
        "note": payload.note,
        "truth_boundary": "User confirmed the external platform submission; the app did not publish automatically.",
    }
    job.status = "published"
    job.error_message = None
    job.finished_at = now
    job.result = result

    db.add(
        PublicationAttempt(
            job_id=job.id,
            platform=job.platform,
            status="published",
            error_message=None,
            payload_snapshot={
                "manual_completion": result["manual_completion"],
                "source_status": "needs_user_action",
            },
        )
    )
    db.add(
        PublishingJobLog(
            job_id=job.id,
            level="info",
            message="Manual platform completion confirmed by user.",
            data=result["manual_completion"],
        )
    )
    add_audit_event(
        db,
        owner_id=user.id,
        actor_id=user.id,
        event_type="manual_completion_confirmed",
        resource_type="publishing_job",
        resource_id=job.id,
        message="Manual platform completion confirmed by user.",
        details={
            "listing_id": job.listing_id,
            "platform": job.platform,
            "platform_url": platform_url,
            "platform_listing_id": payload.platform_listing_id,
        },
    )
    db.commit()
    db.refresh(job)
    return job


@router.get("/accounts", response_model=list[PlatformAccountOut])
def list_accounts(
    response: Response,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    platform: str | None = Query(default=None, max_length=80),
    status: str | None = Query(default=None, max_length=40),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(PlatformAccount).filter(PlatformAccount.owner_id == user.id)
    if platform:
        query = query.filter(PlatformAccount.platform == platform)
    if status:
        query = query.filter(PlatformAccount.status == status)
    query = query.order_by(PlatformAccount.created_at.desc())
    return apply_pagination(query, response, limit, offset).all()


@router.post("/accounts", response_model=PlatformAccountOut)
def create_account(
    payload: PlatformAccountCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_adapter(payload.platform)
    account = PlatformAccount(owner_id=user.id, **payload.model_dump())
    db.add(account)
    db.flush()
    add_audit_event(
        db,
        owner_id=user.id,
        actor_id=user.id,
        event_type="platform_account_created",
        resource_type="platform_account",
        resource_id=account.id,
        message="Platform account metadata created.",
        details={"platform": account.platform, "mode": account.mode, "status": account.status},
    )
    db.commit()
    db.refresh(account)
    return account


@router.delete("/accounts/{account_id}", status_code=204)
def delete_account(account_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    account = (
        db.query(PlatformAccount)
        .filter(PlatformAccount.id == account_id, PlatformAccount.owner_id == user.id)
        .one_or_none()
    )
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    add_audit_event(
        db,
        owner_id=user.id,
        actor_id=user.id,
        event_type="platform_account_deleted",
        resource_type="platform_account",
        resource_id=account.id,
        message="Platform account metadata deleted.",
        details={"platform": account.platform, "display_name": account.display_name},
    )
    db.delete(account)
    db.commit()


@router.get("/templates", response_model=list[TemplateOut])
def list_templates(
    response: Response,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    platform: str | None = Query(default=None, max_length=80),
    search: str | None = Query(default=None, max_length=120),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(ListingTemplate).filter(ListingTemplate.owner_id == user.id)
    if platform:
        query = query.filter(ListingTemplate.platform == platform)
    if search:
        query = query.filter(ListingTemplate.name.ilike(f"%{search.strip()}%"))
    query = query.order_by(ListingTemplate.name)
    return apply_pagination(query, response, limit, offset).all()


@router.post("/templates", response_model=TemplateOut)
def create_template(
    payload: TemplateCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    template = ListingTemplate(owner_id=user.id, **payload.model_dump())
    db.add(template)
    db.flush()
    add_audit_event(
        db,
        owner_id=user.id,
        actor_id=user.id,
        event_type="template_created",
        resource_type="template",
        resource_id=template.id,
        message="Listing template created.",
        details={"platform": template.platform},
    )
    db.commit()
    db.refresh(template)
    return template


@router.get("/category-mappings", response_model=list[CategoryMappingOut])
def list_category_mappings(
    response: Response,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    platform: str | None = Query(default=None, max_length=80),
    source_category: str | None = Query(default=None, max_length=120),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(CategoryMapping).filter(CategoryMapping.owner_id == user.id)
    if platform:
        query = query.filter(CategoryMapping.platform == platform)
    if source_category:
        query = query.filter(CategoryMapping.source_category.ilike(f"%{source_category.strip()}%"))
    query = query.order_by(CategoryMapping.source_category.asc(), CategoryMapping.platform.asc())
    return apply_pagination(query, response, limit, offset).all()


@router.post("/category-mappings", response_model=CategoryMappingOut)
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
        add_audit_event(
            db,
            owner_id=user.id,
            actor_id=user.id,
            event_type="category_mapping_updated",
            resource_type="category_mapping",
            resource_id=existing.id,
            message="Category mapping updated.",
            details={"source_category": existing.source_category, "platform": existing.platform},
        )
        db.commit()
        db.refresh(existing)
        return existing
    category_mapping = CategoryMapping(owner_id=user.id, **payload.model_dump())
    db.add(category_mapping)
    db.flush()
    add_audit_event(
        db,
        owner_id=user.id,
        actor_id=user.id,
        event_type="category_mapping_created",
        resource_type="category_mapping",
        resource_id=category_mapping.id,
        message="Category mapping created.",
        details={"source_category": category_mapping.source_category, "platform": category_mapping.platform},
    )
    db.commit()
    db.refresh(category_mapping)
    return category_mapping


@router.patch("/category-mappings/{mapping_id}", response_model=CategoryMappingOut)
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
    add_audit_event(
        db,
        owner_id=user.id,
        actor_id=user.id,
        event_type="category_mapping_updated",
        resource_type="category_mapping",
        resource_id=category_mapping.id,
        message="Category mapping updated.",
        details={"fields": sorted(data.keys())},
    )
    db.commit()
    db.refresh(category_mapping)
    return category_mapping


@router.delete("/category-mappings/{mapping_id}", status_code=204)
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
    add_audit_event(
        db,
        owner_id=user.id,
        actor_id=user.id,
        event_type="category_mapping_deleted",
        resource_type="category_mapping",
        resource_id=category_mapping.id,
        message="Category mapping deleted.",
        details={"source_category": category_mapping.source_category, "platform": category_mapping.platform},
    )
    db.delete(category_mapping)
    db.commit()


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


@router.get("/export", response_model=DataExportBundle)
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
    payload = {
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
            {"name": template.name, "platform": template.platform, "body": template.body}
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
    add_audit_event(
        db,
        owner_id=user.id,
        actor_id=user.id,
        event_type="data_exported",
        resource_type="user",
        resource_id=user.id,
        message="User exported portable business data.",
        details={
            "listings": len(payload["listings"]),
            "platform_accounts": len(payload["platform_accounts"]),
            "templates": len(payload["templates"]),
            "category_mappings": len(payload["category_mappings"]),
            "includes_secrets": False,
            "includes_image_binaries": False,
        },
    )
    db.commit()
    return payload


@router.post("/import", response_model=DataImportResult)
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
                ListingTemplate.platform == template_payload.platform,
            )
            .one_or_none()
        )
        if template:
            template.body = template_payload.body
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

    add_audit_event(
        db,
        owner_id=user.id,
        actor_id=user.id,
        event_type="data_imported",
        resource_type="user",
        resource_id=user.id,
        message="User imported portable business data.",
        details=result.model_dump(),
    )
    db.commit()
    return result
