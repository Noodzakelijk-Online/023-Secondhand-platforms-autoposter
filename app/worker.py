import logging
import time
import uuid

from app.config import get_settings, validate_startup_safety
from app.database import SessionLocal, init_db
from app.observability import configure_logging
from app.services.jobs import process_due_jobs
from app.services.worker_health import record_heartbeat

logger = logging.getLogger("autoposter.worker")


def run_once() -> int:
    settings = get_settings()
    db = SessionLocal()
    try:
        return process_due_jobs(db, settings.job_worker_batch_size)
    finally:
        db.close()


def run_forever() -> None:
    settings = get_settings()
    validate_startup_safety(settings)
    configure_logging(settings.log_level, settings.log_format)
    if settings.auto_create_tables:
        init_db()
    worker_id = f"worker-{uuid.uuid4().hex}"
    logger.info("Worker started: %s", worker_id)
    while True:
        processed = run_once()
        db = SessionLocal()
        try:
            record_heartbeat(db, worker_id, processed)
        finally:
            db.close()
        if processed:
            logger.info("Processed %s queued job(s)", processed)
        time.sleep(settings.job_worker_poll_seconds)


if __name__ == "__main__":
    run_forever()
