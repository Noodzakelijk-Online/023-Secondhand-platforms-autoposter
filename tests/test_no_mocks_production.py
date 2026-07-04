from types import SimpleNamespace

from app.adapters.registry import ADAPTERS


def ready_listing():
    return SimpleNamespace(
        title="No mocks lamp",
        description="A complete listing for adapter honesty checks.",
        price_cents=2500,
        currency="EUR",
        condition="used",
        category="Home and furniture",
        location="Arnhem",
        delivery_options={"pickup": True},
        pickup_allowed=True,
        shipping_allowed=False,
        shipping_cost_cents=0,
        dimensions={},
        weight_grams=0,
        brand="",
        model="",
        color="",
        material="",
        tags=[],
        images=[SimpleNamespace(filename="lamp.png")],
    )


def test_registered_production_adapters_do_not_fake_published_success():
    listing = ready_listing()

    for adapter in ADAPTERS.values():
        assert adapter.automation_mode == "assisted"
        outcome = adapter.publish_listing(listing, account=None, overrides={})

        assert outcome.status == "needs_user_action"
        assert outcome.platform_listing_id is None
        assert outcome.data["automation_mode"] == "assisted"
