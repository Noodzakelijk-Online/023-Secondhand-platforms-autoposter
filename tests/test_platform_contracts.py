from pathlib import Path
from types import SimpleNamespace

import pytest

from app.adapters.registry import ADAPTERS, list_platforms


def ready_listing():
    return SimpleNamespace(
        title="Contract lamp",
        description="Complete listing used to verify platform-specific adapter contracts.",
        price_cents=2500,
        currency="EUR",
        condition="used",
        category="Home and furniture",
        location="Arnhem",
        delivery_options={"pickup": True, "shipping": False},
        pickup_allowed=True,
        shipping_allowed=False,
        shipping_cost_cents=0,
        dimensions={"width_cm": 20, "height_cm": 40},
        weight_grams=1200,
        brand="Anglepoise",
        model="Desk",
        color="Green",
        material="Metal",
        tags=["lamp", "desk"],
        images=[SimpleNamespace(filename="lamp.png")],
    )


def incomplete_listing():
    listing = ready_listing()
    listing.title = ""
    listing.description = ""
    listing.price_cents = 0
    listing.location = ""
    listing.images = []
    return listing


@pytest.mark.parametrize("platform_key,adapter", ADAPTERS.items())
def test_platform_contract_validates_maps_and_requires_user_action(platform_key, adapter):
    listing = ready_listing()

    validation = adapter.validate_listing(listing, overrides={})
    mapped = adapter.map_listing_to_platform_fields(listing, overrides={})
    outcome = adapter.publish_listing(listing, account=None, overrides={})

    assert validation.ready is True
    assert validation.missing_fields == []
    assert mapped["title"] == listing.title
    assert mapped["price"] == 25
    assert mapped["image_filenames"] == ["lamp.png"]
    assert outcome.status == "needs_user_action"
    assert outcome.platform_listing_id is None
    assert outcome.platform_url == adapter.posting_url
    assert outcome.data["automation_mode"] == "assisted"
    assert outcome.data["mapped_fields"]["title"] == listing.title
    assert platform_key in ADAPTERS


@pytest.mark.parametrize("platform_key,adapter", ADAPTERS.items())
def test_platform_contract_reports_missing_fields(platform_key, adapter):
    validation = adapter.validate_listing(incomplete_listing(), overrides={})

    assert validation.ready is False
    assert "title" in validation.missing_fields
    assert "description" in validation.missing_fields
    assert "price_cents" in validation.missing_fields
    assert "location" in validation.missing_fields
    assert "images" in validation.missing_fields
    assert platform_key in ADAPTERS


def test_platform_metadata_contracts_are_specific_and_honest():
    platforms = {platform["key"]: platform for platform in list_platforms()}

    assert set(platforms) == set(ADAPTERS)
    for platform in platforms.values():
        capabilities = platform["capabilities"]
        assert platform["automation_mode"] == "assisted"
        assert platform["posting_url"]
        assert platform["required_fields"]
        assert platform["supported_categories"]
        assert capabilities["prepared_fields"]
        assert capabilities["account_requirements"]
        assert capabilities["manual_steps"]
        assert capabilities["requires_user_final_submission"] is True
        assert "final_submission" in capabilities["blocked_actions"]

    assert "paid_placement_choices" in platforms["marktplaats"]["capabilities"]["blocked_actions"]
    assert "neighborhood_permission_checks" in platforms["nextdoor"]["capabilities"]["blocked_actions"]
    assert "oauth_token_exchange" in platforms["ebay"]["capabilities"]["blocked_actions"]
    assert platforms["ebay"]["capabilities"]["official_api_candidate"] is True
    assert platforms["ebay"]["capabilities"]["supports_official_api"] is False
    assert "scraping_without_user_control" in platforms["tweedehands"]["capabilities"]["blocked_actions"]


def test_platform_completion_contract_document_covers_registered_platforms():
    content = Path("docs/PLATFORM_COMPLETION_CONTRACTS.md").read_text(encoding="utf-8")

    for platform in list_platforms():
        assert platform["name"] in content
    assert "must not mark a job as published" in content
    assert "official API credential checklist" in content
