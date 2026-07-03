"""Add session revocation timestamp.

Revision ID: 20260703_0003
Revises: 20260703_0002
Create Date: 2026-07-03
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260703_0003"
down_revision: str | None = "20260703_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_columns = {column["name"] for column in inspector.get_columns("user_sessions")}
    if "revoked_at" not in existing_columns:
        op.add_column("user_sessions", sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_columns = {column["name"] for column in inspector.get_columns("user_sessions")}
    if "revoked_at" in existing_columns:
        op.drop_column("user_sessions", "revoked_at")
