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


def test_openapi_routes_are_grouped_with_tags():
    response = client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert paths["/api/metrics"]["get"]["tags"] == ["Diagnostics"]
    assert paths["/api/analytics"]["get"]["tags"] == ["Diagnostics"]
    assert paths["/api/auth/login"]["post"]["tags"] == ["Auth"]
    assert paths["/api/listings"]["get"]["tags"] == ["Listings"]
    assert paths["/api/listings/{listing_id}/images"]["post"]["tags"] == ["Images"]
    assert paths["/api/listings/{listing_id}/publish"]["post"]["tags"] == ["Publishing"]
    assert paths["/api/jobs"]["get"]["tags"] == ["Jobs"]
    assert paths["/api/templates/{template_id}"]["patch"]["tags"] == ["Templates"]
    assert paths["/api/export"]["get"]["tags"] == ["Data portability"]


def test_metrics_returns_operational_counts():
    before = client.get("/api/metrics").json()
    headers = auth_headers()
    client.post("/api/listings", headers=headers, json={"title": "Draft metrics", "status": "draft"})
    client.post("/api/listings", headers=headers, json={"title": "Ready metrics", "status": "ready"})

    response = client.get("/api/metrics")

    assert response.status_code == 200
    payload = response.json()
    assert payload["users_total"] == before["users_total"] + 1
    assert payload["listings_total"] == before["listings_total"] + 2
    assert payload["publishing_jobs_total"] == before["publishing_jobs_total"]
    assert payload["platform_accounts_total"] == 0
    assert payload["listing_statuses"]["draft"] == before["listing_statuses"].get("draft", 0) + 1
    assert payload["listing_statuses"]["ready"] == before["listing_statuses"].get("ready", 0) + 1
    assert payload["publishing_job_statuses"] == before["publishing_job_statuses"]


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
    client.post(
        "/api/listings",
        headers=headers,
        json={
            "title": "Dining chair",
            "description": "Wood chair already sold.",
            "price_cents": 6500,
            "category": "Home and furniture",
            "location": "Nijmegen",
            "status": "published",
        },
    )

    response = client.get("/api/listings?search=chair&status=draft&limit=1&offset=0&sort=title", headers=headers)

    assert response.status_code == 200
    assert response.headers["X-Total-Count"] == "1"
    assert response.headers["X-Limit"] == "1"
    assert response.json()[0]["title"] == "Desk chair"

    page_response = client.get("/api/listings?limit=1&offset=1&sort=-price_cents", headers=headers)

    assert page_response.status_code == 200
    assert page_response.headers["X-Total-Count"] == "3"
    assert page_response.headers["X-Offset"] == "1"
    assert page_response.json()[0]["title"] == "Desk chair"
