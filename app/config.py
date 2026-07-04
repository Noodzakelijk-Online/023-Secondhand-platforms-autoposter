from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.feature_flags import FeatureFlag, build_feature_flags, unsafe_production_feature_flags


class Settings(BaseSettings):
    app_name: str = "Secondhand Platforms Autoposter"
    app_env: str = "development"
    secret_key: str = "change-me-in-production"
    database_url: str = "sqlite:///./data/autoposter.db"
    public_base_url: str = "http://127.0.0.1:8000"
    upload_dir: str = "./data/uploads"
    storage_backend: str = "local"
    max_upload_size_mb: int = 10
    allowed_image_types: str = "image/jpeg,image/png,image/gif,image/webp"
    cors_origins: str = "*"
    log_level: str = "INFO"
    log_format: str = "text"
    dev_auto_login: bool = False
    auth_transport: str = "bearer"
    login_rate_limit_attempts: int = 5
    login_rate_limit_window_seconds: int = 300
    auto_create_tables: bool = True
    job_process_inline: bool = True
    job_worker_poll_seconds: int = 5
    job_worker_batch_size: int = 10
    job_stale_running_seconds: int = 1800
    platform_rate_limit_seconds: int = 60
    platform_rate_limit_overrides: str = ""
    session_expire_hours: int = 168

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def upload_path(self) -> Path:
        return Path(self.upload_dir)

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def allowed_image_type_set(self) -> set[str]:
        return {item.strip().lower() for item in self.allowed_image_types.split(",") if item.strip()}

    @property
    def platform_rate_limit_seconds_by_platform(self) -> dict[str, int]:
        overrides: dict[str, int] = {}
        for raw_item in self.platform_rate_limit_overrides.split(","):
            item = raw_item.strip()
            if not item:
                continue
            if "=" not in item:
                raise ValueError("PLATFORM_RATE_LIMIT_OVERRIDES entries must use platform=seconds")
            platform, raw_seconds = item.split("=", 1)
            platform_key = platform.strip().lower()
            if not platform_key:
                raise ValueError("PLATFORM_RATE_LIMIT_OVERRIDES platform cannot be empty")
            try:
                seconds = int(raw_seconds.strip())
            except ValueError as exc:
                raise ValueError("PLATFORM_RATE_LIMIT_OVERRIDES seconds must be integers") from exc
            if seconds < 0:
                raise ValueError("PLATFORM_RATE_LIMIT_OVERRIDES seconds must be non-negative")
            overrides[platform_key] = seconds
        return overrides

    def platform_rate_limit_for(self, platform: str) -> int:
        return self.platform_rate_limit_seconds_by_platform.get(platform.lower(), self.platform_rate_limit_seconds)

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def feature_flags(self) -> tuple[FeatureFlag, ...]:
        return build_feature_flags(self)


def validate_startup_safety(settings: Settings) -> None:
    if settings.auth_transport.lower() != "bearer":
        raise RuntimeError("Unsupported auth transport: AUTH_TRANSPORT must be bearer")

    if not settings.is_production:
        return

    problems: list[str] = []
    if settings.secret_key in {"", "change-me-in-production"}:
        problems.append("SECRET_KEY must be set to a strong non-default value")
    for flag in unsafe_production_feature_flags(settings):
        problems.append(flag.production_error)
    if settings.cors_origins.strip() == "*":
        problems.append("CORS_ORIGINS must be restricted in production")

    if problems:
        detail = "; ".join(problems)
        raise RuntimeError(f"Unsafe production configuration: {detail}")


@lru_cache
def get_settings() -> Settings:
    return Settings()
