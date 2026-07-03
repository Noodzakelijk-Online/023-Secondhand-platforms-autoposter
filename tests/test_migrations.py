from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


def test_alembic_migration_runs_from_empty_database(tmp_path):
    db_path = tmp_path / "migration-test.db"
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path.as_posix()}")

    command.upgrade(config, "head")

    engine = create_engine(f"sqlite:///{db_path.as_posix()}")
    tables = set(inspect(engine).get_table_names())

    assert "alembic_version" in tables
    assert "users" in tables
    assert "listings" in tables
    assert "listing_images" in tables
    assert "publishing_jobs" in tables
    assert "publishing_job_logs" in tables
    assert "audit_events" in tables
    image_columns = {column["name"] for column in inspect(engine).get_columns("listing_images")}
    assert "file_size" in image_columns
    assert "checksum_sha256" in image_columns
    session_columns = {column["name"] for column in inspect(engine).get_columns("user_sessions")}
    assert "revoked_at" in session_columns
    listing_columns = {column["name"] for column in inspect(engine).get_columns("listings")}
    assert "revision" in listing_columns
    assert "pickup_allowed" in listing_columns
    assert "shipping_cost_cents" in listing_columns
    assert "brand" in listing_columns
    assert "internal_notes" in listing_columns
    job_columns = {column["name"] for column in inspect(engine).get_columns("publishing_jobs")}
    assert "listing_revision" in job_columns
    assert "action_type" in job_columns
    assert "operation_mode" in job_columns
    listing_indexes = {index["name"] for index in inspect(engine).get_indexes("listings")}
    assert "ix_listings_owner_updated_at" in listing_indexes
    job_indexes = {index["name"] for index in inspect(engine).get_indexes("publishing_jobs")}
    assert "ix_publishing_jobs_due_queue" in job_indexes
    assert "ix_publishing_jobs_listing_platform_status" in job_indexes
    audit_columns = {column["name"] for column in inspect(engine).get_columns("audit_events")}
    assert "owner_id" in audit_columns
    assert "event_type" in audit_columns
    assert "resource_type" in audit_columns
    assert "details" in audit_columns
