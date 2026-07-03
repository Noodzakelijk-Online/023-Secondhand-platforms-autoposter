# Secondhand Platforms Autoposter

A full-stack listing manager for preparing one reusable secondhand product listing and publishing or preparing it across multiple secondhand platforms from one dashboard.

The current production-safe implementation uses assisted-posting adapters for Marktplaats, Koopplein, Nextdoor, eBay, and Tweedehands. It validates listings, stores platform-specific overrides, queues publishing jobs, records logs and attempts, and produces a prepared posting package for the account owner to complete on each platform. It does not bypass login checks, CAPTCHAs, paid placement flows, rate limits, or platform security systems.

## Stack

- FastAPI backend
- SQLAlchemy models
- SQLite by default
- Static HTML/CSS/JavaScript dashboard
- Pytest API tests
- Docker Compose for local deployment

Legacy Selenium scripts remain in the repository as reference/manual tooling, but they are not part of the default web app startup path.

Install `requirements-legacy.txt` only if you need to run the old Selenium scripts in a compatible Python environment.

## Local setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`.

On Linux/macOS, activate with `source .venv/bin/activate` and copy the env file with `cp .env.example .env`.

## Docker

```bash
copy .env.example .env
docker compose up --build
```

The app is available at `http://127.0.0.1:8000`. SQLite data and uploads are stored in `./data`.

## Environment variables

- `SECRET_KEY`: set to a long random value in production.
- `DATABASE_URL`: SQLAlchemy database URL. Default: `sqlite:///./data/autoposter.db`.
- `UPLOAD_DIR`: image upload directory. Default: `./data/uploads`.
- `CORS_ORIGINS`: comma-separated allowed origins or `*` for local development.
- `DEV_AUTO_LOGIN`: creates a demo session for local-only development when `true`.
- `AUTO_CREATE_TABLES`: local development helper. Must be `false` in production.
- `JOB_PROCESS_INLINE`: processes queued jobs in the request for local simplicity.
- `PLATFORM_RATE_LIMIT_SECONDS`: cooldown per platform between job attempts.
- `SESSION_EXPIRE_HOURS`: bearer session lifetime.
- `PUBLIC_BASE_URL`: public URL used for future generated links and diagnostics.
- `LOG_LEVEL`: desired logging verbosity for deployment.

Legacy Selenium variables are documented in `.env.example` and should only be filled locally.

## Database

In development, tables can be created automatically when `AUTO_CREATE_TABLES=true`.

For production, set `AUTO_CREATE_TABLES=false` and run Alembic migrations explicitly:

```bash
alembic upgrade head
```

The schema includes:

- users and user sessions
- listings/products
- listing images
- platform accounts
- platform listing mappings
- category mappings
- publishing jobs
- publishing job logs
- listing drafts
- description templates
- publication attempts

SQLite is the default for quick local development. PostgreSQL is supported through SQLAlchemy by setting `DATABASE_URL`, for example:

```bash
DATABASE_URL=postgresql+psycopg://autoposter:autoposter@postgres:5432/autoposter
docker compose --profile postgres up --build
```

## Running tests

```bash
pytest
```

The test suite uses an isolated temporary SQLite database and validates the core create-listing-to-publish-job flow, adapter validation, auth, and image upload.

## Platform support

| Platform | Mode | Notes |
| --- | --- | --- |
| Marktplaats | Assisted | Prepares mapped fields. User completes login, verification, category/payment choices, and final submission. |
| Koopplein | Assisted | Prepares fields and tracks status. User confirms final post manually. |
| Nextdoor | Assisted | Keeps neighborhood/account confirmations user-controlled. |
| eBay | Assisted | Ready for future official API/OAuth integration; no credential-dependent automation is enabled by default. |
| Tweedehands | Assisted | Legacy import/posting scripts are separate and must be run only in compliant user-controlled sessions. |

## Adding a platform adapter

1. Add a class implementing `PlatformAdapter` in `app/adapters/`.
2. Implement `validate_listing`, `map_listing_to_platform_fields`, `publish_listing`, `get_required_fields`, and `get_supported_categories`.
3. Register it in `app/adapters/registry.py`.
4. Add adapter tests with mocked external behavior.
5. Document the automation mode and compliance limits here.

## API highlights

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/listings`
- `POST /api/listings`
- `PATCH /api/listings/{id}`
- `POST /api/listings/{id}/images`
- `GET /api/listings/{id}/validate`
- `POST /api/listings/{id}/publish`
- `GET /api/jobs`
- `POST /api/jobs/{id}/retry`
- `GET /api/platforms`
- `POST /api/accounts`
- `POST /api/templates`

Interactive API docs are available at `http://127.0.0.1:8000/docs`.

List endpoints support bounded pagination with `limit` and `offset`. Core list endpoints also expose focused filtering/sorting parameters, such as `/api/listings?search=chair&status=draft&sort=-updated_at`.

API errors use a consistent envelope:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request contains invalid fields.",
    "details": {},
    "field_errors": {},
    "retryable": false,
    "request_id": "..."
  }
}
```

Every response includes `X-Request-ID`; callers may provide their own `X-Request-ID` header for traceability.

## Security and compliance

- No raw platform passwords are stored by the web app.
- External calls are isolated behind adapter interfaces.
- The default integrations are assisted-only where official automation credentials are absent.
- Jobs are idempotent per listing/platform and include platform cooldowns.
- Use official APIs when converting an assisted adapter into a fully automated adapter.
- Do not bypass CAPTCHAs, anti-bot protections, login protections, payment prompts, or platform rate limits.

## Project phase documentation

- Product definition: `docs/PRODUCT_DEFINITION.md`
- Platform reality review: `docs/PLATFORM_REALITY_REVIEW.md`
- Legacy script quarantine: `docs/LEGACY_SCRIPT_QUARANTINE.md`
- Rate limits: `docs/RATE_LIMITS.md`
- Completion matrix: `docs/COMPLETION_MATRIX.md`

## Production notes

- Set a strong `SECRET_KEY`.
- Use a managed database by changing `DATABASE_URL`.
- Place uploads on persistent storage.
- Put the app behind HTTPS.
- Restrict `CORS_ORIGINS`.
- Run Alembic migrations before production startup.
- Configure platform OAuth/API credentials only through environment variables or a proper secret manager.
- Keep the security headers middleware enabled. HTTPS deployments also receive HSTS.
