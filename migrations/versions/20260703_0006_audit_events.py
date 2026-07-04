"""Add privacy audit events.

Revision ID: 20260703_0006
Revises: 20260703_0005
Create Date: 2026-07-03
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260703_0006"
down_revision: str | None = "20260703_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "audit_events" not in inspector.get_table_names():
        op.create_table(
            "audit_events",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=True),
            sa.Column("user_email_hash", sa.String(length=64), nullable=False),
            sa.Column("action", sa.String(length=80), nullable=False),
            sa.Column("event_data", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
    index_names = {index["name"] for index in sa.inspect(op.get_bind()).get_indexes("audit_events")}
    indexes = [
        ("ix_audit_events_user_id", ["user_id"]),
        ("ix_audit_events_user_email_hash", ["user_email_hash"]),
        ("ix_audit_events_action", ["action"]),
        ("ix_audit_events_user_created_at", ["user_id", "created_at"]),
        ("ix_audit_events_action_created_at", ["action", "created_at"]),
    ]
    for index_name, columns in indexes:
        if index_name not in index_names:
            op.create_index(index_name, "audit_events", columns)


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "audit_events" not in inspector.get_table_names():
        return
    index_names = {index["name"] for index in inspector.get_indexes("audit_events")}
    for index_name in [
        "ix_audit_events_action_created_at",
        "ix_audit_events_user_created_at",
        "ix_audit_events_action",
        "ix_audit_events_user_email_hash",
        "ix_audit_events_user_id",
    ]:
        if index_name in index_names:
            op.drop_index(index_name, table_name="audit_events")
    op.drop_table("audit_events")
