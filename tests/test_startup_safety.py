import pytest

from app.config import Settings, validate_startup_safety


def test_production_rejects_unsafe_defaults():
    settings = Settings(app_env="production")

    with pytest.raises(RuntimeError) as exc:
        validate_startup_safety(settings)

    message = str(exc.value)
    assert "SECRET_KEY" in message
    assert "AUTO_CREATE_TABLES" in message
    assert "CORS_ORIGINS" in message


def test_production_accepts_safe_startup_configuration():
    settings = Settings(
        app_env="production",
        secret_key="production-secret-with-enough-entropy",
        cors_origins="https://example.com",
        auto_create_tables=False,
        dev_auto_login=False,
    )

    validate_startup_safety(settings)


def test_unsupported_auth_transport_is_rejected():
    settings = Settings(auth_transport="cookie")

    with pytest.raises(RuntimeError) as exc:
        validate_startup_safety(settings)

    assert "AUTH_TRANSPORT must be bearer" in str(exc.value)


def test_supported_runtime_configuration_modes_are_accepted():
    settings = Settings(storage_backend="local", log_format="json", platform_rate_limit_seconds=0)

    validate_startup_safety(settings)


def test_invalid_runtime_configuration_values_are_rejected():
    settings = Settings(
        storage_backend="s3",
        log_format="xml",
        max_upload_size_mb=0,
        login_rate_limit_attempts=0,
        login_rate_limit_window_seconds=0,
        job_worker_poll_seconds=0,
        job_worker_batch_size=0,
        job_stale_running_seconds=-1,
        platform_rate_limit_seconds=-1,
        session_expire_hours=0,
        audit_retention_days=-1,
    )

    with pytest.raises(RuntimeError) as exc:
        validate_startup_safety(settings)

    message = str(exc.value)
    assert "STORAGE_BACKEND must be local" in message
    assert "LOG_FORMAT must be text or json" in message
    assert "MAX_UPLOAD_SIZE_MB must be positive" in message
    assert "LOGIN_RATE_LIMIT_ATTEMPTS must be positive" in message
    assert "LOGIN_RATE_LIMIT_WINDOW_SECONDS must be positive" in message
    assert "JOB_WORKER_POLL_SECONDS must be positive" in message
    assert "JOB_WORKER_BATCH_SIZE must be positive" in message
    assert "JOB_STALE_RUNNING_SECONDS must be non-negative" in message
    assert "PLATFORM_RATE_LIMIT_SECONDS must be non-negative" in message
    assert "SESSION_EXPIRE_HOURS must be positive" in message
    assert "AUDIT_RETENTION_DAYS must be non-negative" in message


def test_feature_flags_are_reported_from_settings():
    settings = Settings(dev_auto_login=True, auto_create_tables=False, job_process_inline=False)

    flags = {flag.name: flag for flag in settings.feature_flags}

    assert flags["dev_auto_login"].enabled is True
    assert flags["dev_auto_login"].production_allowed is False
    assert flags["auto_create_tables"].enabled is False
    assert flags["inline_job_processing"].enabled is False
