from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ValidationIssue:
    field: str
    message: str


@dataclass
class ValidationOutcome:
    ready: bool
    missing_fields: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    mapped_fields: dict[str, Any] = field(default_factory=dict)


@dataclass
class PublishOutcome:
    status: str
    platform_listing_id: str | None = None
    platform_url: str | None = None
    message: str = ""
    data: dict[str, Any] = field(default_factory=dict)


class PlatformAdapter(ABC):
    key: str
    name: str
    automation_mode: str
    posting_url: str
    official_api_status: str = "not_configured"
    credential_requirements: list[dict[str, str]] = []
    automation_blockers: list[str] = []

    @abstractmethod
    def validate_listing(self, listing, overrides: dict[str, Any] | None = None) -> ValidationOutcome:
        raise NotImplementedError

    @abstractmethod
    def map_listing_to_platform_fields(
        self, listing, overrides: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def publish_listing(self, listing, account=None, overrides: dict[str, Any] | None = None) -> PublishOutcome:
        raise NotImplementedError

    def update_listing(self, listing, platform_listing_id: str) -> PublishOutcome:
        return PublishOutcome(
            status="needs_user_action",
            platform_listing_id=platform_listing_id,
            message="Use the prepared fields to update the listing manually on the platform.",
        )

    def remove_listing(self, platform_listing_id: str) -> PublishOutcome:
        return PublishOutcome(
            status="needs_user_action",
            platform_listing_id=platform_listing_id,
            message="Remove this listing directly on the platform.",
        )

    def get_status(self, platform_listing_id: str) -> PublishOutcome:
        return PublishOutcome(
            status="needs_user_action",
            platform_listing_id=platform_listing_id,
            message="Status cannot be fetched automatically for this assisted integration.",
        )

    @abstractmethod
    def get_required_fields(self) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def get_supported_categories(self) -> list[str]:
        raise NotImplementedError
