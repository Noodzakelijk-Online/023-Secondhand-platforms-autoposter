import uuid
from datetime import datetime, timedelta, timezone

from app.database import Base, engine
from app.database import SessionLocal
from app.models import PublishingJob, PublishingJobLog
from app.services.jobs import claim_due_queued_jobs, requeue_stale_running_jobs
from app.worker import run_once
from tests.test_api import PNG_BYTES, client


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def auth_headers():
    response = client.post(
        "/api/auth/register",
        json={
            "email": f"worker-{uuid.uuid4().hex}@example.com",
            "password": "correct-password",
            "name": "Worker User",
        },
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['token']}"}


def create_ready_listing(headers):
    response = client.post(
        "/api/listings",
        headers=headers,
        json={
            "title": "Worker queue lamp",
            "description": "Ready for assisted posting.",
            "price_cents": 2200,
            "condition": "used",
            "category": "Home and furniture",
            "location": "Arnhem",
            "delivery_options": {"pickup": True},
        },
    )
    assert response.status_code == 200, response.text
    listing_id = response.json()["id"]
    image_response = client.post(
        f"/api/listings/{listing_id}/images",
        headers=headers,
        files={"file": ("lamp.png", PNG_BYTES, "image/png")},
    )
    assert image_response.status_code == 200, image_response.text
    return listing_id


def test_worker_processes_queued_publish_job(monkeypatch):
    monkeypatch.setenv("JOB_PROCESS_INLINE", "false")
    from app.config import get_settings

    get_settings.cache_clear()
    headers = auth_headers()
    listing_id = create_ready_listing(headers)

    publish_response = client.post(
        f"/api/listings/{listing_id}/publish",
        headers=headers,
        json={"platforms": ["marktplaats"], "process_now": True},
    )

    assert publish_response.status_code == 200, publish_response.text
    queued_job = publish_response.json()[0]
    assert queued_job["status"] == "queued"

    processed = run_once()
    assert processed == 1

    jobs_response = client.get("/api/jobs", headers=headers)
    assert jobs_response.status_code == 200, jobs_response.text
    job = jobs_response.json()[0]
    assert job["status"] == "needs_user_action"
    assert job["attempts"] == 1
    assert job["logs"]

    detail_response = client.get(f"/api/jobs/{job['id']}", headers=headers)
    assert detail_response.status_code == 200, detail_response.text
    assert detail_response.json()["id"] == job["id"]
    assert detail_response.json()["listing_id"] == listing_id

    monkeypatch.delenv("JOB_PROCESS_INLINE")
    get_settings.cache_clear()


def test_jobs_support_pagination_filtering_and_sorting(monkeypatch):
    monkeypatch.setenv("JOB_PROCESS_INLINE", "false")
    from app.config import get_settings

    get_settings.cache_clear()
    headers = auth_headers()
    listing_id = create_ready_listing(headers)
    publish_response = client.post(
        f"/api/listings/{listing_id}/publish",
        headers=headers,
        json={"platforms": ["marktplaats", "ebay"], "process_now": True},
    )
    assert publish_response.status_code == 200, publish_response.text

    response = client.get(
        "/api/jobs?platform=ebay&status=queued&limit=1&offset=0&sort=platform",
        headers=headers,
    )

    assert response.status_code == 200, response.text
    assert response.headers["X-Total-Count"] == "1"
    assert response.headers["X-Limit"] == "1"
    assert response.json()[0]["platform"] == "ebay"
    assert response.json()[0]["status"] == "queued"

    page_response = client.get("/api/jobs?limit=1&offset=1&sort=platform", headers=headers)
    assert page_response.status_code == 200, page_response.text
    assert page_response.headers["X-Total-Count"] == "2"
    assert page_response.headers["X-Offset"] == "1"
    assert page_response.json()[0]["platform"] == "marktplaats"

    monkeypatch.delenv("JOB_PROCESS_INLINE")
    get_settings.cache_clear()


def test_worker_ignores_empty_queue():
    assert run_once() == 0


def test_due_jobs_are_claimed_once(monkeypatch):
    monkeypatch.setenv("JOB_PROCESS_INLINE", "false")
    from app.config import get_settings

    get_settings.cache_clear()
    headers = auth_headers()
    listing_id = create_ready_listing(headers)

    publish_response = client.post(
        f"/api/listings/{listing_id}/publish",
        headers=headers,
        json={"platforms": ["marktplaats"], "process_now": True},
    )
    assert publish_response.status_code == 200, publish_response.text

    first_session = SessionLocal()
    second_session = SessionLocal()
    try:
        first_claim = claim_due_queued_jobs(first_session, 10)
        second_claim = claim_due_queued_jobs(second_session, 10)
    finally:
        first_session.close()
        second_session.close()

    assert len(first_claim) == 1
    assert second_claim == []

    monkeypatch.delenv("JOB_PROCESS_INLINE")
    get_settings.cache_clear()


def test_stale_running_jobs_are_requeued(monkeypatch):
    monkeypatch.setenv("JOB_PROCESS_INLINE", "false")
    from app.config import get_settings

    get_settings.cache_clear()
    headers = auth_headers()
    listing_id = create_ready_listing(headers)

    publish_response = client.post(
        f"/api/listings/{listing_id}/publish",
        headers=headers,
        json={"platforms": ["marktplaats"], "process_now": True},
    )
    assert publish_response.status_code == 200, publish_response.text
    job_id = publish_response.json()[0]["id"]

    db = SessionLocal()
    try:
        job = db.get(PublishingJob, job_id)
        job.status = "running"
        job.started_at = datetime.now(timezone.utc) - timedelta(seconds=3600)
        db.commit()

        recovered = requeue_stale_running_jobs(db, timeout_seconds=900)
        db.refresh(job)
        logs = db.query(PublishingJobLog).filter(PublishingJobLog.job_id == job_id).all()
    finally:
        db.close()

    assert recovered == 1
    assert job.status == "queued"
    assert any("Stale running job requeued" in log.message for log in logs)

    monkeypatch.delenv("JOB_PROCESS_INLINE")
    get_settings.cache_clear()


def test_fresh_running_jobs_are_not_requeued(monkeypatch):
    monkeypatch.setenv("JOB_PROCESS_INLINE", "false")
    from app.config import get_settings

    get_settings.cache_clear()
    headers = auth_headers()
    listing_id = create_ready_listing(headers)

    publish_response = client.post(
        f"/api/listings/{listing_id}/publish",
        headers=headers,
        json={"platforms": ["marktplaats"], "process_now": True},
    )
    assert publish_response.status_code == 200, publish_response.text
    job_id = publish_response.json()[0]["id"]

    db = SessionLocal()
    try:
        job = db.get(PublishingJob, job_id)
        job.status = "running"
        job.started_at = datetime.now(timezone.utc)
        db.commit()

        recovered = requeue_stale_running_jobs(db, timeout_seconds=900)
        db.refresh(job)
    finally:
        db.close()

    assert recovered == 0
    assert job.status == "running"

    monkeypatch.delenv("JOB_PROCESS_INLINE")
    get_settings.cache_clear()
