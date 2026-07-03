from typing import Any

from app.adapters.base import PlatformAdapter, PublishOutcome, ValidationOutcome

COMMON_CATEGORIES = [
    "Electronics",
    "Home and furniture",
    "Clothing and accessories",
    "Books and media",
    "Sports and outdoor",
    "Tools",
    "Baby and children",
    "Vehicles",
    "Garden",
    "Other",
]


class AssistedPostingAdapter(PlatformAdapter):
    key = "assisted"
    name = "Assisted platform"
    automation_mode = "assisted"
    posting_url = ""
    required_fields = ["title", "description", "price_cents", "condition", "category", "location"]
    supported_categories = COMMON_CATEGORIES
    extra_warnings: list[str] = []

    def get_required_fields(self) -> list[str]:
        return list(self.required_fields)

    def get_supported_categories(self) -> list[str]:
        return list(self.supported_categories)

    def _value_for(self, listing, field: str, overrides: dict[str, Any]) -> Any:
        if field in overrides and overrides[field] not in (None, "", []):
            return overrides[field]
        return getattr(listing, field, None)

    def validate_listing(self, listing, overrides: dict[str, Any] | None = None) -> ValidationOutcome:
        overrides = overrides or {}
        missing = []
        for field in self.get_required_fields():
            value = self._value_for(listing, field, overrides)
            if value in (None, "", [], {}) or (field == "price_cents" and value <= 0):
                missing.append(field)

        if not listing.images:
            missing.append("images")

        mapped = self.map_listing_to_platform_fields(listing, overrides)
        return ValidationOutcome(
            ready=not missing,
            missing_fields=missing,
            warnings=list(self.extra_warnings),
            mapped_fields=mapped,
        )

    def map_listing_to_platform_fields(
        self, listing, overrides: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        overrides = overrides or {}
        fields = {
            "title": overrides.get("title", listing.title),
            "description": overrides.get("description", listing.description),
            "price": overrides.get("price_cents", listing.price_cents) / 100,
            "currency": overrides.get("currency", listing.currency),
            "condition": overrides.get("condition", listing.condition),
            "category": overrides.get("category", listing.category),
            "location": overrides.get("location", listing.location),
            "delivery_options": overrides.get("delivery_options", listing.delivery_options),
            "pickup_allowed": overrides.get("pickup_allowed", listing.pickup_allowed),
            "shipping_allowed": overrides.get("shipping_allowed", listing.shipping_allowed),
            "shipping_cost": overrides.get("shipping_cost_cents", listing.shipping_cost_cents) / 100,
            "dimensions": overrides.get("dimensions", listing.dimensions),
            "weight_grams": overrides.get("weight_grams", listing.weight_grams),
            "brand": overrides.get("brand", listing.brand),
            "model": overrides.get("model", listing.model),
            "color": overrides.get("color", listing.color),
            "material": overrides.get("material", listing.material),
            "tags": overrides.get("tags", listing.tags),
            "image_filenames": [image.filename for image in listing.images],
        }
        fields.update(overrides.get("platform_fields", {}))
        return fields

    def publish_listing(self, listing, account=None, overrides: dict[str, Any] | None = None) -> PublishOutcome:
        validation = self.validate_listing(listing, overrides)
        if not validation.ready:
            return PublishOutcome(
                status="failed",
                message=f"Missing required fields: {', '.join(validation.missing_fields)}",
                data={"missing_fields": validation.missing_fields, "warnings": validation.warnings},
            )

        return PublishOutcome(
            status="needs_user_action",
            platform_url=self.posting_url,
            message=(
                "Prepared assisted posting package. Open the platform, review the mapped fields, "
                "and complete any login, CAPTCHA, payment, or confirmation step yourself."
            ),
            data={
                "automation_mode": self.automation_mode,
                "posting_url": self.posting_url,
                "mapped_fields": validation.mapped_fields,
                "warnings": validation.warnings,
            },
        )


class MarktplaatsAdapter(AssistedPostingAdapter):
    key = "marktplaats"
    name = "Marktplaats"
    posting_url = "https://www.marktplaats.nl/plaats"
    required_fields = AssistedPostingAdapter.required_fields + ["delivery_options"]
    supported_categories = COMMON_CATEGORIES + ["Bicycles", "Collectibles", "Music instruments"]
    extra_warnings = [
        "Marktplaats is configured as assisted posting because login, two-factor checks, "
        "paid placement choices, and anti-abuse controls may require the account owner."
    ]


class KooppleinAdapter(AssistedPostingAdapter):
    key = "koopplein"
    name = "Koopplein"
    posting_url = "https://koopplein.nl/nederland/advertenties/edit"
    supported_categories = COMMON_CATEGORIES + ["Free", "Wanted"]
    extra_warnings = [
        "Koopplein is configured as assisted posting; review category and price type before final submission."
    ]


class NextdoorAdapter(AssistedPostingAdapter):
    key = "nextdoor"
    name = "Nextdoor"
    posting_url = "https://nextdoor.nl/for_sale_and_free/"
    required_fields = ["title", "description", "price_cents", "category", "location"]
    supported_categories = [
        "Other",
        "Appliances",
        "Electronics",
        "Bicycles",
        "Furniture",
        "Tools",
        "Children and baby",
        "Clothing and accessories",
        "Sport and outdoor",
        "Garden",
    ]
    extra_warnings = [
        "Nextdoor posting remains assisted because neighborhood account controls and confirmations "
        "must stay user-controlled."
    ]


class EbayAdapter(AssistedPostingAdapter):
    key = "ebay"
    name = "eBay"
    posting_url = "https://www.ebay.nl/sl/sell"
    required_fields = AssistedPostingAdapter.required_fields + ["delivery_options"]
    supported_categories = COMMON_CATEGORIES + ["Collectibles", "Parts and accessories"]
    extra_warnings = [
        "eBay can support official API integration later, but this build stays assisted "
        "until OAuth credentials and marketplace policies are configured."
    ]


class TweedehandsAdapter(AssistedPostingAdapter):
    key = "tweedehands"
    name = "Tweedehands"
    posting_url = "https://www.tweedehands.net"
    extra_warnings = [
        "Tweedehands import/posting is assisted; use the legacy scraper only in a user-controlled "
        "session that respects site rules."
    ]
