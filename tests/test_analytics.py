import uuid

from app.database import Base, engine
from tests.test_api import PNG_BYTES, client


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def auth_headers(prefix: str):
    response = client.post(
        "/api/auth/register",
        json={
            "email": f"{prefix}-{uuid.uuid4().hex}@example.com",
            "password": "correct-password",
            "name": f"{prefix} User",
        },
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['token']}"}


def test_analytics_are_local_owner_scoped_aggregates():
    owner_headers = auth_headers("analytics-owner")
    other_headers = auth_headers("analytics-other")
    listing_response = client.post(
        "/api/listings",
        headers=owner_headers,
        json={
            "title": "Vintage brass desk lamp",
            "description": "Working used lamp with light wear as pictured and no known issues.",
            "price_cents": 2500,
            "condition": "used",
            "category": "Home and furniture",
            "location": "Arnhem",
            "pickup_allowed": True,
            "status": "ready",
        },
    )
    listing_id = listing_response.json()["id"]
    image_response = client.post(
        f"/api/listings/{listing_id}/images",
        headers=owner_headers,
        files={"file": ("lamp.png", PNG_BYTES, "image/png")},
    )
    assert image_response.status_code == 200, image_response.text
    mapping_response = client.post(
        f"/api/listings/{listing_id}/platforms",
        headers=owner_headers,
        json={"platform": "marktplaats", "selected": True, "overrides": {}},
    )
    assert mapping_response.status_code == 200, mapping_response.text
    publish_response = client.post(
        f"/api/listings/{listing_id}/publish",
        headers=owner_headers,
        json={"platforms": ["marktplaats"], "process_now": True},
    )
    assert publish_response.status_code == 200, publish_response.text
    client.post("/api/listings", headers=other_headers, json={"title": "Other user listing"})

    response = client.get("/api/analytics", headers=owner_headers)

    assert response.status_code == 200, response.text
    analytics = response.json()
    assert analytics["source"] == "local_database"
    assert analytics["external_tracking"] is False
    assert analytics["summary"]["listings_total"] == 1
    assert analytics["summary"]["ready_listings"] == 1
    assert analytics["summary"]["inventory_value_cents"] == 2500
    assert analytics["selected_platforms"] == {"marktplaats": 1}
    assert analytics["summary"]["jobs_total"] == 1
    assert sum(analytics["job_statuses"].values()) == 1
    assert analytics["job_platforms"] == {"marktplaats": 1}
    assert analytics["quality"]["listings_missing_images"] == 0
    assert analytics["summary"]["average_quality_score"] > 0

    other_response = client.get("/api/analytics", headers=other_headers)
    assert other_response.status_code == 200, other_response.text
    assert other_response.json()["summary"]["listings_total"] == 1
    assert other_response.json()["summary"]["inventory_value_cents"] == 0


def test_analytics_requires_authentication():
    response = client.get("/api/analytics")

    assert response.status_code == 401
