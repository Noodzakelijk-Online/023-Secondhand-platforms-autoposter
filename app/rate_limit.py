from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException

from app.config import get_settings


@dataclass
class LoginBucket:
    attempts: int
    window_started_at: datetime


login_buckets: dict[str, LoginBucket] = {}


def check_login_rate_limit(identifier: str) -> None:
    settings = get_settings()
    now = datetime.now(UTC)
    window = timedelta(seconds=settings.login_rate_limit_window_seconds)
    bucket = login_buckets.get(identifier)
    if not bucket or now - bucket.window_started_at > window:
        login_buckets[identifier] = LoginBucket(attempts=0, window_started_at=now)
        return
    if bucket.attempts >= settings.login_rate_limit_attempts:
        raise HTTPException(status_code=429, detail="Too many login attempts. Please try again later.")


def record_failed_login(identifier: str) -> None:
    now = datetime.now(UTC)
    bucket = login_buckets.get(identifier)
    if not bucket:
        login_buckets[identifier] = LoginBucket(attempts=1, window_started_at=now)
        return
    bucket.attempts += 1


def record_successful_login(identifier: str) -> None:
    login_buckets.pop(identifier, None)
