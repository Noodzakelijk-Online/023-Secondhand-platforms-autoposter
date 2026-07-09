"""Add persistent login throttles.

Revision ID: 20260703_0007
Revises: 20260703_0006
Create Date: 2026-07-03
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260703_0007"
down_revision: str | None = "20260703_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "login_throttles" not in inspector.get_table_names():
        op.create_table(
            "login_throttles",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("identifier_hash", sa.String(length=64), nullable=False),
            sa.Column("attempts", sa.Integer(), nullable=False),
            sa.Column("window_started_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("last_failed_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("identifier_hash"),
        )
    index_names = {index["name"] for index in sa.inspect(op.get_bind()).get_indexes("login_throttles")}
    indexes = [
        ("ix_login_throttles_identifier_hash", ["identifier_hash"]),
        ("ix_login_throttles_window_started_at", ["window_started_at"]),
    ]
    for index_name, columns in indexes:
        if index_name not in index_names:
            op.create_index(index_name, "login_throttles", columns)


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "login_throttles" not in inspector.get_table_names():
        return
    index_names = {index["name"] for index in inspector.get_indexes("login_throttles")}
    for index_name in [
        "ix_login_throttles_window_started_at",
        "ix_login_throttles_identifier_hash",
    ]:
        if index_name in index_names:
            op.drop_index(index_name, table_name="login_throttles")
    op.drop_table("login_throttles")
