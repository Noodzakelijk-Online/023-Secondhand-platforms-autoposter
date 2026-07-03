"""Add listing image storage metadata.

Revision ID: 20260703_0002
Revises: 20260703_0001
Create Date: 2026-07-03
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260703_0002"
down_revision: str | None = "20260703_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_columns = {column["name"] for column in inspector.get_columns("listing_images")}

    if "file_size" not in existing_columns:
        op.add_column("listing_images", sa.Column("file_size", sa.Integer(), nullable=False, server_default="0"))
    if "checksum_sha256" not in existing_columns:
        op.add_column(
            "listing_images",
            sa.Column("checksum_sha256", sa.String(length=64), nullable=False, server_default=""),
        )
        op.create_index("ix_listing_images_checksum_sha256", "listing_images", ["checksum_sha256"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_columns = {column["name"] for column in inspector.get_columns("listing_images")}
    existing_indexes = {index["name"] for index in inspector.get_indexes("listing_images")}

    if "ix_listing_images_checksum_sha256" in existing_indexes:
        op.drop_index("ix_listing_images_checksum_sha256", table_name="listing_images")
    if "checksum_sha256" in existing_columns:
        op.drop_column("listing_images", "checksum_sha256")
    if "file_size" in existing_columns:
        op.drop_column("listing_images", "file_size")
