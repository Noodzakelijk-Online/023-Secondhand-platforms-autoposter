import uuid

from tests.test_api import client


PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\rIHDR"
    b"\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
)


def auth_headers():
    response = client.post(
        "/api/auth/register",
        json={
            "email": f"storage-{uuid.uuid4().hex}@example.com",
            "password": "correct-password",
            "name": "Storage User",
        },
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['token']}"}


def create_listing(headers):
    response = client.post(
        "/api/listings",
        headers=headers,
        json={
            "title": "Storage test listing",
            "description": "Image upload test.",
            "price_cents": 1000,
            "category": "Other",
            "location": "Arnhem",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["id"]


def test_upload_sanitizes_and_records_image_metadata():
    headers = auth_headers()
    listing_id = create_listing(headers)

    response = client.post(
        f"/api/listings/{listing_id}/images",
        headers=headers,
        files={"file": ("..\\bad name.png", PNG_BYTES, "image/png")},
    )

    assert response.status_code == 200, response.text
    image = response.json()["images"][0]
    assert image["filename"] == "bad-name.png"
    assert image["content_type"] == "image/png"
    assert image["file_size"] == len(PNG_BYTES)
    assert len(image["checksum_sha256"]) == 64


def test_duplicate_image_is_not_added_twice():
    headers = auth_headers()
    listing_id = create_listing(headers)

    for _ in range(2):
        response = client.post(
            f"/api/listings/{listing_id}/images",
            headers=headers,
            files={"file": ("photo.png", PNG_BYTES, "image/png")},
        )
        assert response.status_code == 200, response.text

    assert len(response.json()["images"]) == 1


def test_upload_rejects_non_image_content():
    headers = auth_headers()
    listing_id = create_listing(headers)

    response = client.post(
        f"/api/listings/{listing_id}/images",
        headers=headers,
        files={"file": ("notes.txt", b"not an image", "text/plain")},
    )

    assert response.status_code == 415
    assert response.json()["error"]["code"] == "UNSUPPORTED_MEDIA_TYPE"
