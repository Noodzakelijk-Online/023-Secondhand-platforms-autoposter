import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import LoginThrottle


@dataclass
class LoginBucket:
    attempts: int
    window_started_at: datetime


@dataclass
class ApiBucket:
    requests: int
    window_started_at: datetime


login_buckets: dict[str, LoginBucket] = {}
api_buckets: dict[str, ApiBucket] = {}


def _identifier_hash(identifier: str) -> str:
    return hashlib.sha256(identifier.encode("utf-8")).hexdigest()


def _active_bucket(db: Session, identifier: str) -> LoginThrottle | None:
    settings = get_settings()
    now = datetime.now(UTC)
    window = timedelta(seconds=settings.login_rate_limit_window_seconds)
    bucket = (
        db.query(LoginThrottle)
        .filter(LoginThrottle.identifier_hash == _identifier_hash(identifier))
        .with_for_update()
        .one_or_none()
    )
    if not bucket:
        return None
    started_at = _aware_utc(bucket.window_started_at)
    if now - started_at > window:
        db.delete(bucket)
        db.commit()
        return None
    return bucket


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def check_login_rate_limit(db: Session, identifier: str) -> None:
    settings = get_settings()
    bucket = _active_bucket(db, identifier)
    if not bucket:
        return
    if bucket.attempts >= settings.login_rate_limit_attempts:
        now = datetime.now(UTC)
        started_at = _aware_utc(bucket.window_started_at)
        elapsed_seconds = int((now - started_at).total_seconds())
        retry_after = max(1, settings.login_rate_limit_window_seconds - elapsed_seconds)
        raise HTTPException(
            status_code=429,
            detail="Too many login attempts. Please try again later.",
            headers={"Retry-After": str(retry_after)},
        )


def record_failed_login(db: Session, identifier: str) -> None:
    now = datetime.now(UTC)
    bucket = _active_bucket(db, identifier)
    if not bucket:
        db.add(
            LoginThrottle(
                identifier_hash=_identifier_hash(identifier),
                attempts=1,
                window_started_at=now,
                last_failed_at=now,
            )
        )
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            record_failed_login(db, identifier)
        return
    bucket.attempts += 1
    bucket.last_failed_at = now
    db.commit()


def record_successful_login(db: Session, identifier: str) -> None:
    bucket = _active_bucket(db, identifier)
    if bucket:
        db.delete(bucket)
        db.commit()


def check_api_rate_limit(identifier: str, limit: int, window_seconds: int) -> int | None:
    now = datetime.now(UTC)
    window = timedelta(seconds=window_seconds)
    bucket_key = _identifier_hash(identifier)
    bucket = api_buckets.get(bucket_key)
    if not bucket or now - bucket.window_started_at > window:
        api_buckets[bucket_key] = ApiBucket(requests=1, window_started_at=now)
        return None
    if bucket.requests >= limit:
        retry_after = window_seconds - int((now - bucket.window_started_at).total_seconds())
        return max(1, retry_after)
    bucket.requests += 1
    return None
