from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, onupdate=now_utc
    )


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120), default="")
    password_hash: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    sessions: Mapped[list["UserSession"]] = relationship(
        cascade="all, delete-orphan", back_populates="user"
    )
    listings: Mapped[list["Listing"]] = relationship(back_populates="owner")


class UserSession(Base):
    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    user: Mapped[User] = relationship(back_populates="sessions")


class Listing(Base, TimestampMixin):
    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(160), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    price_cents: Mapped[int] = mapped_column(Integer, default=0)
    currency: Mapped[str] = mapped_column(String(3), default="EUR")
    condition: Mapped[str] = mapped_column(String(40), default="used")
    category: Mapped[str] = mapped_column(String(120), default="")
    location: Mapped[str] = mapped_column(String(160), default="")
    delivery_options: Mapped[dict] = mapped_column(JSON, default=dict)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(40), default="draft")

    owner: Mapped[User] = relationship(back_populates="listings")
    images: Mapped[list["ListingImage"]] = relationship(
        cascade="all, delete-orphan", back_populates="listing", order_by="ListingImage.position"
    )
    platform_mappings: Mapped[list["PlatformListingMapping"]] = relationship(
        cascade="all, delete-orphan", back_populates="listing"
    )
    jobs: Mapped[list["PublishingJob"]] = relationship(back_populates="listing")
    drafts: Mapped[list["ListingDraft"]] = relationship(
        cascade="all, delete-orphan", back_populates="listing"
    )


class ListingImage(Base, TimestampMixin):
    __tablename__ = "listing_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id", ondelete="CASCADE"))
    filename: Mapped[str] = mapped_column(String(255))
    storage_path: Mapped[str] = mapped_column(String(500))
    content_type: Mapped[str] = mapped_column(String(120), default="application/octet-stream")
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    checksum_sha256: Mapped[str] = mapped_column(String(64), default="", index=True)
    position: Mapped[int] = mapped_column(Integer, default=0)

    listing: Mapped[Listing] = relationship(back_populates="images")


class PlatformAccount(Base, TimestampMixin):
    __tablename__ = "platform_accounts"
    __table_args__ = (UniqueConstraint("owner_id", "platform", "display_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    platform: Mapped[str] = mapped_column(String(80), index=True)
    display_name: Mapped[str] = mapped_column(String(120))
    mode: Mapped[str] = mapped_column(String(40), default="assisted")
    status: Mapped[str] = mapped_column(String(40), default="needs_setup")
    connection_data: Mapped[dict] = mapped_column(JSON, default=dict)
    secret_ref: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)


class PlatformListingMapping(Base, TimestampMixin):
    __tablename__ = "platform_listing_mappings"
    __table_args__ = (UniqueConstraint("listing_id", "platform"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id", ondelete="CASCADE"))
    platform: Mapped[str] = mapped_column(String(80), index=True)
    platform_listing_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="draft")
    platform_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    overrides: Mapped[dict] = mapped_column(JSON, default=dict)
    validation_errors: Mapped[list] = mapped_column(JSON, default=list)
    last_published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    listing: Mapped[Listing] = relationship(back_populates="platform_mappings")


class CategoryMapping(Base, TimestampMixin):
    __tablename__ = "category_mappings"
    __table_args__ = (UniqueConstraint("owner_id", "source_category", "platform"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    source_category: Mapped[str] = mapped_column(String(120))
    platform: Mapped[str] = mapped_column(String(80))
    platform_category: Mapped[str] = mapped_column(String(120))


class PublishingJob(Base, TimestampMixin):
    __tablename__ = "publishing_jobs"
    __table_args__ = (UniqueConstraint("idempotency_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id", ondelete="CASCADE"))
    platform: Mapped[str] = mapped_column(String(80), index=True)
    account_id: Mapped[Optional[int]] = mapped_column(ForeignKey("platform_accounts.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="queued", index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    idempotency_key: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    next_retry_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    result: Mapped[dict] = mapped_column(JSON, default=dict)

    listing: Mapped[Listing] = relationship(back_populates="jobs")
    logs: Mapped[list["PublishingJobLog"]] = relationship(
        cascade="all, delete-orphan", back_populates="job", order_by="PublishingJobLog.created_at"
    )


class PublishingJobLog(Base):
    __tablename__ = "publishing_job_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("publishing_jobs.id", ondelete="CASCADE"))
    level: Mapped[str] = mapped_column(String(20), default="info")
    message: Mapped[str] = mapped_column(Text)
    data: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    job: Mapped[PublishingJob] = relationship(back_populates="logs")


class ListingDraft(Base, TimestampMixin):
    __tablename__ = "listing_drafts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id", ondelete="CASCADE"))
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    source: Mapped[str] = mapped_column(String(40), default="manual")

    listing: Mapped[Listing] = relationship(back_populates="drafts")


class ListingTemplate(Base, TimestampMixin):
    __tablename__ = "listing_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(120))
    platform: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    body: Mapped[str] = mapped_column(Text)


class PublicationAttempt(Base):
    __tablename__ = "publication_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("publishing_jobs.id", ondelete="CASCADE"))
    platform: Mapped[str] = mapped_column(String(80), index=True)
    status: Mapped[str] = mapped_column(String(40))
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    payload_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
