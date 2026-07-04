from types import SimpleNamespace

from app.adapters.registry import ADAPTERS
from tests.fake_provider_lab import FakeApiResponse, FakeOfficialApiAdapter, FakeOfficialApiClient


def ready_listing():
    return SimpleNamespace(
        id=42,
        revision=3,
        title="Fake API lamp",
        description="Ready for fake official API testing.",
        price_cents=2500,
        currency="EUR",
        condition="used",
        category="Home and furniture",
        location="Arnhem",
        images=[SimpleNamespace(filename="lamp.png")],
    )


def test_fake_provider_lab_is_not_registered_as_production_adapter():
    assert FakeOfficialApiAdapter.key not in ADAPTERS


def test_fake_provider_lab_publishes_deterministic_success():
    client = FakeOfficialApiClient()
    adapter = FakeOfficialApiAdapter(client)

    outcome = adapter.publish_listing(ready_listing(), overrides={"idempotency_key": "listing-42"})

    assert outcome.status == "published"
    assert outcome.platform_listing_id == "fake-listing-1"
    assert outcome.platform_url == "https://fake-provider.test/listings/fake-listing-1"
    assert outcome.data["automation_mode"] == "official_api"
    assert outcome.data["fake_provider"] is True
    assert client.submissions[0]["idempotency_key"] == "listing-42"


def test_fake_provider_lab_replays_idempotent_success():
    client = FakeOfficialApiClient()
    adapter = FakeOfficialApiAdapter(client)
    listing = ready_listing()

    first = adapter.publish_listing(listing, overrides={"idempotency_key": "same-key"})
    second = adapter.publish_listing(listing, overrides={"idempotency_key": "same-key"})

    assert first.status == "published"
    assert second.status == "published"
    assert second.platform_listing_id == first.platform_listing_id
    assert second.data["duplicate"] is True


def test_fake_provider_lab_can_queue_api_failures():
    client = FakeOfficialApiClient(
        responses=[
            FakeApiResponse(
                status="failed",
                message="Sandbox rejected the category.",
                data={"error_code": "category_invalid"},
            )
        ]
    )
    adapter = FakeOfficialApiAdapter(client)

    outcome = adapter.publish_listing(ready_listing(), overrides={"idempotency_key": "bad-category"})

    assert outcome.status == "failed"
    assert outcome.platform_listing_id is None
    assert outcome.message == "Sandbox rejected the category."
    assert outcome.data["error_code"] == "category_invalid"


def test_fake_provider_lab_validates_required_listing_fields():
    listing = ready_listing()
    listing.images = []
    adapter = FakeOfficialApiAdapter()

    outcome = adapter.publish_listing(listing)

    assert outcome.status == "failed"
    assert outcome.data["missing_fields"] == ["images"]
