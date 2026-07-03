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
            "email": f"revision-{uuid.uuid4().hex}@example.com",
            "password": "correct-password",
            "name": "Revision User",
        },
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['token']}"}


def create_ready_listing(headers):
    response = client.post(
        "/api/listings",
        headers=headers,
        json={
            "title": "Revision lamp",
            "description": "A listing with richer domain fields.",
            "price_cents": 2000,
            "condition": "good",
            "category": "Home and furniture",
            "location": "Arnhem",
            "delivery_options": {"pickup": True},
            "pickup_allowed": True,
            "shipping_allowed": True,
            "shipping_cost_cents": 695,
            "dimensions": {"width_cm": 20, "height_cm": 40},
            "weight_grams": 1200,
            "brand": "Anglepoise",
            "model": "Type 75",
            "color": "black",
            "material": "metal",
            "notes": "Small scratch on base.",
            "internal_notes": "Bought at estate sale.",
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


def test_listing_revision_increments_and_fields_round_trip():
    headers = auth_headers()
    listing_id = create_ready_listing(headers)

    before = client.get(f"/api/listings/{listing_id}", headers=headers).json()
    assert before["revision"] == 1
    assert before["shipping_allowed"] is True
    assert before["shipping_cost_cents"] == 695
    assert before["dimensions"]["height_cm"] == 40
    assert before["brand"] == "Anglepoise"

    response = client.patch(
        f"/api/listings/{listing_id}",
        headers=headers,
        json={"title": "Updated revision lamp", "weight_grams": 1300},
    )

    assert response.status_code == 200, response.text
    listing = response.json()
    assert listing["revision"] == 2
    assert listing["title"] == "Updated revision lamp"
    assert listing["weight_grams"] == 1300


def test_publish_idempotency_is_revision_aware():
    headers = auth_headers()
    listing_id = create_ready_listing(headers)

    first = client.post(
        f"/api/listings/{listing_id}/publish",
        headers=headers,
        json={"platforms": ["marktplaats"], "process_now": True},
    ).json()[0]
    second = client.post(
        f"/api/listings/{listing_id}/publish",
        headers=headers,
        json={"platforms": ["marktplaats"], "process_now": True},
    ).json()[0]

    assert second["id"] == first["id"]
    assert first["listing_revision"] == 1
    assert first["action_type"] == "publish"
    assert first["operation_mode"] == "assisted"

    update = client.patch(
        f"/api/listings/{listing_id}",
        headers=headers,
        json={"description": "Changed enough to create a new publish package."},
    )
    assert update.status_code == 200, update.text

    third = client.post(
        f"/api/listings/{listing_id}/publish",
        headers=headers,
        json={"platforms": ["marktplaats"], "process_now": True},
    ).json()[0]

    assert third["id"] != first["id"]
    assert third["listing_revision"] == 2
