import pytest

from app.config import Settings


def test_platform_rate_limit_overrides_are_platform_specific():
    settings = Settings(platform_rate_limit_seconds=60, platform_rate_limit_overrides="marktplaats=120, ebay=300")

    assert settings.platform_rate_limit_for("marktplaats") == 120
    assert settings.platform_rate_limit_for("EBAY") == 300
    assert settings.platform_rate_limit_for("nextdoor") == 60


def test_platform_rate_limit_overrides_reject_invalid_entries():
    settings = Settings(platform_rate_limit_overrides="marktplaats")

    with pytest.raises(ValueError, match="platform=seconds"):
        _ = settings.platform_rate_limit_seconds_by_platform
