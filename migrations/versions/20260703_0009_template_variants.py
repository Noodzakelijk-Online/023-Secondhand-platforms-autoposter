"""Add template variants.

Revision ID: 20260703_0009
Revises: 20260703_0008
Create Date: 2026-07-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260703_0009"
down_revision: str | None = "20260703_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("listing_templates")}
    if "variant" not in columns:
        op.add_column(
            "listing_templates",
            sa.Column("variant", sa.String(length=80), nullable=False, server_default="default"),
        )
        op.alter_column("listing_templates", "variant", server_default=None)

    index_names = {index["name"] for index in inspector.get_indexes("listing_templates")}
    if "ix_listing_templates_owner_variant" not in index_names:
        op.create_index("ix_listing_templates_owner_variant", "listing_templates", ["owner_id", "variant"])


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    index_names = {index["name"] for index in inspector.get_indexes("listing_templates")}
    if "ix_listing_templates_owner_variant" in index_names:
        op.drop_index("ix_listing_templates_owner_variant", table_name="listing_templates")
    columns = {column["name"] for column in inspector.get_columns("listing_templates")}
    if "variant" in columns:
        op.drop_column("listing_templates", "variant")
