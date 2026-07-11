import uuid

from app.database import Base, engine
from tests.test_api import PNG_BYTES, client


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def register(label: str) -> dict[str, str]:
    response = client.post(
        "/api/auth/register",
        json={
            "email": f"{label}-{uuid.uuid4().hex}@example.com",
            "password": "correct-password",
            "name": label,
        },
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['token']}"}


def test_seller_acceptance_workflow_from_setup_to_portability():
    seller_headers = register("acceptance-seller")

    account_response = client.post(
        "/api/accounts",
        headers=seller_headers,
        json={
            "platform": "ebay",
            "display_name": "Acceptance eBay",
            "status": "ready",
            "connection_data": {"store": "main", "access_token": "never-export"},
        },
    )
    assert account_response.status_code == 200, account_response.text

    template_response = client.post(
        "/api/templates",
        headers=seller_headers,
        json={
            "name": "Furniture pickup",
            "variant": "short",
            "platform": "marktplaats",
            "body": "Pickup available by appointment.",
        },
    )
    assert template_response.status_code == 200, template_response.text

    mapping_response = client.post(
        "/api/category-mappings",
        headers=seller_headers,
        json={
            "source_category": "Home and furniture",
            "platform": "marktplaats",
            "platform_category": "Huis en Inrichting",
        },
    )
    assert mapping_response.status_code == 200, mapping_response.text

    listing_response = client.post(
        "/api/listings",
        headers=seller_headers,
        json={
            "title": "Solid oak side table",
            "description": (
                "Solid oak side table in good used condition. Dimensions are 60 cm wide, "
                "45 cm deep, and 55 cm high. Minor wear on the top as pictured."
            ),
            "price_cents": 4500,
            "condition": "good",
            "category": "Home and furniture",
            "location": "Utrecht",
            "delivery_options": {"pickup": True, "shipping": False},
            "pickup_allowed": True,
            "shipping_allowed": False,
            "dimensions": {"width_cm": 60, "depth_cm": 45, "height_cm": 55},
            "material": "oak",
            "tags": ["furniture", "oak", "side table"],
        },
    )
    assert listing_response.status_code == 200, listing_response.text
    listing_id = listing_response.json()["id"]

    image_response = client.post(
        f"/api/listings/{listing_id}/images",
        headers=seller_headers,
        files={"file": ("table.png", PNG_BYTES, "image/png")},
    )
    assert image_response.status_code == 200, image_response.text
    assert image_response.json()["images"][0]["checksum_sha256"]

    quality_response = client.get(f"/api/listings/{listing_id}/quality", headers=seller_headers)
    assert quality_response.status_code == 200, quality_response.text
    quality = quality_response.json()
    assert quality["score"] >= 80
    assert quality["checklist"]["has_images"] is True

    validation_response = client.get(
        f"/api/listings/{listing_id}/validate?platform=marktplaats",
        headers=seller_headers,
    )
    assert validation_response.status_code == 200, validation_response.text
    validation = validation_response.json()[0]
    assert validation["ready"] is True
    assert validation["missing_fields"] == []
    assert validation["mapped_fields"]["category"] == "Huis en Inrichting"

    publish_response = client.post(
        f"/api/listings/{listing_id}/publish",
        headers=seller_headers,
        json={"platforms": ["marktplaats"], "process_now": True},
    )
    assert publish_response.status_code == 200, publish_response.text
    job = publish_response.json()[0]
    assert job["status"] == "needs_user_action"
    assert job["operation_mode"] == "assisted"
    assert job["result"]["automation_mode"] == "assisted"
    assert job["result"]["mapped_fields"]["title"] == "Solid oak side table"

    jobs_response = client.get("/api/jobs?status=needs_user_action", headers=seller_headers)
    assert jobs_response.status_code == 200, jobs_response.text
    assert [queued_job["id"] for queued_job in jobs_response.json()] == [job["id"]]

    detail_response = client.get(f"/api/jobs/{job['id']}", headers=seller_headers)
    assert detail_response.status_code == 200, detail_response.text
    assert detail_response.json()["logs"]

    analytics_response = client.get("/api/analytics", headers=seller_headers)
    assert analytics_response.status_code == 200, analytics_response.text
    analytics = analytics_response.json()
    assert analytics["external_tracking"] is False
    assert analytics["summary"]["listings_total"] == 1
    assert analytics["job_statuses"]["needs_user_action"] == 1

    export_response = client.get("/api/export", headers=seller_headers)
    assert export_response.status_code == 200, export_response.text
    bundle = export_response.json()
    assert bundle["listings"][0]["title"] == "Solid oak side table"
    assert bundle["platform_accounts"][0]["connection_data"] == {"store": "main"}
    assert "never-export" not in export_response.text

    target_headers = register("acceptance-import")
    import_response = client.post("/api/import", headers=target_headers, json=bundle)
    assert import_response.status_code == 200, import_response.text
    imported = import_response.json()
    assert imported["listings_created"] == 1
    assert imported["platform_accounts_created"] == 1
    assert imported["templates_created"] == 1
    assert imported["category_mappings_created"] == 1

    imported_listings = client.get("/api/listings", headers=target_headers).json()
    assert imported_listings[0]["title"] == "Solid oak side table"

    audit_response = client.get("/api/audit-events", headers=seller_headers)
    assert audit_response.status_code == 200, audit_response.text
    assert "data_exported" in {event["action"] for event in audit_response.json()}
