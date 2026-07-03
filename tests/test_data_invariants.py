import uuid

from app.database import Base, engine
from tests.test_api import client


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def auth_headers():
    response = client.post(
        "/api/auth/register",
        json={
            "email": f"invariant-{uuid.uuid4().hex}@example.com",
            "password": "correct-password",
            "name": "Owner",
        },
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['token']}"}


def test_listing_rejects_negative_money_and_weight():
    headers = auth_headers()

    response = client.post(
        "/api/listings",
        headers=headers,
        json={
            "title": "Invalid listing",
            "price_cents": -1,
            "shipping_cost_cents": -5,
            "weight_grams": -10,
        },
    )

    assert response.status_code == 422
    field_errors = response.json()["error"]["field_errors"]
    assert "price_cents" in field_errors
    assert "shipping_cost_cents" in field_errors
    assert "weight_grams" in field_errors


def test_listing_normalizes_currency_and_tags():
    headers = auth_headers()

    response = client.post(
        "/api/listings",
        headers=headers,
        json={
            "title": "Clean listing",
            "currency": " eur ",
            "tags": [" Lamp ", "", "lamp", "Desk"],
        },
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["currency"] == "EUR"
    assert data["tags"] == ["Lamp", "Desk"]


def test_listing_update_rejects_invalid_currency():
    headers = auth_headers()
    listing_response = client.post("/api/listings", headers=headers, json={"title": "Currency test"})
    assert listing_response.status_code == 200, listing_response.text

    response = client.patch(
        f"/api/listings/{listing_response.json()['id']}",
        headers=headers,
        json={"currency": "EURO"},
    )

    assert response.status_code == 422
    assert "currency" in response.json()["error"]["field_errors"]
