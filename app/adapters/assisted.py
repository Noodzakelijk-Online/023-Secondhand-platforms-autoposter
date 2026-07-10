from typing import Any

from app.adapters.base import PlatformAdapter, PlatformCapabilities, PublishOutcome, ValidationOutcome

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

COMMON_PREPARED_FIELDS = [
    "title",
    "description",
    "price",
    "currency",
    "condition",
    "category",
    "location",
    "delivery_options",
    "pickup_allowed",
    "shipping_allowed",
    "shipping_cost",
    "dimensions",
    "weight_grams",
    "brand",
    "model",
    "color",
    "material",
    "tags",
    "image_filenames",
]

ASSISTED_CAPABILITIES = PlatformCapabilities(
    prepared_fields=COMMON_PREPARED_FIELDS,
    account_requirements=[
        "User-controlled marketplace account",
        "Manual login or active platform session when the platform asks for it",
    ],
    manual_steps=[
        "Open the platform posting page",
        "Copy the prepared fields into the marketplace form",
        "Complete any account, verification, payment, or confirmation prompt",
        "Review the marketplace preview and submit manually",
    ],
    blocked_actions=[
        "login",
        "captcha_or_anti_abuse_checks",
        "two_factor_or_sms_prompts",
        "paid_placement_choices",
        "final_submission",
    ],
    rate_limit_policy=(
        "The app rate-limits local package preparation; final marketplace submission remains user-controlled."
    ),
)


class AssistedPostingAdapter(PlatformAdapter):
    key = "assisted"
    name = "Assisted platform"
    automation_mode = "assisted"
    posting_url = ""
    required_fields = ["title", "description", "price_cents", "condition", "category", "location"]
    supported_categories = COMMON_CATEGORIES
    capabilities = ASSISTED_CAPABILITIES
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
    capabilities = PlatformCapabilities(
        prepared_fields=COMMON_PREPARED_FIELDS,
        account_requirements=[
            "Marktplaats account",
            "Manual login or active session",
            "User review of category, shipping, paid placement, and confirmation choices",
        ],
        manual_steps=ASSISTED_CAPABILITIES.manual_steps,
        blocked_actions=ASSISTED_CAPABILITIES.blocked_actions,
        rate_limit_policy=ASSISTED_CAPABILITIES.rate_limit_policy,
    )
    extra_warnings = [
        "Marktplaats is configured as assisted posting because login, two-factor checks, "
        "paid placement choices, and anti-abuse controls may require the account owner."
    ]


class KooppleinAdapter(AssistedPostingAdapter):
    key = "koopplein"
    name = "Koopplein"
    posting_url = "https://koopplein.nl/nederland/advertenties/edit"
    supported_categories = COMMON_CATEGORIES + ["Free", "Wanted"]
    capabilities = PlatformCapabilities(
        prepared_fields=COMMON_PREPARED_FIELDS,
        account_requirements=[
            "Koopplein account if the platform requires one for the chosen listing",
            "User review of category, price type, and final confirmation",
        ],
        manual_steps=ASSISTED_CAPABILITIES.manual_steps,
        blocked_actions=ASSISTED_CAPABILITIES.blocked_actions,
        rate_limit_policy=ASSISTED_CAPABILITIES.rate_limit_policy,
    )
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
    capabilities = PlatformCapabilities(
        prepared_fields=[
            "title",
            "description",
            "price",
            "currency",
            "category",
            "location",
            "image_filenames",
            "tags",
        ],
        account_requirements=[
            "Nextdoor account",
            "Neighborhood access and any user-controlled local posting permissions",
        ],
        manual_steps=[
            "Open the Nextdoor for-sale posting page",
            "Copy the prepared listing fields",
            "Review neighborhood visibility and platform confirmations",
            "Submit manually from the account owner's session",
        ],
        blocked_actions=[
            "login",
            "captcha_or_anti_abuse_checks",
            "neighborhood_permission_checks",
            "final_submission",
        ],
        rate_limit_policy=ASSISTED_CAPABILITIES.rate_limit_policy,
    )
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
    capabilities = PlatformCapabilities(
        prepared_fields=COMMON_PREPARED_FIELDS,
        supports_official_api=False,
        official_api_candidate=True,
        account_requirements=[
            "eBay seller account",
            "Seller policy, payment, shipping, and return settings when required by eBay",
            "OAuth credentials and token storage before any future official API publishing",
        ],
        manual_steps=[
            "Open the eBay selling flow",
            "Copy the prepared listing fields",
            "Review seller policies, shipping, returns, fees, and listing preview",
            "Submit manually unless a future official API adapter is enabled and proven",
        ],
        blocked_actions=[
            "login",
            "captcha_or_anti_abuse_checks",
            "oauth_token_exchange",
            "fee_confirmation",
            "final_submission",
        ],
        rate_limit_policy=(
            "Assisted jobs are locally rate-limited. Future official API work must obey eBay quota headers."
        ),
    )
    extra_warnings = [
        "eBay can support official API integration later, but this build stays assisted "
        "until OAuth credentials and marketplace policies are configured."
    ]


class TweedehandsAdapter(AssistedPostingAdapter):
    key = "tweedehands"
    name = "Tweedehands"
    posting_url = "https://www.tweedehands.net"
    capabilities = PlatformCapabilities(
        prepared_fields=COMMON_PREPARED_FIELDS,
        account_requirements=[
            "Tweedehands account",
            "Manual session that follows the platform rules",
        ],
        manual_steps=ASSISTED_CAPABILITIES.manual_steps,
        blocked_actions=ASSISTED_CAPABILITIES.blocked_actions + ["scraping_without_user_control"],
        rate_limit_policy=ASSISTED_CAPABILITIES.rate_limit_policy,
    )
    extra_warnings = [
        "Tweedehands import/posting is assisted; use the legacy scraper only in a user-controlled "
        "session that respects site rules."
    ]
