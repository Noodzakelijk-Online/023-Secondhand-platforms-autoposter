from datetime import datetime, timezone
from pathlib import Path
import shutil
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, File, Header, HTTPException, Query, Response, UploadFile
from sqlalchemy.orm import Session, selectinload

from app.adapters import get_adapter, list_platforms
from app.config import get_settings
from app.database import SessionLocal, get_db
from app.models import (
    Listing,
    ListingDraft,
    ListingImage,
    ListingTemplate,
    PlatformAccount,
    PlatformListingMapping,
    PublishingJob,
    User,
    UserSession,
)
from app.query import apply_pagination, apply_sort, listing_search_filter
from app.schemas import (
    AuthLogin,
    AuthRegister,
    AuthToken,
    ImageOrderUpdate,
    ListingCreate,
    ListingOut,
    ListingUpdate,
    PlatformAccountCreate,
    PlatformAccountOut,
    PlatformMappingOut,
    PlatformOverrideUpdate,
    PublishRequest,
    PublishingJobOut,
    TemplateCreate,
    TemplateOut,
    UserOut,
    ValidationResult,
)
from app.security import create_session, hash_password, hash_token, verify_password
from app.services.jobs import enqueue_publish_job, get_or_create_mapping, process_job, retry_job


router = APIRouter(prefix="/api")


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    settings = get_settings()
    if settings.dev_auto_login:
        user = db.query(User).filter(User.email == "demo@example.com").one_or_none()
        if not user:
            user = User(
                email="demo@example.com",
                name="Demo User",
                password_hash=hash_password("development-only"),
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

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
    expires_at = session.expires_at
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    if not session.user.is_active:
        raise HTTPException(status_code=403, detail="User is disabled")
    return session.user


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "time": datetime.now(timezone.utc).isoformat()}


@router.get("/diagnostics")
def diagnostics(db: Session = Depends(get_db)) -> dict:
    return {
        "status": "ok",
        "listings": db.query(Listing).count(),
        "jobs": db.query(PublishingJob).count(),
        "platforms": [platform["key"] for platform in list_platforms()],
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
def login(payload: AuthLogin, db: Session = Depends(get_db)) -> AuthToken:
    user = db.query(User).filter(User.email == payload.email.lower()).one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_session(db, user)
    return AuthToken(token=token, user=UserOut.model_validate(user))


@router.get("/auth/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user


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
    db.add(ListingDraft(listing_id=listing.id, payload=data, source="manual_save"))
    db.commit()
    return _load_listing(db, user.id, listing_id)


@router.delete("/listings/{listing_id}", status_code=204)
def delete_listing(
    listing_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    listing = _load_listing(db, user.id, listing_id)
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
                position=image.position,
            )
        )
    db.commit()
    return _load_listing(db, user.id, clone.id)


@router.post("/listings/{listing_id}/images", response_model=ListingOut)
def upload_image(
    listing_id: int,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    listing = _load_listing(db, user.id, listing_id)
    settings = get_settings()
    upload_dir = settings.upload_path / str(listing.id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(file.filename or "upload").suffix
    stored_name = f"{uuid.uuid4().hex}{suffix}"
    target = upload_dir / stored_name
    with target.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    position = len(listing.images)
    db.add(
        ListingImage(
            listing_id=listing.id,
            filename=file.filename or stored_name,
            storage_path=str(target),
            content_type=file.content_type or "application/octet-stream",
            position=position,
        )
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
        outcome = adapter.validate_listing(listing, mapping.overrides)
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


@router.post("/listings/{listing_id}/publish", response_model=list[PublishingJobOut])
def publish_listing(
    listing_id: int,
    payload: PublishRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    listing = _load_listing(db, user.id, listing_id)
    jobs = []
    for platform_key in payload.platforms:
        get_adapter(platform_key)
        account_id = payload.account_ids.get(platform_key)
        job = enqueue_publish_job(db, listing, platform_key, account_id)
        if payload.process_now and get_settings().job_process_inline:
            job = process_job(db, job.id)
        elif payload.process_now:
            background_tasks.add_task(process_job_task, job.id)
        jobs.append(job)
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
    job = db.query(PublishingJob).options(selectinload(PublishingJob.listing)).filter(PublishingJob.id == job_id).one_or_none()
    if not job or job.listing.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Job not found")
    return retry_job(db, job)


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
    db.commit()
    db.refresh(template)
    return template
