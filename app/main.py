from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import router
from app.config import get_settings, validate_startup_safety
from app.database import init_db
from app.middleware import setup_middleware
from app.observability import configure_logging


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level, settings.log_format)
    validate_startup_safety(settings)
    if settings.auto_create_tables:
        init_db()
    settings.upload_path.mkdir(parents=True, exist_ok=True)

    app = FastAPI(title=settings.app_name)
    setup_middleware(app)
    origins = ["*"] if settings.cors_origins == "*" else [item.strip() for item in settings.cors_origins.split(",")]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)

    public_dir = Path(__file__).resolve().parent.parent / "public"
    app.mount("/uploads", StaticFiles(directory=settings.upload_path), name="uploads")
    app.mount("/", StaticFiles(directory=public_dir, html=True), name="public")
    return app


app = create_app()
