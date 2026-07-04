from dataclasses import dataclass, field
from typing import Any

from app.adapters.base import PlatformAdapter, PublishOutcome, ValidationOutcome


@dataclass(frozen=True)
class FakeApiResponse:
    status: str
    platform_listing_id: str | None = None
    platform_url: str | None = None
    message: str = ""
    data: dict[str, Any] = field(default_factory=dict)


class FakeOfficialApiClient:
    """Deterministic test double for future official API provider tests."""

    def __init__(self, responses: list[FakeApiResponse] | None = None):
        self.responses = list(responses or [])
        self.submissions: list[dict[str, Any]] = []
        self._published_by_key: dict[str, FakeApiResponse] = {}

    def create_listing(self, payload: dict[str, Any], idempotency_key: str) -> FakeApiResponse:
        self.submissions.append({"payload": payload, "idempotency_key": idempotency_key})

        if idempotency_key in self._published_by_key:
            previous = self._published_by_key[idempotency_key]
            return FakeApiResponse(
                status=previous.status,
                platform_listing_id=previous.platform_listing_id,
                platform_url=previous.platform_url,
                message="Duplicate idempotency key replayed existing fake API result.",
                data={**previous.data, "duplicate": True},
            )

        response = self.responses.pop(0) if self.responses else self._default_success()
        if response.status == "published" and response.platform_listing_id:
            self._published_by_key[idempotency_key] = response
        return response

    def _default_success(self) -> FakeApiResponse:
        listing_number = len(self.submissions)
        listing_id = f"fake-listing-{listing_number}"
        return FakeApiResponse(
            status="published",
            platform_listing_id=listing_id,
            platform_url=f"https://fake-provider.test/listings/{listing_id}",
            message="Fake official API accepted the listing.",
            data={"fake_provider": True},
        )


class FakeOfficialApiAdapter(PlatformAdapter):
    key = "fake_official_api"
    name = "Fake Official API"
    automation_mode = "official_api"
    posting_url = "https://fake-provider.test/sell"
    required_fields = ["title", "description", "price_cents", "condition", "category", "location"]

    def __init__(self, client: FakeOfficialApiClient | None = None):
        self.client = client or FakeOfficialApiClient()

    def validate_listing(self, listing, overrides: dict[str, Any] | None = None) -> ValidationOutcome:
        overrides = overrides or {}
        missing = []
        for field_name in self.required_fields:
            value = overrides.get(field_name, getattr(listing, field_name, None))
            if value in (None, "", [], {}) or (field_name == "price_cents" and value <= 0):
                missing.append(field_name)
        if not getattr(listing, "images", []):
            missing.append("images")

        return ValidationOutcome(
            ready=not missing,
            missing_fields=missing,
            mapped_fields=self.map_listing_to_platform_fields(listing, overrides),
        )

    def map_listing_to_platform_fields(
        self, listing, overrides: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        overrides = overrides or {}
        return {
            "title": overrides.get("title", listing.title),
            "description": overrides.get("description", listing.description),
            "price_cents": overrides.get("price_cents", listing.price_cents),
            "currency": overrides.get("currency", listing.currency),
            "condition": overrides.get("condition", listing.condition),
            "category": overrides.get("category", listing.category),
            "location": overrides.get("location", listing.location),
            "image_filenames": [image.filename for image in listing.images],
            **overrides.get("platform_fields", {}),
        }

    def publish_listing(self, listing, account=None, overrides: dict[str, Any] | None = None) -> PublishOutcome:
        overrides = overrides or {}
        validation = self.validate_listing(listing, overrides)
        if not validation.ready:
            return PublishOutcome(
                status="failed",
                message=f"Missing required fields: {', '.join(validation.missing_fields)}",
                data={"missing_fields": validation.missing_fields},
            )

        idempotency_key = overrides.get("idempotency_key", self._idempotency_key(listing, account))
        response = self.client.create_listing(validation.mapped_fields, idempotency_key)
        return PublishOutcome(
            status=response.status,
            platform_listing_id=response.platform_listing_id,
            platform_url=response.platform_url,
            message=response.message,
            data={
                "automation_mode": self.automation_mode,
                "fake_provider": True,
                "idempotency_key": idempotency_key,
                **response.data,
            },
        )

    def get_required_fields(self) -> list[str]:
        return list(self.required_fields)

    def get_supported_categories(self) -> list[str]:
        return ["Home and furniture", "Electronics", "Other"]

    def _idempotency_key(self, listing, account=None) -> str:
        account_id = getattr(account, "id", "no-account")
        return f"{getattr(listing, 'id', 'listing')}:{getattr(listing, 'revision', 1)}:{account_id}:{self.key}"
