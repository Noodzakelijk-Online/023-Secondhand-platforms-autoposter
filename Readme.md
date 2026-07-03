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

The Compose stack also starts a worker service that runs queued publishing jobs:

```bash
python -m app.worker
```

For local development, `JOB_PROCESS_INLINE=true` keeps publish jobs immediately processed in the API request. For production-style operation, set `JOB_PROCESS_INLINE=false` and run the worker process.

## Environment variables

- `SECRET_KEY`: set to a long random value in production.
- `DATABASE_URL`: SQLAlchemy database URL. Default: `sqlite:///./data/autoposter.db`.
- `UPLOAD_DIR`: image upload directory. Default: `./data/uploads`.
- `STORAGE_BACKEND`: storage adapter. Current supported value: `local`.
- `MAX_UPLOAD_SIZE_MB`: maximum image upload size.
- `ALLOWED_IMAGE_TYPES`: comma-separated accepted image MIME types.
- `CORS_ORIGINS`: comma-separated allowed origins or `*` for local development.
- `DEV_AUTO_LOGIN`: creates a reserved local demo session only when `APP_ENV=development`.
- `LOGIN_RATE_LIMIT_ATTEMPTS`: failed login attempts allowed per email/IP window.
- `LOGIN_RATE_LIMIT_WINDOW_SECONDS`: failed login throttle window.
- `AUTO_CREATE_TABLES`: local development helper. Must be `false` in production.
- `JOB_PROCESS_INLINE`: processes queued jobs in the request for local simplicity.
- `JOB_WORKER_POLL_SECONDS`: worker polling interval.
- `JOB_WORKER_BATCH_SIZE`: maximum queued jobs processed per worker pass.
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
- audit events

SQLite is the default for quick local development. PostgreSQL is supported through SQLAlchemy by setting `DATABASE_URL`, for example:

```bash
DATABASE_URL=postgresql+psycopg://autoposter:autoposter@postgres:5432/autoposter
docker compose --profile postgres up --build
```

## Verification

Run the local verification gate before pushing changes:

```bash
python scripts/verify.py
```

The script runs Ruff lint, Python compile checks, the full pytest suite, and the doctor command.

You can also run the test suite directly:

```bash
pytest
```

The test suite uses an isolated temporary SQLite database and validates the core create-listing-to-publish-job flow, adapter validation, auth, image upload, and local backup/restore guardrails.

GitHub Actions runs the same verification gate on pushes and pull requests to `main`.

## Diagnostics

Run the doctor command to verify local configuration, database connectivity, migration state, upload storage, platform adapters, and legacy-script isolation:

```bash
python -m app.doctor
python -m app.doctor --json
```

The API also exposes `GET /api/diagnostics`, which includes the same doctor summary plus basic record counts.

Create a redacted support/debug bundle for handoff or incident triage:

```bash
python scripts/support_bundle.py
```

The bundle includes doctor output, git state, and selected docs. It excludes `.env` files, local databases, uploaded media, virtual environments, caches, and raw credentials.

## Local backup and restore

For local SQLite deployments, create a private operator backup of the database and uploaded images:

```bash
python scripts/backup_local_data.py --confirm-private-data
```

Restore a local backup into the configured SQLite database/upload directory:

```bash
python scripts/restore_local_data.py tmp/backups/<backup>.zip --confirm-overwrite
```

These archives contain private user data and uploaded media. Store them encrypted, never attach them to public issues or support bundles, and delete them when the recovery window expires. PostgreSQL and object-storage deployments must use their provider-native backup/restore tooling.

## Image storage

Image uploads are validated before storage:

- filenames are sanitized
- upload size is bounded by `MAX_UPLOAD_SIZE_MB`
- MIME type and file signature are checked
- SHA-256 checksum is stored
- duplicate images on the same listing are ignored
- local storage is isolated under `UPLOAD_DIR/{listing_id}/`

Only JPEG, PNG, GIF, and WebP are enabled by default.

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
- `DELETE /api/auth/me`
- `GET /api/audit-events`
- `GET /api/listings`
- `POST /api/listings`
- `PATCH /api/listings/{id}`
- `POST /api/listings/{id}/images`
- `GET /api/listings/{id}/validate`
- `POST /api/listings/{id}/publish`
- `GET /api/jobs`
- `POST /api/jobs/{id}/retry`
- `POST /api/jobs/{id}/confirm-completion`
- `GET /api/platforms`
- `GET /api/diagnostics`
- `POST /api/accounts`
- `POST /api/templates`
- `GET /api/category-mappings`
- `POST /api/category-mappings`
- `GET /api/export`
- `POST /api/import`

Interactive API docs are available at `http://127.0.0.1:8000/docs`.

Listings include revision tracking. Editing a listing increments its `revision`, and publishing job idempotency includes user, listing, revision, platform, action type, account, and operation mode. Re-queuing the same listing revision returns the existing job; editing the listing allows a fresh platform package/job.

Assisted jobs finish as `needs_user_action` until the owner completes the external platform submission. After that, the owner records the final platform URL with `POST /api/jobs/{id}/confirm-completion` or the queue UI. That changes the job and platform mapping to `published`, adds a publication attempt/history entry, and records that the app did not publish automatically.

Category mappings let a user translate a master listing category into a platform-specific category. Validation and publishing jobs apply these mappings unless a platform-specific override already supplies a category.

List endpoints support bounded pagination with `limit` and `offset`. Core list endpoints also expose focused filtering/sorting parameters, such as `/api/listings?search=chair&status=draft&sort=-updated_at`. The Listings screen uses those query parameters for search, status filtering, sorting, and previous/next paging.

Data portability is available through Settings and the API. `GET /api/export` returns a JSON bundle with listings, platform override drafts, templates, category mappings, and sanitized platform account metadata. `POST /api/import` recreates that business data for the authenticated user. `DELETE /api/auth/me` removes the authenticated user's account, sessions, owned listings, jobs, templates, mappings, platform accounts, and uploaded image files. Password hashes, sessions, job history, platform secret references, and image binaries are not included in the JSON export.

Security and privacy-sensitive actions are recorded in `audit_events`. `GET /api/audit-events` returns the authenticated user's owner-scoped audit history for listing changes, image changes, publish queue actions, manual completion, export/import, and account deletion. Audit details are summary-only and do not store exported payloads, raw platform secrets, passwords, or bearer tokens.

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

## Worker

Publishing jobs are persisted in the database. The worker command processes due queued jobs and can run independently from the web process:

```bash
python -m app.worker
```

Jobs with `next_retry_at` in the future remain queued until their retry time. This keeps assisted posting preparation and future official API publishing out of fragile blocking requests.

## Security and compliance

- No raw platform passwords are stored by the web app.
- New user passwords are hashed with Argon2.
- Older PBKDF2 hashes are still accepted and upgraded on successful login.
- Bearer sessions can be revoked with `POST /api/auth/logout`.
- Failed login attempts are rate-limited per email/IP window.
- External calls are isolated behind adapter interfaces.
- The default integrations are assisted-only where official automation credentials are absent.
- Jobs are idempotent per listing/platform and include platform cooldowns.
- Use official APIs when converting an assisted adapter into a fully automated adapter.
- Do not bypass CAPTCHAs, anti-bot protections, login protections, payment prompts, or platform rate limits.

## Project phase documentation

- Technical audit: `docs/TECHNICAL_AUDIT.md`
- Critical path: `docs/CRITICAL_PATH.md`
- Acceptance tests: `docs/ACCEPTANCE_TESTS.md`
- Product definition: `docs/PRODUCT_DEFINITION.md`
- Platform reality review: `docs/PLATFORM_REALITY_REVIEW.md`
- Legacy script quarantine: `docs/LEGACY_SCRIPT_QUARANTINE.md`
- Rate limits: `docs/RATE_LIMITS.md`
- Security: `docs/SECURITY.md`
- API usage audit: `docs/API_USAGE_AUDIT.md`
- UI action audit: `docs/UI_ACTION_AUDIT.md`
- Operator runbook: `docs/OPERATOR_RUNBOOK.md`
- Technical debt register: `docs/TECHNICAL_DEBT_REGISTER.md`
- Testing strategy: `docs/TESTING_STRATEGY.md`
- Operator runbook: `docs/OPERATOR_RUNBOOK.md`
- Backup and restore: `docs/BACKUP_RESTORE.md`
- Official API credential checklist: `docs/OFFICIAL_API_CREDENTIAL_CHECKLIST.md`
- Performance and scale basics: `docs/PERFORMANCE_SCALE_BASICS.md`
- Release readiness: `docs/RELEASE_READINESS.md`
- Supply chain and dependencies: `docs/SUPPLY_CHAIN.md`
- State machines: `docs/STATE_MACHINES.md`
- Feature flags: `docs/FEATURE_FLAGS.md`
- Demo mode: `docs/DEMO_MODE.md`
- Completion matrix: `docs/COMPLETION_MATRIX.md`
- Final verification report: `docs/FINAL_VERIFICATION_REPORT.md`
- Codex worklog: `docs/CODEX_WORKLOG.md`
- Codex checkpoints: `docs/CODEX_CHECKPOINTS.md`
- Task graph: `docs/TASK_GRAPH.md`

## Production notes

- Set a strong `SECRET_KEY`.
- Use a managed database by changing `DATABASE_URL`.
- Place uploads on persistent storage.
- Put the app behind HTTPS.
- Restrict `CORS_ORIGINS`.
- Run Alembic migrations before production startup.
- Configure platform OAuth/API credentials only through environment variables or a proper secret manager.
- Keep the security headers middleware enabled. HTTPS deployments also receive HSTS.
