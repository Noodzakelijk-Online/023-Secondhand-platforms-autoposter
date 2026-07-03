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
    image_columns = {column["name"] for column in inspect(engine).get_columns("listing_images")}
    assert "file_size" in image_columns
    assert "checksum_sha256" in image_columns
    session_columns = {column["name"] for column in inspect(engine).get_columns("user_sessions")}
    assert "revoked_at" in session_columns
