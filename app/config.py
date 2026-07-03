from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


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
    dev_auto_login: bool = False
    auto_create_tables: bool = True
    job_process_inline: bool = True
    platform_rate_limit_seconds: int = 60
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
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


def validate_startup_safety(settings: Settings) -> None:
    if not settings.is_production:
        return

    problems: list[str] = []
    if settings.secret_key in {"", "change-me-in-production"}:
        problems.append("SECRET_KEY must be set to a strong non-default value")
    if settings.dev_auto_login:
        problems.append("DEV_AUTO_LOGIN must be false in production")
    if settings.auto_create_tables:
        problems.append("AUTO_CREATE_TABLES must be false in production; run Alembic migrations explicitly")
    if settings.cors_origins.strip() == "*":
        problems.append("CORS_ORIGINS must be restricted in production")

    if problems:
        detail = "; ".join(problems)
        raise RuntimeError(f"Unsafe production configuration: {detail}")


@lru_cache
def get_settings() -> Settings:
    return Settings()
