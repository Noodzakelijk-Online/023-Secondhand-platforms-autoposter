import uuid

from app.database import Base, engine
from tests.test_api import PNG_BYTES, client


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def auth_headers():
    response = client.post(
        "/api/auth/register",
        json={
            "email": f"category-{uuid.uuid4().hex}@example.com",
            "password": "correct-password",
            "name": "Category User",
        },
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['token']}"}


def create_listing(headers):
    response = client.post(
        "/api/listings",
        headers=headers,
        json={
            "title": "Mapped bicycle",
            "description": "City bike in good condition.",
            "price_cents": 8500,
            "condition": "good",
            "category": "Bikes",
            "location": "Arnhem",
            "delivery_options": {"pickup": True},
        },
    )
    assert response.status_code == 200, response.text
    listing_id = response.json()["id"]
    image_response = client.post(
        f"/api/listings/{listing_id}/images",
        headers=headers,
        files={"file": ("bike.png", PNG_BYTES, "image/png")},
    )
    assert image_response.status_code == 200, image_response.text
    return listing_id


def test_category_mapping_crud_and_upsert():
    headers = auth_headers()
    payload = {
        "source_category": "Bikes",
        "platform": "marktplaats",
        "platform_category": "Fietsen en Brommers",
    }

    create_response = client.post("/api/category-mappings", headers=headers, json=payload)
    assert create_response.status_code == 200, create_response.text
    mapping = create_response.json()
    assert mapping["platform_category"] == "Fietsen en Brommers"

    update_response = client.post(
        "/api/category-mappings",
        headers=headers,
        json={**payload, "platform_category": "Fietsen"},
    )
    assert update_response.status_code == 200, update_response.text
    assert update_response.json()["id"] == mapping["id"]
    assert update_response.json()["platform_category"] == "Fietsen"

    list_response = client.get("/api/category-mappings?platform=marktplaats", headers=headers)
    assert list_response.status_code == 200, list_response.text
    assert list_response.headers["X-Total-Count"] == "1"
    assert list_response.json()[0]["source_category"] == "Bikes"

    delete_response = client.delete(f"/api/category-mappings/{mapping['id']}", headers=headers)
    assert delete_response.status_code == 204
    assert client.get("/api/category-mappings", headers=headers).json() == []


def test_category_mapping_is_applied_to_validation_and_publish_package():
    headers = auth_headers()
    listing_id = create_listing(headers)
    mapping_response = client.post(
        "/api/category-mappings",
        headers=headers,
        json={
            "source_category": "Bikes",
            "platform": "marktplaats",
            "platform_category": "Fietsen en Brommers",
        },
    )
    assert mapping_response.status_code == 200, mapping_response.text

    validation_response = client.get(
        f"/api/listings/{listing_id}/validate?platform=marktplaats",
        headers=headers,
    )
    assert validation_response.status_code == 200, validation_response.text
    validation = validation_response.json()[0]
    assert validation["mapped_fields"]["category"] == "Fietsen en Brommers"

    publish_response = client.post(
        f"/api/listings/{listing_id}/publish",
        headers=headers,
        json={"platforms": ["marktplaats"], "process_now": True},
    )
    assert publish_response.status_code == 200, publish_response.text
    mapped_fields = publish_response.json()[0]["result"]["mapped_fields"]
    assert mapped_fields["category"] == "Fietsen en Brommers"
