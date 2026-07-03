from alembic import command
from alembic.config import Config

from app.config import Settings
from app.doctor import run_checks


def migrate(db_path):
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path.as_posix()}")
    command.upgrade(config, "head")


def test_doctor_reports_ok_for_migrated_local_setup(tmp_path):
    db_path = tmp_path / "doctor-ok.db"
    migrate(db_path)
    settings = Settings(
        secret_key="development-secret",
        database_url=f"sqlite:///{db_path.as_posix()}",
        upload_dir=str(tmp_path / "uploads"),
    )

    result = run_checks(settings)

    assert result["status"] == "ok"
    checks = {check["name"]: check for check in result["checks"]}
    assert checks["database"]["status"] == "ok"
    assert checks["migrations"]["status"] == "ok"
    assert checks["upload_directory"]["status"] == "ok"
    assert checks["platform_adapters"]["status"] == "ok"
    assert checks["legacy_import_isolation"]["status"] == "ok"


def test_doctor_warns_when_database_is_not_migrated(tmp_path):
    db_path = tmp_path / "doctor-unmigrated.db"
    settings = Settings(
        secret_key="development-secret",
        database_url=f"sqlite:///{db_path.as_posix()}",
        upload_dir=str(tmp_path / "uploads"),
    )

    result = run_checks(settings)

    assert result["status"] == "warning"
    checks = {check["name"]: check for check in result["checks"]}
    assert checks["database"]["status"] == "ok"
    assert checks["migrations"]["status"] == "warning"


def test_doctor_reports_production_startup_errors(tmp_path):
    db_path = tmp_path / "doctor-prod.db"
    migrate(db_path)
    settings = Settings(
        app_env="production",
        secret_key="change-me-in-production",
        cors_origins="*",
        auto_create_tables=True,
        database_url=f"sqlite:///{db_path.as_posix()}",
        upload_dir=str(tmp_path / "uploads"),
    )

    result = run_checks(settings)

    assert result["status"] == "error"
    checks = {check["name"]: check for check in result["checks"]}
    assert checks["startup_safety"]["status"] == "error"
    assert "SECRET_KEY" in checks["startup_safety"]["message"]
