# Testing Strategy

This strategy defines the current test layers, the verification gate, and the gaps that remain before release.

## Verification Gate

Run the full local gate before pushing:

```bash
python scripts/verify.py
```

The gate runs:

- Ruff lint for `app`, `tests`, `migrations`, and `scripts`
- Python compile checks for `app`, `tests`, and `migrations`
- the full pytest suite
- `python -m app.doctor --json`

Doctor warnings are allowed for local development defaults; doctor errors fail the gate.

GitHub Actions runs the same command on pushes and pull requests to `main` via `.github/workflows/verify.yml`.

## Current Test Layers

| Layer | Files | Purpose |
| --- | --- | --- |
| Architecture boundaries | `tests/test_architecture.py` | Verifies auth/system routes and shared request dependencies stay split from product routes. |
| API smoke and route contract | `tests/test_api.py`, `tests/test_api_hardening.py` | Core listing/account/template flow, platform metadata, direct detail/delete routes, request IDs, metrics, pagination, filters, and structured errors. |
| Acceptance workflow | `tests/test_acceptance_workflow.py` | Seller setup-to-portability API acceptance flow covering accounts, templates, mappings, listing/image creation, quality, validation, assisted jobs, analytics, export/import, and audit activity. |
| Owner isolation | `tests/test_owner_isolation.py` | Cross-user visibility and mutation boundaries for owned listings, jobs, accounts, templates, and category mappings. |
| Auth/security | `tests/test_auth_security.py`, `tests/test_api_rate_limit.py` | Password hashing, login/logout/session behavior, token revocation, bearer-only auth posture, database-backed hashed failed-login throttling with expiry/success clearing/`Retry-After`, and general API throttling. |
| SaaS/account readiness | `tests/test_saas_readiness.py` | Personal-account readiness contract, billing-free status, workspace deferral, and owner-scoped usage counts. |
| Storage | `tests/test_storage_uploads.py`, `tests/test_startup_safety.py` | Filename sanitization, MIME/signature validation, duplicate detection, delete/reorder behavior, metadata persistence, local file cleanup, S3-compatible object writes/deletes, and storage config validation. |
| Category mappings | `tests/test_category_mappings.py` | Mapping CRUD/upsert/patch behavior and mapping use in validation/publish output. |
| Official API foundations | `tests/test_ebay_oauth.py`, `tests/test_platform_rate_limits.py` | eBay OAuth state safety, token exchange, token refresh, secret-store redaction, sandbox Inventory API probe shape, and quota-header backoff. |
| Jobs/worker | `tests/test_worker.py`, `tests/test_job_state.py`, `tests/test_platform_rate_limits.py`, `tests/test_config.py` | Database-backed queue processing, worker empty-queue behavior, job detail route, filtering/sorting/pagination, atomic claims, PostgreSQL `SKIP LOCKED` claim SQL, stale-running recovery, state transitions, user-confirmed manual completion, platform cooldown overrides, and official API quota-header backoff. |
| Listing revisions/idempotency | `tests/test_listing_revisions.py` | Revision increments and publish idempotency boundaries. |
| Domain model | `tests/test_domain_model.py` | Listing aggregate cascade behavior for images, drafts, mappings, jobs, logs, and attempts. |
| Data invariants | `tests/test_data_invariants.py` | Money/weight validation, currency/tag/category-attribute normalization, and listing condition/status choices. |
| Data portability | `tests/test_data_portability.py` | Sanitized JSON export/import, listing CSV round trip including category attributes, image ZIP export, settings, mappings, and account metadata. |
| Diagnostics/startup/migrations | `tests/test_doctor.py`, `tests/test_config.py`, `tests/test_startup_safety.py`, `tests/test_migrations.py` | Doctor checks, `.env.example` runtime-setting synchronization, startup safety guards, production-like config validation, SQLite migration smoke coverage, and PostgreSQL dialect schema rendering. |
| Observability | `tests/test_observability.py` | Structured JSON log formatting and request log metadata. |
| Internationalization | `tests/test_internationalization.py` | Locale metadata, frontend copy catalog presence, Dutch shell copy, locale selector, and English fallback contract. |
| Accessibility | `tests/test_accessibility_audit.py` | Static dashboard smoke checks for labeled controls, named buttons, image alt text, landmarks, headings, and live status regions. |
| Browser workflow evidence | `scripts/browser_e2e_workflow.cjs`, `tests/test_browser_e2e_workflow.py`, `docs/BROWSER_E2E_WORKFLOW.md` | Executed Chromium workflow for registration, listing save, image upload, validation, assisted job queueing, manual completion, JSON export, and account deletion. |
| Release readiness controls | `tests/test_release_readiness.py`, `docs/RELEASE_READINESS.md`, `docs/RELEASE_EVIDENCE_RECORD.md` | Launch evidence gates, explicit missing-evidence placeholders, and anti-overclaim release blocker language. |
| Non-technical user evidence controls | `tests/test_non_technical_user_simulation.py`, `docs/NON_TECHNICAL_USER_SIMULATION.md`, `docs/NON_TECHNICAL_USER_WALKTHROUGH_RECORD.md` | Proxy scenario, observed-user record requirements, manual-posting comprehension checks, and explicit external-evidence blocker language. |
| Legacy isolation | `tests/test_legacy_quarantine.py` | Ensures legacy browser automation imports do not leak into the web app path. |

## Data And Isolation

- Tests use SQLite via `sqlite:///./data/test_autoposter.db`.
- Test modules reset the SQLAlchemy metadata for isolation.
- Platform cooldown tests either disable cooldowns with `PLATFORM_RATE_LIMIT_SECONDS=0` or use `PLATFORM_RATE_LIMIT_OVERRIDES` for platform-specific behavior.
- Tests do not require browser automation, external marketplace credentials, or real platform network calls.

## Coverage Priorities

1. Idempotency, retries, and worker concurrency for publishing jobs.
2. File safety: upload validation, storage paths, duplicate handling, ordering, and deletion.
3. Data portability and privacy: no password/session/platform secrets in exports.
4. Assisted-posting honesty: tests should verify prepared packages and user-action states instead of fake automated success.

## Remaining Gaps

- Browser-executed accessibility, keyboard navigation, and cross-browser matrix tests.
- Live multi-worker concurrency tests against the target PostgreSQL database.
- Live PostgreSQL-backed migration and integration test run.
- Frontend state consistency tests for filters, pagination, and edit modes.
- Official API/OAuth sandbox tests when future platform API integrations are added.
