# Official API Real Credential Checklist

This checklist must be completed before any platform adapter is switched from `assisted` mode to `official_api` mode.

The current app does not use real marketplace API credentials. Every exposed platform remains assisted unless this checklist is satisfied for that specific platform and environment.

## Non-Negotiable Rules

- Use official platform APIs only. Do not automate browser flows, CAPTCHA steps, login protections, paid placement prompts, or anti-abuse controls.
- Keep sandbox and production credentials separate.
- Store secrets only in environment variables or a proper secret manager. Do not store raw platform passwords, OAuth client secrets, refresh tokens, cookies, or browser profiles in the database, repository, logs, exports, or screenshots.
- A job may be marked `published` only after the official API returns a durable success response for the listing, or after a separate user-confirmed manual flow records the platform URL.
- If a platform account is missing credentials, expired authorization, seller policy setup, billing setup, required scopes, or required webhook verification, the adapter must return `needs_user_action`.

## Platform Credential Intake

For each platform, record:

- Platform name and account owner.
- Official developer application name.
- Sandbox client ID and secret reference.
- Production client ID and secret reference.
- OAuth redirect URL or callback URL.
- Required API scopes.
- Token lifetime, refresh behavior, and revocation behavior.
- Seller account prerequisites, such as business verification, payment policy, return policy, shipping policy, tax settings, or regional marketplace enrollment.
- Rate-limit, quota, retry, and daily cap rules from the platform documentation.
- Webhook or notification setup, if required for listing lifecycle events.
- Support contact and developer dashboard URL.

## eBay Readiness Checklist

Before enabling any eBay `official_api` adapter:

- Create an eBay developer application for sandbox and production.
- Configure OAuth redirect URLs for the deployed app environment.
- Set `EBAY_OAUTH_CLIENT_ID`, `EBAY_OAUTH_REDIRECT_URI`, `EBAY_OAUTH_ENVIRONMENT`, and `EBAY_OAUTH_SCOPES` for the target environment.
- Confirm the seller account has listing privileges in the target marketplace.
- Confirm required seller policies exist for payment, fulfillment, returns, and location.
- Verify listing category, condition, item specifics, image requirements, shipping details, and marketplace currency rules against eBay documentation.
- Prove sandbox token exchange and token refresh without storing raw secrets in app tables.
- Prove sandbox listing draft/create flow with a test item.
- Prove API error handling for invalid category, missing specifics, expired token, quota limit, duplicate request, and seller policy failure.
- Add tests that use fake local API responses only for automated CI and require explicit operator action for real sandbox credentials.
- Add a production cutover note that names the exact environment variables or secret-manager entries required.

## eBay OAuth Foundation In This Repository

The app now includes a guarded OAuth consent foundation:

- `POST /api/accounts/ebay/oauth/start` requires an authenticated app user and returns an eBay consent URL.
- OAuth `state` is stored only as a SHA-256 hash in `platform_oauth_states`, expires according to `EBAY_OAUTH_STATE_TTL_SECONDS`, and can be consumed once.
- `GET /api/accounts/ebay/oauth/callback` validates state and records an eBay platform account as `mode=official_api` and `status=needs_token_exchange`.
- The callback does not store raw authorization codes, access tokens, refresh tokens, client secrets, or token payloads in app tables.
- `PlatformAccount.secret_ref` records the expected secret-manager location prefix from `EBAY_TOKEN_SECRET_REF_PREFIX`; it is not exposed in API responses or data exports.

This is not a complete eBay API integration. The next production-hardening slice must exchange the authorization code through a secret-manager-backed token service, persist only external secret references, refresh tokens safely, and prove sandbox Inventory API behavior before any adapter can mark jobs as published.

## Adapter Activation Gate

An adapter can expose `official_api` mode only when all of these are true:

- Credential configuration validates at startup or through `python -m app.doctor`.
- Missing or invalid credentials fail closed to assisted mode or `needs_user_action`.
- Tokens are encrypted or stored outside the application database.
- API calls use idempotency keys or platform-supported duplicate prevention where available.
- Platform-specific rate limits are enforced and logged.
- The adapter records request intent and response summaries without logging secrets or full personal data.
- Tests cover success, retryable failure, permanent validation failure, expired authorization, and duplicate prevention.
- The README and platform reality review clearly state what is automated and what remains user-controlled.

## Production Evidence To Capture

Keep these artifacts outside the public repository if they contain account details:

- Screenshot or export of developer app configuration with secrets redacted.
- Sandbox OAuth authorization proof with token values redacted.
- Sandbox listing creation proof with test listing ID.
- Rate-limit and quota notes with date checked.
- Security review confirming no secrets appear in logs, exports, backups, or diagnostics.
- Rollback plan for disabling official API mode per platform.

## Current Repository Status

- Marktplaats: assisted only.
- Koopplein: assisted only.
- Nextdoor: assisted only.
- eBay: assisted by default; OAuth consent foundation exists, but token exchange and official publishing are not implemented.
- Tweedehands: assisted only.

No platform should be represented to a client as fully API-automated until its checklist is complete and committed with tests, documentation, and operator runbook updates.
