import json
import uuid
from pathlib import Path

from app.database import Base, SessionLocal, engine
from app.models import AuditEvent, CategoryMapping, Listing, ListingTemplate, PlatformAccount, PublishingJob, User
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

    db = SessionLocal()
    try:
        event = db.query(AuditEvent).filter(AuditEvent.action == "data_exported").one()
        assert event.user_email_hash
        assert event.event_data == {
            "listings": 1,
            "platform_accounts": 1,
            "templates": 1,
            "category_mappings": 1,
        }
        assert "export-" not in json.dumps(event.event_data)
    finally:
        db.close()


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

    db = SessionLocal()
    try:
        event = db.query(AuditEvent).filter(AuditEvent.action == "data_imported").one()
        assert event.event_data["listings_created"] == 1
        assert event.event_data["platform_accounts_created"] == 1
        assert event.event_data["skipped"] == 0
    finally:
        db.close()


def test_delete_me_purges_owned_data_and_revokes_session():
    headers = auth_headers("delete")
    create_portable_workspace(headers)
    listing = client.get("/api/listings", headers=headers).json()[0]
    image_response = client.post(
        f"/api/listings/{listing['id']}/images",
        headers=headers,
        files={"file": ("cabinet.png", PNG_BYTES, "image/png")},
    )
    assert image_response.status_code == 200, image_response.text
    image_path = image_response.json()["images"][0]["storage_path"]
    publish_response = client.post(
        f"/api/listings/{listing['id']}/publish",
        headers=headers,
        json={"platforms": ["marktplaats"], "process_now": True},
    )
    assert publish_response.status_code == 200, publish_response.text

    other_headers = auth_headers("keep")
    other_listing = client.post("/api/listings", headers=other_headers, json={"title": "Keep me"})
    assert other_listing.status_code == 200, other_listing.text

    delete_response = client.delete("/api/auth/me", headers=headers)

    assert delete_response.status_code == 204, delete_response.text
    assert client.get("/api/auth/me", headers=headers).status_code == 401
    assert client.get("/api/listings", headers=other_headers).json()[0]["title"] == "Keep me"

    db = SessionLocal()
    try:
        assert db.query(User).filter(User.email.like("delete-%")).count() == 0
        assert db.query(Listing).filter(Listing.title == "Portable cabinet").count() == 0
        assert db.query(PublishingJob).count() == 0
        assert db.query(PlatformAccount).filter(PlatformAccount.display_name == "Portable eBay").count() == 0
        assert db.query(ListingTemplate).filter(ListingTemplate.name == "Pickup").count() == 0
        assert db.query(CategoryMapping).filter(CategoryMapping.source_category == "Furniture").count() == 0
        event = db.query(AuditEvent).filter(AuditEvent.action == "account_deleted").one()
        assert event.user_id is not None
        assert event.user_email_hash
        assert event.event_data["listings_deleted"] == 1
        assert event.event_data["jobs_deleted"] == 1
        assert event.event_data["images_deleted"] == 1
        assert event.event_data["platform_accounts_deleted"] == 1
        assert "delete-" not in json.dumps(event.event_data)
    finally:
        db.close()
    assert not Path(image_path).exists()
