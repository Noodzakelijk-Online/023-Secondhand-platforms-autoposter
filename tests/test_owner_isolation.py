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
            "email": f"{label}-{uuid.uuid4().hex}@example.com",
            "password": "correct-password",
            "name": label,
        },
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['token']}"}


def create_ready_listing(headers: dict[str, str]) -> int:
    response = client.post(
        "/api/listings",
        headers=headers,
        json={
            "title": "Owner scoped listing",
            "description": "Ready for ownership checks.",
            "price_cents": 2200,
            "condition": "used",
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
        files={"file": ("listing.png", PNG_BYTES, "image/png")},
    )
    assert image_response.status_code == 200, image_response.text
    return listing_id


def test_platform_accounts_are_owner_scoped():
    owner_headers = auth_headers("account-owner")
    other_headers = auth_headers("account-other")
    account_response = client.post(
        "/api/accounts",
        headers=owner_headers,
        json={"platform": "ebay", "display_name": "Owner eBay", "status": "needs_setup"},
    )
    assert account_response.status_code == 200, account_response.text
    account_id = account_response.json()["id"]

    assert client.get("/api/accounts", headers=other_headers).json() == []
    assert client.delete(f"/api/accounts/{account_id}", headers=other_headers).status_code == 404

    owner_accounts = client.get("/api/accounts", headers=owner_headers).json()
    assert [account["id"] for account in owner_accounts] == [account_id]


def test_category_mappings_are_owner_scoped():
    owner_headers = auth_headers("mapping-owner")
    other_headers = auth_headers("mapping-other")
    mapping_response = client.post(
        "/api/category-mappings",
        headers=owner_headers,
        json={
            "source_category": "Bikes",
            "platform": "marktplaats",
            "platform_category": "Fietsen",
        },
    )
    assert mapping_response.status_code == 200, mapping_response.text
    mapping_id = mapping_response.json()["id"]

    assert client.get("/api/category-mappings", headers=other_headers).json() == []
    assert (
        client.patch(
            f"/api/category-mappings/{mapping_id}",
            headers=other_headers,
            json={"platform_category": "Not mine"},
        ).status_code
        == 404
    )
    assert client.delete(f"/api/category-mappings/{mapping_id}", headers=other_headers).status_code == 404

    owner_mappings = client.get("/api/category-mappings", headers=owner_headers).json()
    assert [mapping["id"] for mapping in owner_mappings] == [mapping_id]


def test_listing_jobs_are_owner_scoped():
    owner_headers = auth_headers("job-owner")
    other_headers = auth_headers("job-other")
    listing_id = create_ready_listing(owner_headers)
    publish_response = client.post(
        f"/api/listings/{listing_id}/publish",
        headers=owner_headers,
        json={"platforms": ["marktplaats"], "process_now": True},
    )
    assert publish_response.status_code == 200, publish_response.text
    job_id = publish_response.json()[0]["id"]

    assert client.get("/api/jobs", headers=other_headers).json() == []
    assert client.get(f"/api/jobs/{job_id}", headers=other_headers).status_code == 404
    assert client.post(f"/api/jobs/{job_id}/retry", headers=other_headers).status_code == 404

    owner_jobs = client.get("/api/jobs", headers=owner_headers).json()
    assert [job["id"] for job in owner_jobs] == [job_id]
