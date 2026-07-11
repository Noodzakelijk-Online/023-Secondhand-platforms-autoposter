"""Add listing category attributes.

Revision ID: 20260703_0010
Revises: 20260703_0009
Create Date: 2026-07-12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260703_0010"
down_revision: str | None = "20260703_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("listings")}
    if "category_attributes" not in columns:
        op.add_column("listings", sa.Column("category_attributes", sa.JSON(), nullable=True))
        op.execute("UPDATE listings SET category_attributes = '{}' WHERE category_attributes IS NULL")


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("listings")}
    if "category_attributes" in columns:
        op.drop_column("listings", "category_attributes")
