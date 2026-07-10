"""Add platform OAuth state tracking.

Revision ID: 20260703_0008
Revises: 20260703_0007
Create Date: 2026-07-03
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260703_0008"
down_revision: str | None = "20260703_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "platform_oauth_states" not in inspector.get_table_names():
        op.create_table(
            "platform_oauth_states",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("platform", sa.String(length=80), nullable=False),
            sa.Column("state_hash", sa.String(length=64), nullable=False),
            sa.Column("redirect_uri", sa.String(length=500), nullable=False),
            sa.Column("scopes", sa.JSON(), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("state_hash"),
        )

    index_names = {index["name"] for index in inspector.get_indexes("platform_oauth_states")}
    indexes = [
        ("ix_platform_oauth_states_platform", ["platform"]),
        ("ix_platform_oauth_states_state_hash", ["state_hash"]),
        ("ix_platform_oauth_states_expires_at", ["expires_at"]),
        (
            "ix_platform_oauth_states_user_platform_created_at",
            ["user_id", "platform", "created_at"],
        ),
    ]
    for index_name, columns in indexes:
        if index_name not in index_names:
            op.create_index(index_name, "platform_oauth_states", columns)


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "platform_oauth_states" not in inspector.get_table_names():
        return
    index_names = {index["name"] for index in inspector.get_indexes("platform_oauth_states")}
    for index_name in [
        "ix_platform_oauth_states_user_platform_created_at",
        "ix_platform_oauth_states_expires_at",
        "ix_platform_oauth_states_state_hash",
        "ix_platform_oauth_states_platform",
    ]:
        if index_name in index_names:
            op.drop_index(index_name, table_name="platform_oauth_states")
    op.drop_table("platform_oauth_states")
