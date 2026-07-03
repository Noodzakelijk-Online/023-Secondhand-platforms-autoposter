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
