import uuid

from app.database import Base, engine
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

    monkeypatch.delenv("JOB_PROCESS_INLINE")
    get_settings.cache_clear()


def test_worker_ignores_empty_queue():
    assert run_once() == 0
