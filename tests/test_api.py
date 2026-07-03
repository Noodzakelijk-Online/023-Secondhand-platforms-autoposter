import os

os.environ["DATABASE_URL"] = "sqlite:///./data/test_autoposter.db"
os.environ["PLATFORM_RATE_LIMIT_SECONDS"] = "0"

from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app

client = TestClient(app)

PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\rIHDR"
    b"\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
)


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


def test_platform_metadata_contract():
    response = client.get("/api/platforms")

    assert response.status_code == 200
    platforms = response.json()
    assert {platform["key"] for platform in platforms} >= {"marktplaats", "koopplein", "nextdoor", "ebay"}
    for platform in platforms:
        assert platform["name"]
        assert platform["automation_mode"] == "assisted"
        assert isinstance(platform["required_fields"], list)
        assert isinstance(platform["supported_categories"], list)
        assert isinstance(platform["compliance_notes"], list)
        assert platform["official_api_status"]
        assert isinstance(platform["credential_requirements"], list)
        assert isinstance(platform["automation_blockers"], list)

    ebay = next(platform for platform in platforms if platform["key"] == "ebay")
    assert ebay["official_api_status"] == "eligible_when_configured"
    assert any(item["status"] == "blocked" for item in ebay["credential_requirements"])


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
        files={"file": ("lamp.png", PNG_BYTES, "image/png")},
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

    detail_response = client.get(f"/api/listings/{listing_id}", headers=headers)
    assert detail_response.status_code == 200, detail_response.text
    assert detail_response.json()["title"] == "Vintage desk lamp"


def test_manual_completion_records_final_url_and_history():
    headers = auth_headers()
    listing_response = client.post(
        "/api/listings",
        headers=headers,
        json={
            "title": "Oak side table",
            "description": "Solid oak table with light wear.",
            "price_cents": 4500,
            "condition": "good",
            "category": "Furniture",
            "location": "Arnhem",
            "delivery_options": {"pickup": True},
        },
    )
    listing_id = listing_response.json()["id"]
    client.post(
        f"/api/listings/{listing_id}/images",
        headers=headers,
        files={"file": ("table.png", PNG_BYTES, "image/png")},
    )
    publish_response = client.post(
        f"/api/listings/{listing_id}/publish",
        headers=headers,
        json={"platforms": ["marktplaats"], "process_now": True},
    )
    job = publish_response.json()[0]
    assert job["status"] == "needs_user_action"

    completion_response = client.post(
        f"/api/jobs/{job['id']}/confirm-completion",
        headers=headers,
        json={
            "platform_url": "https://www.marktplaats.nl/v/huis-en-inrichting/tafels/m1234567890-oak-side-table",
            "platform_listing_id": "m1234567890",
            "note": "User completed CAPTCHA and final submit on Marktplaats.",
        },
    )

    assert completion_response.status_code == 200, completion_response.text
    completed_job = completion_response.json()
    assert completed_job["status"] == "published"
    assert completed_job["result"]["manual_completion"]["platform_listing_id"] == "m1234567890"
    assert "did not publish automatically" in completed_job["result"]["manual_completion"]["truth_boundary"]
    assert completed_job["logs"][-1]["message"] == "Manual platform completion confirmed by user."

    listing = client.get(f"/api/listings/{listing_id}", headers=headers).json()
    mapping = listing["platform_mappings"][0]
    assert mapping["status"] == "published"
    assert mapping["platform_listing_id"] == "m1234567890"
    assert mapping["platform_url"].startswith("https://www.marktplaats.nl/")
    assert mapping["last_published_at"] is not None


def test_manual_completion_requires_waiting_assisted_job():
    headers = auth_headers()
    listing_response = client.post("/api/listings", headers=headers, json={"title": "Incomplete"})
    listing_id = listing_response.json()["id"]
    publish_response = client.post(
        f"/api/listings/{listing_id}/publish",
        headers=headers,
        json={"platforms": ["marktplaats"], "process_now": False},
    )
    job = publish_response.json()[0]

    completion_response = client.post(
        f"/api/jobs/{job['id']}/confirm-completion",
        headers=headers,
        json={"platform_url": "https://www.marktplaats.nl/v/example"},
    )

    assert completion_response.status_code == 409
    assert completion_response.json()["error"]["code"] == "CONFLICT"


def test_manual_completion_is_owner_scoped():
    owner_headers = auth_headers()
    listing_response = client.post(
        "/api/listings",
        headers=owner_headers,
        json={
            "title": "Vintage mirror",
            "description": "Brass-framed mirror.",
            "price_cents": 3000,
            "condition": "used",
            "category": "Home",
            "location": "Arnhem",
            "delivery_options": {"pickup": True},
        },
    )
    listing_id = listing_response.json()["id"]
    client.post(
        f"/api/listings/{listing_id}/images",
        headers=owner_headers,
        files={"file": ("mirror.png", PNG_BYTES, "image/png")},
    )
    publish_response = client.post(
        f"/api/listings/{listing_id}/publish",
        headers=owner_headers,
        json={"platforms": ["marktplaats"], "process_now": True},
    )
    job_id = publish_response.json()[0]["id"]
    other_auth = client.post(
        "/api/auth/register",
        json={"email": "other@example.com", "password": "correct-password", "name": "Other"},
    ).json()
    other_headers = {"Authorization": f"Bearer {other_auth['token']}"}

    completion_response = client.post(
        f"/api/jobs/{job_id}/confirm-completion",
        headers=other_headers,
        json={"platform_url": "https://www.marktplaats.nl/v/example"},
    )

    assert completion_response.status_code == 404


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

    account = client.get("/api/accounts", headers=headers).json()[0]
    delete_response = client.delete(f"/api/accounts/{account['id']}", headers=headers)
    assert delete_response.status_code == 204
    assert client.get("/api/accounts", headers=headers).json() == []


def test_listing_detail_and_delete_are_owner_scoped():
    headers = auth_headers()
    listing_response = client.post(
        "/api/listings",
        headers=headers,
        json={"title": "Delete me", "status": "draft"},
    )
    assert listing_response.status_code == 200, listing_response.text
    listing_id = listing_response.json()["id"]

    detail_response = client.get(f"/api/listings/{listing_id}", headers=headers)
    assert detail_response.status_code == 200, detail_response.text
    assert detail_response.json()["id"] == listing_id

    delete_response = client.delete(f"/api/listings/{listing_id}", headers=headers)
    assert delete_response.status_code == 204
    assert client.get(f"/api/listings/{listing_id}", headers=headers).status_code == 404
