from __future__ import annotations

from sqlalchemy.orm import Session

from app.config import Settings
from app.models import User
from app.security import hash_password

DEMO_USER_EMAIL = "demo@local.autoposter.invalid"
DEMO_USER_NAME = "Local Demo User"


def demo_mode_enabled(settings: Settings) -> bool:
    return settings.dev_auto_login and settings.app_env.lower() == "development"


def ensure_demo_user(db: Session) -> User:
    user = db.query(User).filter(User.email == DEMO_USER_EMAIL).one_or_none()
    if user:
        return user
    user = User(
        email=DEMO_USER_EMAIL,
        name=DEMO_USER_NAME,
        password_hash=hash_password("development-only-demo-user"),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
