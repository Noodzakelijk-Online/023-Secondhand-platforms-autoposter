import logging
import time

from app.config import get_settings
from app.database import SessionLocal, init_db
from app.observability import configure_logging
from app.services.jobs import process_due_jobs

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
    configure_logging(settings.log_level, settings.log_format)
    if settings.auto_create_tables:
        init_db()
    logger.info("Worker started")
    while True:
        processed = run_once()
        if processed:
            logger.info("Processed %s queued job(s)", processed)
        time.sleep(settings.job_worker_poll_seconds)


if __name__ == "__main__":
    run_forever()
