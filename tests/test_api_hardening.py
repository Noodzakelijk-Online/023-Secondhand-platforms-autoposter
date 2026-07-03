import uuid

from tests.test_api import client


def auth_headers():
    response = client.post(
        "/api/auth/register",
        json={
            "email": f"owner-{uuid.uuid4().hex}@example.com",
            "password": "correct-password",
            "name": "Owner",
        },
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['token']}"}


def test_request_id_and_security_headers_are_returned():
    response = client.get("/api/health", headers={"X-Request-ID": "client-request-1"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "client-request-1"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert "camera=()" in response.headers["Permissions-Policy"]


def test_error_responses_use_structured_envelope():
    response = client.get("/api/listings")

    assert response.status_code == 401
    payload = response.json()
    assert payload["error"]["code"] == "UNAUTHORIZED"
    assert payload["error"]["message"] == "Missing bearer token"
    assert payload["error"]["request_id"]


def test_validation_errors_use_structured_envelope():
    headers = auth_headers()
    response = client.get("/api/listings?limit=999", headers=headers)

    assert response.status_code == 422
    payload = response.json()
    assert payload["error"]["code"] == "VALIDATION_ERROR"
    assert "query.limit" in payload["error"]["field_errors"]


def test_listings_support_pagination_filtering_and_sorting():
    headers = auth_headers()
    client.post(
        "/api/listings",
        headers=headers,
        json={
            "title": "Camera bag",
            "description": "Compact shoulder bag.",
            "price_cents": 1500,
            "category": "Accessories",
            "location": "Arnhem",
            "status": "draft",
        },
    )
    client.post(
        "/api/listings",
        headers=headers,
        json={
            "title": "Desk chair",
            "description": "Comfortable office chair.",
            "price_cents": 4000,
            "category": "Home and furniture",
            "location": "Utrecht",
            "status": "draft",
        },
    )

    response = client.get("/api/listings?search=chair&limit=1&offset=0&sort=title", headers=headers)

    assert response.status_code == 200
    assert response.headers["X-Total-Count"] == "1"
    assert response.headers["X-Limit"] == "1"
    assert response.json()[0]["title"] == "Desk chair"
