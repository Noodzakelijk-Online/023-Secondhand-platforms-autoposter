"""Add listing details and revision-aware job metadata.

Revision ID: 20260703_0004
Revises: 20260703_0003
Create Date: 2026-07-03
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260703_0004"
down_revision: str | None = "20260703_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    listing_columns = {column["name"] for column in inspector.get_columns("listings")}
    job_columns = {column["name"] for column in inspector.get_columns("publishing_jobs")}

    listing_additions = [
        ("pickup_allowed", sa.Column("pickup_allowed", sa.Boolean(), nullable=False, server_default=sa.true())),
        ("shipping_allowed", sa.Column("shipping_allowed", sa.Boolean(), nullable=False, server_default=sa.false())),
        ("shipping_cost_cents", sa.Column("shipping_cost_cents", sa.Integer(), nullable=False, server_default="0")),
        ("dimensions", sa.Column("dimensions", sa.JSON(), nullable=False, server_default="{}")),
        ("weight_grams", sa.Column("weight_grams", sa.Integer(), nullable=False, server_default="0")),
        ("brand", sa.Column("brand", sa.String(length=120), nullable=False, server_default="")),
        ("model", sa.Column("model", sa.String(length=120), nullable=False, server_default="")),
        ("color", sa.Column("color", sa.String(length=80), nullable=False, server_default="")),
        ("material", sa.Column("material", sa.String(length=120), nullable=False, server_default="")),
        ("notes", sa.Column("notes", sa.Text(), nullable=False, server_default="")),
        ("internal_notes", sa.Column("internal_notes", sa.Text(), nullable=False, server_default="")),
        ("revision", sa.Column("revision", sa.Integer(), nullable=False, server_default="1")),
    ]
    for name, column in listing_additions:
        if name not in listing_columns:
            op.add_column("listings", column)

    job_additions = [
        ("listing_revision", sa.Column("listing_revision", sa.Integer(), nullable=False, server_default="1")),
        ("action_type", sa.Column("action_type", sa.String(length=40), nullable=False, server_default="publish")),
        (
            "operation_mode",
            sa.Column("operation_mode", sa.String(length=40), nullable=False, server_default="assisted"),
        ),
    ]
    for name, column in job_additions:
        if name not in job_columns:
            op.add_column("publishing_jobs", column)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    listing_columns = {column["name"] for column in inspector.get_columns("listings")}
    job_columns = {column["name"] for column in inspector.get_columns("publishing_jobs")}

    for name in ["operation_mode", "action_type", "listing_revision"]:
        if name in job_columns:
            op.drop_column("publishing_jobs", name)

    for name in [
        "revision",
        "internal_notes",
        "notes",
        "material",
        "color",
        "model",
        "brand",
        "weight_grams",
        "dimensions",
        "shipping_cost_cents",
        "shipping_allowed",
        "pickup_allowed",
    ]:
        if name in listing_columns:
            op.drop_column("listings", name)
