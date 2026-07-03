"""Add performance indexes for common API and worker queries.

Revision ID: 20260703_0005
Revises: 20260703_0004
Create Date: 2026-07-03
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260703_0005"
down_revision: str | None = "20260703_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


INDEXES = [
    ("ix_user_sessions_user_id", "user_sessions", ["user_id"]),
    ("ix_listings_owner_updated_at", "listings", ["owner_id", "updated_at"]),
    ("ix_listings_owner_status_updated_at", "listings", ["owner_id", "status", "updated_at"]),
    ("ix_listing_images_listing_position", "listing_images", ["listing_id", "position"]),
    (
        "ix_platform_accounts_owner_platform_status",
        "platform_accounts",
        ["owner_id", "platform", "status"],
    ),
    ("ix_platform_accounts_owner_created_at", "platform_accounts", ["owner_id", "created_at"]),
    (
        "ix_category_mappings_owner_platform_source",
        "category_mappings",
        ["owner_id", "platform", "source_category"],
    ),
    ("ix_publishing_jobs_listing_created_at", "publishing_jobs", ["listing_id", "created_at"]),
    (
        "ix_publishing_jobs_listing_platform_status",
        "publishing_jobs",
        ["listing_id", "platform", "status"],
    ),
    ("ix_publishing_jobs_due_queue", "publishing_jobs", ["status", "scheduled_at", "next_retry_at"]),
    ("ix_publishing_job_logs_job_created_at", "publishing_job_logs", ["job_id", "created_at"]),
    ("ix_listing_drafts_listing_created_at", "listing_drafts", ["listing_id", "created_at"]),
    ("ix_listing_templates_owner_platform_name", "listing_templates", ["owner_id", "platform", "name"]),
    ("ix_publication_attempts_job_created_at", "publication_attempts", ["job_id", "created_at"]),
]


def _index_names(table_name: str) -> set[str]:
    return {index["name"] for index in sa.inspect(op.get_bind()).get_indexes(table_name)}


def upgrade() -> None:
    cache: dict[str, set[str]] = {}
    for name, table_name, columns in INDEXES:
        names = cache.setdefault(table_name, _index_names(table_name))
        if name not in names:
            op.create_index(name, table_name, columns)
            names.add(name)


def downgrade() -> None:
    cache: dict[str, set[str]] = {}
    for name, table_name, _columns in reversed(INDEXES):
        names = cache.setdefault(table_name, _index_names(table_name))
        if name in names:
            op.drop_index(name, table_name=table_name)
            names.remove(name)
