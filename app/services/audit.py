import hashlib
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.models import AuditEvent, User


def email_hash(email: str) -> str:
    return hashlib.sha256(email.strip().lower().encode()).hexdigest()


def record_audit_event(db: Session, user: User, action: str, event_data: dict[str, Any] | None = None) -> AuditEvent:
    event = AuditEvent(
        user_id=user.id,
        user_email_hash=email_hash(user.email),
        action=action,
        event_data=event_data or {},
    )
    db.add(event)
    db.flush()
    return event


def purge_expired_audit_events(db: Session, retention_days: int) -> int:
    if retention_days <= 0:
        return 0
    cutoff = datetime.now(UTC) - timedelta(days=retention_days)
    deleted = db.query(AuditEvent).filter(AuditEvent.created_at < cutoff).delete(synchronize_session=False)
    db.commit()
    return deleted
