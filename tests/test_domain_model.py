import uuid

from app.database import Base, SessionLocal, engine
from app.models import (
    Listing,
    ListingDraft,
    ListingImage,
    PlatformListingMapping,
    PublicationAttempt,
    PublishingJob,
    PublishingJobLog,
)
from tests.test_api import PNG_BYTES, client


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def auth_headers() -> dict[str, str]:
    response = client.post(
        "/api/auth/register",
        json={
            "email": f"domain-{uuid.uuid4().hex}@example.com",
            "password": "correct-password",
            "name": "Domain User",
        },
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['token']}"}


def test_listing_aggregate_delete_cascades_owned_children():
    headers = auth_headers()
    create_response = client.post(
        "/api/listings",
        headers=headers,
        json={
            "title": "Aggregate cabinet",
            "description": "A domain aggregate with children.",
            "price_cents": 12500,
            "condition": "good",
            "category": "Furniture",
            "location": "Rotterdam",
        },
    )
    assert create_response.status_code == 200, create_response.text
    listing_id = create_response.json()["id"]

    image_response = client.post(
        f"/api/listings/{listing_id}/images",
        headers=headers,
        files={"file": ("cabinet.png", PNG_BYTES, "image/png")},
    )
    assert image_response.status_code == 200, image_response.text
    patch_response = client.patch(
        f"/api/listings/{listing_id}",
        headers=headers,
        json={"description": "Updated aggregate description."},
    )
    assert patch_response.status_code == 200, patch_response.text
    publish_response = client.post(
        f"/api/listings/{listing_id}/publish",
        headers=headers,
        json={"platforms": ["marktplaats"], "process_now": True},
    )
    assert publish_response.status_code == 200, publish_response.text
    job_id = publish_response.json()[0]["id"]

    db = SessionLocal()
    try:
        assert db.query(Listing).filter(Listing.id == listing_id).count() == 1
        assert db.query(ListingImage).filter(ListingImage.listing_id == listing_id).count() == 1
        assert db.query(ListingDraft).filter(ListingDraft.listing_id == listing_id).count() == 1
        assert db.query(PlatformListingMapping).filter(PlatformListingMapping.listing_id == listing_id).count() == 1
        assert db.query(PublishingJob).filter(PublishingJob.id == job_id).count() == 1
        assert db.query(PublishingJobLog).filter(PublishingJobLog.job_id == job_id).count() >= 1
        assert db.query(PublicationAttempt).filter(PublicationAttempt.job_id == job_id).count() == 1
    finally:
        db.close()

    delete_response = client.delete(f"/api/listings/{listing_id}", headers=headers)
    assert delete_response.status_code == 204, delete_response.text

    db = SessionLocal()
    try:
        assert db.query(Listing).filter(Listing.id == listing_id).count() == 0
        assert db.query(ListingImage).filter(ListingImage.listing_id == listing_id).count() == 0
        assert db.query(ListingDraft).filter(ListingDraft.listing_id == listing_id).count() == 0
        assert db.query(PlatformListingMapping).filter(PlatformListingMapping.listing_id == listing_id).count() == 0
        assert db.query(PublishingJob).filter(PublishingJob.id == job_id).count() == 0
        assert db.query(PublishingJobLog).filter(PublishingJobLog.job_id == job_id).count() == 0
        assert db.query(PublicationAttempt).filter(PublicationAttempt.job_id == job_id).count() == 0
    finally:
        db.close()
