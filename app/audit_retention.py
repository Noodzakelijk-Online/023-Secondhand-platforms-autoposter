from app.config import get_settings, validate_startup_safety
from app.database import SessionLocal
from app.services.audit import purge_expired_audit_events


def main() -> None:
    settings = get_settings()
    validate_startup_safety(settings)
    db = SessionLocal()
    try:
        deleted = purge_expired_audit_events(db, settings.audit_retention_days)
    finally:
        db.close()
    print(f"Purged {deleted} expired audit event(s).")


if __name__ == "__main__":
    main()
