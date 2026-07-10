import secrets
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import PlatformAccount, PlatformOAuthState, User
from app.security import hash_token


def create_ebay_authorization_url(db: Session, user: User, settings: Settings) -> tuple[str, datetime]:
    if not settings.ebay_oauth_configured:
        raise HTTPException(
            status_code=503,
            detail="eBay OAuth is not configured. Set EBAY_OAUTH_CLIENT_ID and EBAY_OAUTH_REDIRECT_URI.",
        )

    state = secrets.token_urlsafe(32)
    expires_at = datetime.now(UTC) + timedelta(seconds=settings.ebay_oauth_state_ttl_seconds)
    db.add(
        PlatformOAuthState(
            user_id=user.id,
            platform="ebay",
            state_hash=hash_token(state),
            redirect_uri=settings.ebay_oauth_redirect_uri,
            scopes=settings.ebay_oauth_scope_list,
            expires_at=expires_at,
        )
    )
    db.commit()
    query = urlencode(
        {
            "client_id": settings.ebay_oauth_client_id,
            "redirect_uri": settings.ebay_oauth_redirect_uri,
            "response_type": "code",
            "scope": " ".join(settings.ebay_oauth_scope_list),
            "state": state,
        }
    )
    return f"{settings.ebay_oauth_authorize_url}?{query}", expires_at


def consume_ebay_authorization_callback(
    db: Session,
    state: str,
    code: str,
    settings: Settings,
) -> PlatformAccount:
    if not state or not code:
        raise HTTPException(status_code=400, detail="Missing eBay OAuth state or authorization code")

    oauth_state = (
        db.query(PlatformOAuthState)
        .filter(
            PlatformOAuthState.platform == "ebay",
            PlatformOAuthState.state_hash == hash_token(state),
        )
        .one_or_none()
    )
    if not oauth_state:
        raise HTTPException(status_code=400, detail="Invalid eBay OAuth state")
    if oauth_state.consumed_at is not None:
        raise HTTPException(status_code=400, detail="eBay OAuth state has already been used")

    expires_at = oauth_state.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at < datetime.now(UTC):
        raise HTTPException(status_code=400, detail="eBay OAuth state has expired")

    oauth_state.consumed_at = datetime.now(UTC)
    secret_ref = f"{settings.ebay_token_secret_ref_prefix}/user-{oauth_state.user_id}"
    account = (
        db.query(PlatformAccount)
        .filter(
            PlatformAccount.owner_id == oauth_state.user_id,
            PlatformAccount.platform == "ebay",
            PlatformAccount.display_name == "eBay official API",
        )
        .one_or_none()
    )
    connection_data = {
        "oauth": {
            "environment": settings.ebay_oauth_environment.lower(),
            "redirect_uri": oauth_state.redirect_uri,
            "scopes": oauth_state.scopes,
            "authorization_code_received": True,
            "token_exchange": "pending_secret_manager",
            "authorized_at": oauth_state.consumed_at.isoformat(),
        }
    }
    if account:
        account.mode = "official_api"
        account.status = "needs_token_exchange"
        account.connection_data = connection_data
        account.secret_ref = secret_ref
    else:
        account = PlatformAccount(
            owner_id=oauth_state.user_id,
            platform="ebay",
            display_name="eBay official API",
            mode="official_api",
            status="needs_token_exchange",
            connection_data=connection_data,
            secret_ref=secret_ref,
        )
        db.add(account)
    db.commit()
    db.refresh(account)
    return account
