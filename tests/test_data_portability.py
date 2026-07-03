import json
import uuid

from app.database import Base, SessionLocal, engine
from app.models import PlatformAccount
from tests.test_api import client


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


def create_portable_workspace(headers):
    listing_response = client.post(
        "/api/listings",
        headers=headers,
        json={
            "title": "Portable cabinet",
            "description": "Oak cabinet with two drawers.",
            "price_cents": 11900,
            "condition": "used",
            "category": "Furniture",
            "location": "Arnhem",
            "brand": "Vintage Co",
            "shipping_allowed": True,
            "shipping_cost_cents": 1500,
            "tags": ["cabinet", "oak"],
        },
    )
    assert listing_response.status_code == 200, listing_response.text
    listing_id = listing_response.json()["id"]

    override_response = client.post(
        f"/api/listings/{listing_id}/platforms",
        headers=headers,
        json={
            "platform": "marktplaats",
            "overrides": {"description": "Marktplaats specific copy"},
            "selected": True,
        },
    )
    assert override_response.status_code == 200, override_response.text

    account_response = client.post(
        "/api/accounts",
        headers=headers,
        json={
            "platform": "ebay",
            "display_name": "Portable eBay",
            "mode": "assisted",
            "status": "ready",
            "connection_data": {"store": "main", "access_token": "do-not-export"},
        },
    )
    assert account_response.status_code == 200, account_response.text

    db = SessionLocal()
    try:
        account = db.query(PlatformAccount).filter(PlatformAccount.display_name == "Portable eBay").one()
        account.secret_ref = "vault://secret/platform-token"
        db.commit()
    finally:
        db.close()

    template_response = client.post(
        "/api/templates",
        headers=headers,
        json={"name": "Pickup", "platform": None, "body": "Pickup is available by appointment."},
    )
    assert template_response.status_code == 200, template_response.text

    mapping_response = client.post(
        "/api/category-mappings",
        headers=headers,
        json={
            "source_category": "Furniture",
            "platform": "marktplaats",
            "platform_category": "Huis en Inrichting",
        },
    )
    assert mapping_response.status_code == 200, mapping_response.text


def test_export_omits_private_and_secret_fields():
    headers = auth_headers("export")
    create_portable_workspace(headers)

    response = client.get("/api/export", headers=headers)

    assert response.status_code == 200, response.text
    bundle = response.json()
    assert bundle["version"] == "1"
    assert bundle["listings"][0]["title"] == "Portable cabinet"
    assert bundle["listings"][0]["platform_mappings"][0]["platform"] == "marktplaats"
    assert bundle["platform_accounts"][0]["connection_data"] == {"store": "main"}

    serialized = json.dumps(bundle)
    assert "password_hash" not in serialized
    assert "token_hash" not in serialized
    assert "revoked_at" not in serialized
    assert "secret_ref" not in serialized
    assert "vault://secret/platform-token" not in serialized
    assert "do-not-export" not in serialized


def test_import_recreates_user_owned_business_data():
    source_headers = auth_headers("source")
    create_portable_workspace(source_headers)
    bundle = client.get("/api/export", headers=source_headers).json()

    target_headers = auth_headers("target")
    import_response = client.post("/api/import", headers=target_headers, json=bundle)

    assert import_response.status_code == 200, import_response.text
    result = import_response.json()
    assert result["listings_created"] == 1
    assert result["platform_mappings_created"] == 1
    assert result["platform_accounts_created"] == 1
    assert result["templates_created"] == 1
    assert result["category_mappings_created"] == 1

    listings = client.get("/api/listings", headers=target_headers).json()
    assert len(listings) == 1
    assert listings[0]["title"] == "Portable cabinet"
    assert listings[0]["platform_mappings"][0]["status"] == "draft"
    assert listings[0]["platform_mappings"][0]["overrides"]["description"] == "Marktplaats specific copy"

    accounts = client.get("/api/accounts", headers=target_headers).json()
    assert accounts[0]["display_name"] == "Portable eBay"
    assert "secret_ref" not in accounts[0]

    templates = client.get("/api/templates", headers=target_headers).json()
    assert templates[0]["name"] == "Pickup"

    mappings = client.get("/api/category-mappings", headers=target_headers).json()
    assert mappings[0]["platform_category"] == "Huis en Inrichting"
