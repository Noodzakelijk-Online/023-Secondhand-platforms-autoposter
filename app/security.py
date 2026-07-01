from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import secrets

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import User, UserSession


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120000)
    return f"pbkdf2_sha256${salt}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, salt, digest = stored_hash.split("$", 2)
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120000).hex()
    return hmac.compare_digest(candidate, digest)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_session(db: Session, user: User) -> str:
    token = secrets.token_urlsafe(32)
    settings = get_settings()
    session = UserSession(
        user_id=user.id,
        token_hash=hash_token(token),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=settings.session_expire_hours),
    )
    db.add(session)
    db.commit()
    return token
