import uuid

from app.database import Base, engine
from tests.test_api import PNG_BYTES, client


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def auth_headers(label: str) -> dict[str, str]:
    response = client.post(
        "/api/auth/register",
        json={
            "email": f"saas-{label}-{uuid.uuid4().hex}@example.com",
            "password": "correct-password",
            "name": label,
        },
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['token']}"}


def create_listing(headers: dict[str, str]) -> int:
    response = client.post(
        "/api/listings",
        headers=headers,
        json={
            "title": "SaaS readiness listing",
            "description": "Ready listing for personal-account usage boundaries.",
            "price_cents": 2200,
            "condition": "good",
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
        files={"file": ("ready.png", PNG_BYTES, "image/png")},
    )
    assert image_response.status_code == 200, image_response.text
    return listing_id


def test_account_readiness_is_personal_scoped_and_billing_free():
    owner_headers = auth_headers("owner")
    other_headers = auth_headers("other")

    listing_id = create_listing(owner_headers)
    publish_response = client.post(
        f"/api/listings/{listing_id}/publish",
        headers=owner_headers,
        json={"platforms": ["marktplaats"], "process_now": True},
    )
    assert publish_response.status_code == 200, publish_response.text
    assert client.post(
        "/api/accounts",
        headers=owner_headers,
        json={"platform": "ebay", "display_name": "Owner eBay", "status": "ready"},
    ).status_code == 200
    assert client.post(
        "/api/templates",
        headers=owner_headers,
        json={"name": "Owner template", "body": "Pickup by appointment."},
    ).status_code == 200
    assert client.post(
        "/api/category-mappings",
        headers=owner_headers,
        json={
            "source_category": "Home and furniture",
            "platform": "marktplaats",
            "platform_category": "Huis en Inrichting",
        },
    ).status_code == 200
    assert client.post("/api/listings", headers=other_headers, json={"title": "Other listing"}).status_code == 200

    owner_readiness = client.get("/api/account/readiness", headers=owner_headers)
    other_readiness = client.get("/api/account/readiness", headers=other_headers)

    assert owner_readiness.status_code == 200, owner_readiness.text
    assert other_readiness.status_code == 200, other_readiness.text
    owner_payload = owner_readiness.json()
    other_payload = other_readiness.json()
    assert owner_payload["scope"] == "personal_account"
    assert owner_payload["billing_required"] is False
    assert owner_payload["billing_status"] == "not_configured"
    assert owner_payload["workspaces_enabled"] is False
    assert owner_payload["data_isolation"] == "owner_id"
    assert owner_payload["usage"] == {
        "listings": 1,
        "publishing_jobs": 1,
        "platform_accounts": 1,
        "templates": 1,
        "category_mappings": 1,
    }
    assert other_payload["usage"] == {
        "listings": 1,
        "publishing_jobs": 0,
        "platform_accounts": 0,
        "templates": 0,
        "category_mappings": 0,
    }
