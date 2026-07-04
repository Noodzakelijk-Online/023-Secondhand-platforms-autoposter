from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

LISTING_CONDITIONS = frozenset({"new", "as_new", "good", "used", "fair", "damaged", "for_parts", "other"})
LISTING_STATUSES = frozenset({"draft", "ready", "published", "archived"})


def _non_negative(value: int | None) -> int | None:
    if value is not None and value < 0:
        raise ValueError("must be greater than or equal to 0")
    return value


def _normalize_currency(value: str | None) -> str | None:
    if value is None:
        return value
    normalized = value.strip().upper()
    if len(normalized) != 3 or not normalized.isalpha():
        raise ValueError("currency must be a 3-letter ISO code")
    return normalized


def _normalize_choice(value: str | None, allowed: frozenset[str], field_name: str) -> str | None:
    if value is None:
        return value
    normalized = value.strip().lower()
    if normalized not in allowed:
        allowed_values = ", ".join(sorted(allowed))
        raise ValueError(f"{field_name} must be one of: {allowed_values}")
    return normalized


def _normalize_tags(value: list[str] | None) -> list[str] | None:
    if value is None:
        return value
    normalized: list[str] = []
    seen = set()
    for raw_tag in value:
        tag = raw_tag.strip()
        if not tag:
            continue
        key = tag.casefold()
        if key not in seen:
            seen.add(key)
            normalized.append(tag)
    if len(normalized) > 20:
        raise ValueError("tags cannot contain more than 20 values")
    long_tags = [tag for tag in normalized if len(tag) > 40]
    if long_tags:
        raise ValueError("tags cannot be longer than 40 characters")
    return normalized


class AuthRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str = ""


class AuthLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    name: str


class AuthToken(BaseModel):
    token: str
    user: UserOut


class ListingBase(BaseModel):
    title: str = ""
    description: str = ""
    price_cents: int = 0
    currency: str = "EUR"
    condition: str = "used"
    category: str = ""
    location: str = ""
    delivery_options: dict[str, Any] = Field(default_factory=dict)
    pickup_allowed: bool = True
    shipping_allowed: bool = False
    shipping_cost_cents: int = 0
    dimensions: dict[str, Any] = Field(default_factory=dict)
    weight_grams: int = 0
    brand: str = ""
    model: str = ""
    color: str = ""
    material: str = ""
    notes: str = ""
    internal_notes: str = ""
    tags: list[str] = Field(default_factory=list)
    status: str = "draft"

    @field_validator("price_cents", "shipping_cost_cents", "weight_grams")
    @classmethod
    def validate_non_negative_numbers(cls, value: int) -> int:
        return _non_negative(value) or 0

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value: str) -> str:
        return _normalize_currency(value) or "EUR"

    @field_validator("condition")
    @classmethod
    def validate_condition(cls, value: str) -> str:
        return _normalize_choice(value, LISTING_CONDITIONS, "condition") or "used"

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        return _normalize_choice(value, LISTING_STATUSES, "status") or "draft"

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, value: list[str]) -> list[str]:
        return _normalize_tags(value) or []


class ListingCreate(ListingBase):
    pass


class ListingUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    price_cents: int | None = None
    currency: str | None = None
    condition: str | None = None
    category: str | None = None
    location: str | None = None
    delivery_options: dict[str, Any] | None = None
    pickup_allowed: bool | None = None
    shipping_allowed: bool | None = None
    shipping_cost_cents: int | None = None
    dimensions: dict[str, Any] | None = None
    weight_grams: int | None = None
    brand: str | None = None
    model: str | None = None
    color: str | None = None
    material: str | None = None
    notes: str | None = None
    internal_notes: str | None = None
    tags: list[str] | None = None
    status: str | None = None

    @field_validator("price_cents", "shipping_cost_cents", "weight_grams")
    @classmethod
    def validate_non_negative_numbers(cls, value: int | None) -> int | None:
        return _non_negative(value)

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value: str | None) -> str | None:
        return _normalize_currency(value)

    @field_validator("condition")
    @classmethod
    def validate_condition(cls, value: str | None) -> str | None:
        return _normalize_choice(value, LISTING_CONDITIONS, "condition")

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        return _normalize_choice(value, LISTING_STATUSES, "status")

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, value: list[str] | None) -> list[str] | None:
        return _normalize_tags(value)


class ListingImageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    storage_path: str
    content_type: str
    file_size: int
    checksum_sha256: str
    position: int
    created_at: datetime


class PlatformMappingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    platform: str
    platform_listing_id: str | None
    status: str
    platform_url: str | None
    overrides: dict[str, Any]
    validation_errors: list[Any]
    last_published_at: datetime | None


class ListingOut(ListingBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    revision: int
    created_at: datetime
    updated_at: datetime
    images: list[ListingImageOut] = Field(default_factory=list)
    platform_mappings: list[PlatformMappingOut] = Field(default_factory=list)


class PlatformAccountCreate(BaseModel):
    platform: str
    display_name: str
    mode: str = "assisted"
    status: str = "needs_setup"
    connection_data: dict[str, Any] = Field(default_factory=dict)


class PlatformAccountOut(PlatformAccountCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime


class PlatformOverrideUpdate(BaseModel):
    platform: str
    overrides: dict[str, Any] = Field(default_factory=dict)
    selected: bool = True


class ImageOrderUpdate(BaseModel):
    image_ids: list[int]


class PublishRequest(BaseModel):
    platforms: list[str]
    account_ids: dict[str, int] = Field(default_factory=dict)
    process_now: bool = True


class JobLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    level: str
    message: str
    data: dict[str, Any]
    created_at: datetime


class PublishingJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    listing_id: int
    platform: str
    account_id: int | None
    listing_revision: int
    action_type: str
    operation_mode: str
    status: str
    attempts: int
    max_attempts: int
    scheduled_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    next_retry_at: datetime | None
    error_message: str | None
    result: dict[str, Any]
    logs: list[JobLogOut] = Field(default_factory=list)


class TemplateCreate(BaseModel):
    name: str
    body: str
    platform: str | None = None


class TemplateUpdate(BaseModel):
    name: str | None = None
    body: str | None = None
    platform: str | None = None


class TemplateOut(TemplateCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime


class CategoryMappingCreate(BaseModel):
    source_category: str
    platform: str
    platform_category: str


class CategoryMappingUpdate(BaseModel):
    source_category: str | None = None
    platform: str | None = None
    platform_category: str | None = None


class CategoryMappingOut(CategoryMappingCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime


class ExportListingImage(BaseModel):
    filename: str
    storage_path: str
    content_type: str
    file_size: int
    checksum_sha256: str
    position: int


class ExportPlatformMapping(BaseModel):
    platform: str
    platform_listing_id: str | None = None
    status: str = "draft"
    platform_url: str | None = None
    overrides: dict[str, Any] = Field(default_factory=dict)
    validation_errors: list[Any] = Field(default_factory=list)
    last_published_at: datetime | None = None


class ExportListing(ListingBase):
    revision: int = 1
    images: list[ExportListingImage] = Field(default_factory=list)
    platform_mappings: list[ExportPlatformMapping] = Field(default_factory=list)


class DataExportBundle(BaseModel):
    version: str = "1"
    exported_at: datetime
    user: UserOut
    listings: list[ExportListing] = Field(default_factory=list)
    platform_accounts: list[PlatformAccountCreate] = Field(default_factory=list)
    templates: list[TemplateCreate] = Field(default_factory=list)
    category_mappings: list[CategoryMappingCreate] = Field(default_factory=list)


class ImportPlatformMapping(BaseModel):
    platform: str
    overrides: dict[str, Any] = Field(default_factory=dict)


class ImportListing(ListingCreate):
    platform_mappings: list[ImportPlatformMapping] = Field(default_factory=list)


class DataImportBundle(BaseModel):
    version: str | None = None
    listings: list[ImportListing] = Field(default_factory=list)
    platform_accounts: list[PlatformAccountCreate] = Field(default_factory=list)
    templates: list[TemplateCreate] = Field(default_factory=list)
    category_mappings: list[CategoryMappingCreate] = Field(default_factory=list)


class DataImportResult(BaseModel):
    listings_created: int = 0
    platform_mappings_created: int = 0
    platform_accounts_created: int = 0
    platform_accounts_updated: int = 0
    templates_created: int = 0
    templates_updated: int = 0
    category_mappings_created: int = 0
    category_mappings_updated: int = 0
    skipped: int = 0


class ValidationResult(BaseModel):
    platform: str
    ready: bool
    missing_fields: list[str]
    warnings: list[str] = Field(default_factory=list)
    mapped_fields: dict[str, Any] = Field(default_factory=dict)
