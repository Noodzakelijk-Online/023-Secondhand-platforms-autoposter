from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field


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


class TemplateOut(TemplateCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime


class ValidationResult(BaseModel):
    platform: str
    ready: bool
    missing_fields: list[str]
    warnings: list[str] = Field(default_factory=list)
    mapped_fields: dict[str, Any] = Field(default_factory=dict)
