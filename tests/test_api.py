import os

os.environ["DATABASE_URL"] = "sqlite:///./data/test_autoposter.db"
os.environ["PLATFORM_RATE_LIMIT_SECONDS"] = "0"

from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app


client = TestClient(app)


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def auth_headers():
    response = client.post(
        "/api/auth/register",
        json={"email": "owner@example.com", "password": "correct-password", "name": "Owner"},
    )
    assert response.status_code == 200, response.text
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_validate_and_publish_listing_flow():
    headers = auth_headers()
    listing_response = client.post(
        "/api/listings",
        headers=headers,
        json={
            "title": "Vintage desk lamp",
            "description": "Adjustable metal desk lamp in good working condition.",
            "price_cents": 2500,
            "condition": "used",
            "category": "Home and furniture",
            "location": "Arnhem",
            "delivery_options": {"pickup": True, "shipping": False},
            "tags": ["lamp", "desk"],
        },
    )
    assert listing_response.status_code == 200, listing_response.text
    listing_id = listing_response.json()["id"]

    image_response = client.post(
        f"/api/listings/{listing_id}/images",
        headers=headers,
        files={"file": ("lamp.jpg", b"fake image bytes", "image/jpeg")},
    )
    assert image_response.status_code == 200, image_response.text
    assert len(image_response.json()["images"]) == 1

    validation_response = client.get(f"/api/listings/{listing_id}/validate?platform=marktplaats", headers=headers)
    assert validation_response.status_code == 200, validation_response.text
    validation = validation_response.json()[0]
    assert validation["ready"] is True
    assert validation["missing_fields"] == []

    publish_response = client.post(
        f"/api/listings/{listing_id}/publish",
        headers=headers,
        json={"platforms": ["marktplaats"], "process_now": True},
    )
    assert publish_response.status_code == 200, publish_response.text
    job = publish_response.json()[0]
    assert job["status"] == "needs_user_action"
    assert job["result"]["automation_mode"] == "assisted"
    assert job["logs"]


def test_validation_reports_missing_fields():
    headers = auth_headers()
    listing_response = client.post("/api/listings", headers=headers, json={"title": "Incomplete"})
    listing_id = listing_response.json()["id"]

    validation_response = client.get(f"/api/listings/{listing_id}/validate?platform=nextdoor", headers=headers)

    assert validation_response.status_code == 200
    validation = validation_response.json()[0]
    assert validation["ready"] is False
    assert "description" in validation["missing_fields"]
    assert "images" in validation["missing_fields"]


def test_accounts_and_templates():
    headers = auth_headers()
    account_response = client.post(
        "/api/accounts",
        headers=headers,
        json={"platform": "ebay", "display_name": "Personal eBay", "status": "needs_setup"},
    )
    assert account_response.status_code == 200, account_response.text

    template_response = client.post(
        "/api/templates",
        headers=headers,
        json={"name": "Default", "platform": None, "body": "Available for pickup in Arnhem."},
    )
    assert template_response.status_code == 200, template_response.text

    assert client.get("/api/accounts", headers=headers).json()[0]["platform"] == "ebay"
    assert client.get("/api/templates", headers=headers).json()[0]["name"] == "Default"
