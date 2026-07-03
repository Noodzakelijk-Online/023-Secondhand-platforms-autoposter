from app.config import get_settings
from app.database import Base, SessionLocal, engine
from app.demo import DEMO_USER_EMAIL
from app.models import User
from tests.test_api import client


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    get_settings.cache_clear()


def teardown_function():
    get_settings.cache_clear()


def test_dev_auto_login_uses_reserved_demo_identity(monkeypatch):
    monkeypatch.setenv("DEV_AUTO_LOGIN", "true")
    monkeypatch.setenv("APP_ENV", "development")
    get_settings.cache_clear()

    response = client.get("/api/auth/me")

    assert response.status_code == 200, response.text
    assert response.json()["email"] == DEMO_USER_EMAIL
    db = SessionLocal()
    try:
        users = db.query(User).all()
        assert len(users) == 1
        assert users[0].email == DEMO_USER_EMAIL
    finally:
        db.close()


def test_dev_auto_login_is_blocked_outside_development(monkeypatch):
    monkeypatch.setenv("DEV_AUTO_LOGIN", "true")
    monkeypatch.setenv("APP_ENV", "staging")
    get_settings.cache_clear()

    response = client.get("/api/auth/me")

    assert response.status_code == 403
    assert response.json()["error"]["message"] == "Demo auto-login is only allowed in development"
