from urllib.parse import parse_qs, urlparse

from app.config import get_settings
from app.database import Base, SessionLocal, engine
from app.models import PlatformAccount, PlatformOAuthState
from tests.test_api import auth_headers, client


def setup_function():
    get_settings.cache_clear()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def teardown_function():
    get_settings.cache_clear()


def configure_ebay_oauth(monkeypatch):
    monkeypatch.setenv("EBAY_OAUTH_CLIENT_ID", "sandbox-client-id")
    monkeypatch.setenv("EBAY_OAUTH_REDIRECT_URI", "https://app.example.com/api/accounts/ebay/oauth/callback")
    monkeypatch.setenv("EBAY_OAUTH_ENVIRONMENT", "sandbox")
    monkeypatch.setenv("EBAY_TOKEN_SECRET_REF_PREFIX", "vault://platform-tokens/ebay")
    get_settings.cache_clear()


def test_ebay_oauth_start_fails_closed_without_config():
    headers = auth_headers()

    response = client.post("/api/accounts/ebay/oauth/start", headers=headers)

    assert response.status_code == 503
    assert "not configured" in response.json()["error"]["message"]


def test_ebay_oauth_start_creates_hashed_state_and_authorization_url(monkeypatch):
    configure_ebay_oauth(monkeypatch)
    headers = auth_headers()

    response = client.post("/api/accounts/ebay/oauth/start", headers=headers)

    assert response.status_code == 200, response.text
    payload = response.json()
    parsed = urlparse(payload["authorization_url"])
    query = parse_qs(parsed.query)
    assert parsed.netloc == "auth.sandbox.ebay.com"
    assert query["client_id"] == ["sandbox-client-id"]
    assert query["redirect_uri"] == ["https://app.example.com/api/accounts/ebay/oauth/callback"]
    assert query["response_type"] == ["code"]
    assert "https://api.ebay.com/oauth/api_scope/sell.inventory" in query["scope"][0]
    assert query["state"][0]

    db = SessionLocal()
    try:
        oauth_state = db.query(PlatformOAuthState).one()
        assert oauth_state.platform == "ebay"
        assert oauth_state.state_hash != query["state"][0]
        assert oauth_state.redirect_uri == "https://app.example.com/api/accounts/ebay/oauth/callback"
    finally:
        db.close()


def test_ebay_oauth_callback_consumes_state_without_storing_tokens(monkeypatch):
    configure_ebay_oauth(monkeypatch)
    headers = auth_headers()
    start_response = client.post("/api/accounts/ebay/oauth/start", headers=headers)
    state = parse_qs(urlparse(start_response.json()["authorization_url"]).query)["state"][0]

    callback_response = client.get(
        "/api/accounts/ebay/oauth/callback",
        params={"state": state, "code": "authorization-code-from-ebay"},
    )

    assert callback_response.status_code == 200, callback_response.text
    account = callback_response.json()
    assert account["platform"] == "ebay"
    assert account["display_name"] == "eBay official API"
    assert account["mode"] == "official_api"
    assert account["status"] == "needs_token_exchange"
    assert "secret_ref" not in account
    assert "authorization-code-from-ebay" not in str(account)
    assert account["connection_data"]["oauth"]["token_exchange"] == "pending_secret_manager"

    db = SessionLocal()
    try:
        oauth_state = db.query(PlatformOAuthState).one()
        assert oauth_state.consumed_at is not None
        stored_account = db.query(PlatformAccount).one()
        assert stored_account.secret_ref == "vault://platform-tokens/ebay/user-1"
        assert "authorization-code-from-ebay" not in str(stored_account.connection_data)
    finally:
        db.close()

    replay_response = client.get(
        "/api/accounts/ebay/oauth/callback",
        params={"state": state, "code": "second-code"},
    )
    assert replay_response.status_code == 400
    assert "already been used" in replay_response.json()["error"]["message"]


def test_ebay_oauth_callback_rejects_invalid_state(monkeypatch):
    configure_ebay_oauth(monkeypatch)

    response = client.get(
        "/api/accounts/ebay/oauth/callback",
        params={"state": "unknown", "code": "authorization-code-from-ebay"},
    )

    assert response.status_code == 400
    assert "Invalid eBay OAuth state" in response.json()["error"]["message"]
