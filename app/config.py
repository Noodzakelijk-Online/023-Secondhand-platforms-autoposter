from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Secondhand Platforms Autoposter"
    app_env: str = "development"
    secret_key: str = "change-me-in-production"
    database_url: str = "sqlite:///./data/autoposter.db"
    upload_dir: str = "./data/uploads"
    cors_origins: str = "*"
    dev_auto_login: bool = False
    job_process_inline: bool = True
    platform_rate_limit_seconds: int = 60
    session_expire_hours: int = 168

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def upload_path(self) -> Path:
        return Path(self.upload_dir)


@lru_cache
def get_settings() -> Settings:
    return Settings()
