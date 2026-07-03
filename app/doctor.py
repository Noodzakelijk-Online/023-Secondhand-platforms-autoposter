import argparse
import json
import sys
from dataclasses import asdict, dataclass

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text

from app.adapters import list_platforms
from app.config import Settings, get_settings, validate_startup_safety
from app.demo import DEMO_USER_EMAIL, demo_mode_enabled
from app.feature_flags import feature_flag_summary


@dataclass(frozen=True)
class DoctorCheck:
    name: str
    status: str
    message: str
    details: dict


def run_checks(settings: Settings | None = None) -> dict:
    settings = settings or get_settings()
    checks = [
        check_startup_safety(settings),
        check_database(settings),
        check_migrations(settings),
        check_upload_directory(settings),
        check_platform_adapters(),
        check_legacy_import_isolation(),
    ]
    statuses = [check.status for check in checks]
    if "error" in statuses:
        status = "error"
    elif "warning" in statuses:
        status = "warning"
    else:
        status = "ok"
    return {
        "status": status,
        "checks": [asdict(check) for check in checks],
    }


def check_startup_safety(settings: Settings) -> DoctorCheck:
    details = {
        "app_env": settings.app_env,
        "feature_flags": feature_flag_summary(settings),
        "demo_mode": {
            "enabled": demo_mode_enabled(settings),
            "user_email": DEMO_USER_EMAIL if demo_mode_enabled(settings) else None,
        },
    }
    try:
        validate_startup_safety(settings)
    except RuntimeError as exc:
        return DoctorCheck(
            name="startup_safety",
            status="error",
            message=str(exc),
            details=details,
        )
    if not settings.is_production and settings.secret_key == "change-me-in-production":
        return DoctorCheck(
            name="startup_safety",
            status="warning",
            message="Development is using the default SECRET_KEY. Replace it before production.",
            details=details,
        )
    return DoctorCheck(
        name="startup_safety",
        status="ok",
        message="Startup safety checks passed.",
        details=details,
    )


def check_database(settings: Settings) -> DoctorCheck:
    try:
        engine = create_engine(
            settings.database_url,
            connect_args={"check_same_thread": False}
            if settings.database_url.startswith("sqlite")
            else {},
        )
        with engine.connect() as connection:
            connection.execute(text("select 1"))
    except Exception as exc:
        return DoctorCheck(
            name="database",
            status="error",
            message="Database connection failed.",
            details={"error": str(exc), "database_url": redact_database_url(settings.database_url)},
        )
    return DoctorCheck(
        name="database",
        status="ok",
        message="Database connection succeeded.",
        details={"database_url": redact_database_url(settings.database_url)},
    )


def check_migrations(settings: Settings) -> DoctorCheck:
    try:
        config = Config("alembic.ini")
        config.set_main_option("sqlalchemy.url", settings.database_url)
        script = ScriptDirectory.from_config(config)
        head_revision = script.get_current_head()
        engine = create_engine(
            settings.database_url,
            connect_args={"check_same_thread": False}
            if settings.database_url.startswith("sqlite")
            else {},
        )
        with engine.connect() as connection:
            current_revision = MigrationContext.configure(connection).get_current_revision()
    except Exception as exc:
        return DoctorCheck(
            name="migrations",
            status="error",
            message="Migration check failed.",
            details={"error": str(exc)},
        )

    if current_revision != head_revision:
        return DoctorCheck(
            name="migrations",
            status="warning",
            message="Database is not at the latest Alembic revision.",
            details={"current_revision": current_revision, "head_revision": head_revision},
        )
    return DoctorCheck(
        name="migrations",
        status="ok",
        message="Database is at the latest Alembic revision.",
        details={"current_revision": current_revision, "head_revision": head_revision},
    )


def check_upload_directory(settings: Settings) -> DoctorCheck:
    path = settings.upload_path
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".doctor-write-test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
    except Exception as exc:
        return DoctorCheck(
            name="upload_directory",
            status="error",
            message="Upload directory is not writable.",
            details={"path": str(path), "error": str(exc)},
        )
    return DoctorCheck(
        name="upload_directory",
        status="ok",
        message="Upload directory is writable.",
        details={"path": str(path)},
    )


def check_platform_adapters() -> DoctorCheck:
    platforms = list_platforms()
    if not platforms:
        return DoctorCheck(
            name="platform_adapters",
            status="error",
            message="No platform adapters are registered.",
            details={},
        )
    return DoctorCheck(
        name="platform_adapters",
        status="ok",
        message="Platform adapters are registered.",
        details={"platforms": [platform["key"] for platform in platforms]},
    )


def check_legacy_import_isolation() -> DoctorCheck:
    forbidden = ["selenium", "lastpass", "spacy", "decouple"]
    loaded = [module for module in forbidden if module in sys.modules]
    if loaded:
        return DoctorCheck(
            name="legacy_import_isolation",
            status="warning",
            message="Legacy browser automation modules are loaded in the web app process.",
            details={"loaded_modules": loaded},
        )
    return DoctorCheck(
        name="legacy_import_isolation",
        status="ok",
        message="Legacy browser automation modules are not loaded.",
        details={"forbidden_modules": forbidden},
    )


def redact_database_url(database_url: str) -> str:
    if "://" not in database_url or "@" not in database_url:
        return database_url
    scheme, rest = database_url.split("://", 1)
    _, host = rest.rsplit("@", 1)
    return f"{scheme}://***@{host}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Secondhand Autoposter diagnostic checks.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args()
    result = run_checks()
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Doctor status: {result['status']}")
        for check in result["checks"]:
            print(f"- [{check['status']}] {check['name']}: {check['message']}")
    return 1 if result["status"] == "error" else 0


if __name__ == "__main__":
    raise SystemExit(main())
