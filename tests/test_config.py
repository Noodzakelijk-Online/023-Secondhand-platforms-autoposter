import pytest

from app.config import Settings, validate_startup_safety


def test_platform_rate_limit_overrides_are_platform_specific():
    settings = Settings(platform_rate_limit_seconds=60, platform_rate_limit_overrides="marktplaats=120, ebay=300")

    assert settings.platform_rate_limit_for("marktplaats") == 120
    assert settings.platform_rate_limit_for("EBAY") == 300
    assert settings.platform_rate_limit_for("nextdoor") == 60


def test_platform_rate_limit_overrides_reject_invalid_entries():
    settings = Settings(platform_rate_limit_overrides="marktplaats")

    with pytest.raises(ValueError, match="platform=seconds"):
        _ = settings.platform_rate_limit_seconds_by_platform


def test_ebay_oauth_uses_sandbox_authorize_url_by_default():
    settings = Settings()

    assert settings.ebay_oauth_authorize_url == "https://auth.sandbox.ebay.com/oauth2/authorize"
    assert "https://api.ebay.com/oauth/api_scope/sell.inventory" in settings.ebay_oauth_scope_list


def test_ebay_oauth_production_requires_client_and_redirect_config():
    settings = Settings(
        app_env="development",
        ebay_oauth_environment="production",
        ebay_oauth_client_id="",
        ebay_oauth_redirect_uri="",
    )

    with pytest.raises(RuntimeError, match="EBAY OAuth production mode"):
        validate_startup_safety(settings)


def test_default_locale_must_be_supported():
    settings = Settings(default_locale="nl", supported_locales="en,de")

    with pytest.raises(RuntimeError, match="DEFAULT_LOCALE"):
        validate_startup_safety(settings)


def test_supported_locale_list_is_normalized():
    settings = Settings(supported_locales="en, NL, de")

    assert settings.supported_locale_list == ["en", "nl", "de"]


def test_api_rate_limit_config_must_be_positive():
    settings = Settings(api_rate_limit_requests=0, api_rate_limit_window_seconds=0)

    with pytest.raises(RuntimeError) as exc:
        validate_startup_safety(settings)

    message = str(exc.value)
    assert "API_RATE_LIMIT_REQUESTS must be positive" in message
    assert "API_RATE_LIMIT_WINDOW_SECONDS must be positive" in message
