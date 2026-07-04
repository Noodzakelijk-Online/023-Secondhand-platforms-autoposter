import hashlib
from datetime import UTC, datetime, timedelta

from sqlalchemy import desc
from sqlalchemy.orm import Session, selectinload

from app.adapters import get_adapter
from app.config import get_settings
from app.models import (
    CategoryMapping,
    Listing,
    PlatformAccount,
    PlatformListingMapping,
    PublicationAttempt,
    PublishingJob,
    PublishingJobLog,
)
from app.services.job_state import (
    ACTIVE_IDEMPOTENCY_STATUSES,
    FAILED,
    PUBLISHED,
    QUEUED,
    RUNNING,
    is_terminal_status,
    transition_job,
)


def idempotency_key(
    *,
    user_id: int,
    listing_id: int,
    listing_revision: int,
    platform: str,
    action_type: str,
    account_id: int | None,
    operation_mode: str,
) -> str:
    raw = (
        f"user={user_id}:listing={listing_id}:revision={listing_revision}:platform={platform}:"
        f"action={action_type}:account={account_id or 'none'}:mode={operation_mode}"
    ).encode()
    return hashlib.sha256(raw).hexdigest()


def add_log(db: Session, job: PublishingJob, level: str, message: str, data: dict | None = None) -> None:
    db.add(PublishingJobLog(job_id=job.id, level=level, message=message, data=data or {}))
    db.flush()


def get_or_create_mapping(db: Session, listing_id: int, platform: str) -> PlatformListingMapping:
    mapping = (
        db.query(PlatformListingMapping)
        .filter(PlatformListingMapping.listing_id == listing_id, PlatformListingMapping.platform == platform)
        .one_or_none()
    )
    if mapping:
        return mapping
    mapping = PlatformListingMapping(listing_id=listing_id, platform=platform, status="draft")
    db.add(mapping)
    db.flush()
    return mapping


def enqueue_publish_job(
    db: Session, listing: Listing, platform: str, account_id: int | None = None
) -> PublishingJob:
    adapter = get_adapter(platform)
    action_type = "publish"
    operation_mode = adapter.automation_mode
    key = idempotency_key(
        user_id=listing.owner_id,
        listing_id=listing.id,
        listing_revision=listing.revision,
        platform=platform,
        action_type=action_type,
        account_id=account_id,
        operation_mode=operation_mode,
    )
    existing = (
        db.query(PublishingJob)
        .filter(
            PublishingJob.idempotency_key == key,
            PublishingJob.status.in_(ACTIVE_IDEMPOTENCY_STATUSES),
        )
        .one_or_none()
    )
    if existing:
        return existing

    job = PublishingJob(
        listing_id=listing.id,
        platform=platform,
        account_id=account_id,
        status=QUEUED,
        idempotency_key=key,
        listing_revision=listing.revision,
        action_type=action_type,
        operation_mode=operation_mode,
    )
    db.add(job)
    db.flush()
    add_log(db, job, "info", "Publishing job queued.")
    db.commit()
    db.refresh(job)
    return job


def process_job(db: Session, job_id: int) -> PublishingJob:
    job = (
        db.query(PublishingJob)
        .options(selectinload(PublishingJob.listing).selectinload(Listing.images), selectinload(PublishingJob.logs))
        .filter(PublishingJob.id == job_id)
        .one()
    )
    if is_terminal_status(job.status) and job.status != FAILED:
        return job

    settings = get_settings()
    cooldown_cutoff = datetime.now(UTC) - timedelta(seconds=settings.platform_rate_limit_seconds)
    recent_job = (
        db.query(PublishingJob)
        .filter(
            PublishingJob.platform == job.platform,
            PublishingJob.id != job.id,
            PublishingJob.started_at.is_not(None),
        )
        .order_by(desc(PublishingJob.started_at))
        .first()
    )
    recent_started_at = recent_job.started_at if recent_job else None
    if recent_started_at and recent_started_at.tzinfo is None:
        recent_started_at = recent_started_at.replace(tzinfo=UTC)
    if recent_job and recent_started_at and recent_started_at > cooldown_cutoff:
        transition_job(job, QUEUED)
        job.next_retry_at = datetime.now(UTC) + timedelta(seconds=settings.platform_rate_limit_seconds)
        add_log(db, job, "info", "Rate limit cooldown applied.", {"next_retry_at": job.next_retry_at.isoformat()})
        db.commit()
        db.refresh(job)
        return job

    if job.status != RUNNING:
        transition_job(job, RUNNING)
    job.started_at = datetime.now(UTC)
    job.attempts += 1
    add_log(db, job, "info", "Publishing job started.")
    db.commit()

    listing = job.listing
    adapter = get_adapter(job.platform)
    mapping = get_or_create_mapping(db, listing.id, job.platform)
    account = db.get(PlatformAccount, job.account_id) if job.account_id else None

    try:
        overrides = effective_platform_overrides(db, listing, job.platform, mapping.overrides)
        outcome = adapter.publish_listing(listing, account=account, overrides=overrides)
        transition_job(job, outcome.status)
        job.error_message = None if outcome.status != FAILED else outcome.message
        job.result = outcome.data
        job.finished_at = datetime.now(UTC)

        mapping.status = outcome.status
        mapping.platform_listing_id = outcome.platform_listing_id
        mapping.platform_url = outcome.platform_url
        mapping.validation_errors = outcome.data.get("missing_fields", [])
        if outcome.status == PUBLISHED:
            mapping.last_published_at = datetime.now(UTC)

        db.add(
            PublicationAttempt(
                job_id=job.id,
                platform=job.platform,
                status=outcome.status,
                error_message=job.error_message,
                payload_snapshot=outcome.data.get("mapped_fields", outcome.data),
            )
        )
        add_log(db, job, "info", outcome.message or f"Job finished with status {outcome.status}.", outcome.data)
    except Exception as exc:  # pragma: no cover - defensive boundary around external adapters
        transition_job(job, FAILED)
        job.error_message = str(exc)
        job.finished_at = datetime.now(UTC)
        db.add(
            PublicationAttempt(
                job_id=job.id,
                platform=job.platform,
                status=FAILED,
                error_message=str(exc),
                payload_snapshot={},
            )
        )
        add_log(db, job, "error", "Publishing job failed.", {"error": str(exc)})

    db.commit()
    db.refresh(job)
    return job


def retry_job(db: Session, job: PublishingJob) -> PublishingJob:
    if job.attempts >= job.max_attempts:
        job.max_attempts += 1
    transition_job(job, QUEUED)
    job.error_message = None
    job.next_retry_at = None
    add_log(db, job, "info", "Publishing job queued for retry.")
    db.commit()
    db.refresh(job)
    return process_job(db, job.id)


def effective_platform_overrides(db: Session, listing: Listing, platform: str, overrides: dict) -> dict:
    effective = dict(overrides or {})
    if "category" in effective and effective["category"]:
        return effective
    category_mapping = (
        db.query(CategoryMapping)
        .filter(
            CategoryMapping.owner_id == listing.owner_id,
            CategoryMapping.source_category == listing.category,
            CategoryMapping.platform == platform,
        )
        .one_or_none()
    )
    if category_mapping:
        effective["category"] = category_mapping.platform_category
    return effective


def get_due_queued_jobs(db: Session, limit: int) -> list[PublishingJob]:
    now = datetime.now(UTC)
    return (
        db.query(PublishingJob)
        .filter(PublishingJob.status == QUEUED)
        .filter(PublishingJob.scheduled_at <= now)
        .filter((PublishingJob.next_retry_at.is_(None)) | (PublishingJob.next_retry_at <= now))
        .order_by(PublishingJob.scheduled_at.asc(), PublishingJob.id.asc())
        .limit(limit)
        .all()
    )


def claim_due_queued_jobs(db: Session, limit: int) -> list[int]:
    jobs = get_due_queued_jobs(db, limit)
    claimed_ids: list[int] = []
    for job in jobs:
        updated = (
            db.query(PublishingJob)
            .filter(PublishingJob.id == job.id, PublishingJob.status == "queued")
            .update({"status": "running"})
        )
        if updated:
            claimed_ids.append(job.id)
    db.commit()
    return claimed_ids


def requeue_stale_running_jobs(db: Session, timeout_seconds: int) -> int:
    if timeout_seconds <= 0:
        return 0

    cutoff = datetime.now(UTC) - timedelta(seconds=timeout_seconds)
    jobs = (
        db.query(PublishingJob)
        .filter(PublishingJob.status == "running")
        .filter(PublishingJob.started_at.is_not(None))
        .filter(PublishingJob.started_at < cutoff)
        .all()
    )
    for job in jobs:
        job.status = "queued"
        job.next_retry_at = None
        add_log(
            db,
            job,
            "warning",
            "Stale running job requeued after worker timeout.",
            {"timeout_seconds": timeout_seconds, "previous_started_at": job.started_at.isoformat()},
        )
    db.commit()
    return len(jobs)


def process_due_jobs(db: Session, limit: int) -> int:
    settings = get_settings()
    requeue_stale_running_jobs(db, settings.job_running_timeout_seconds)
    job_ids = claim_due_queued_jobs(db, limit)
    processed = 0
    for job_id in job_ids:
        process_job(db, job_id)
        processed += 1
    return processed
