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
| API smoke and route contract | `tests/test_api.py`, `tests/test_api_hardening.py` | Core listing/account/template flow, platform metadata, direct detail/delete routes, request IDs, pagination, filters, and structured errors. |
| Auth/security | `tests/test_auth_security.py` | Password hashing, login/logout/session behavior, token revocation, and failed-login throttling. |
| Storage | `tests/test_storage_uploads.py` | Filename sanitization, MIME/signature validation, duplicate detection, delete/reorder behavior, and metadata persistence. |
| Category mappings | `tests/test_category_mappings.py` | Mapping CRUD/upsert/patch behavior and mapping use in validation/publish output. |
| Jobs/worker | `tests/test_worker.py` | Database-backed queue processing, claim-once behavior, stale running-job recovery, worker empty-queue behavior, job detail route, and job filtering/sorting/pagination. |
| Listing revisions/idempotency | `tests/test_listing_revisions.py` | Revision increments and publish idempotency boundaries. |
| Data portability | `tests/test_data_portability.py` | Sanitized export/import for listings, settings, mappings, and account metadata. |
| Diagnostics/startup/migrations | `tests/test_doctor.py`, `tests/test_startup_safety.py`, `tests/test_migrations.py` | Doctor checks, startup safety guards, and migration availability. |
| Legacy isolation | `tests/test_legacy_quarantine.py` | Ensures legacy browser automation imports do not leak into the web app path. |
| Static UI accessibility | `tests/test_static_ui_audit.py`, `scripts/audit_static_ui.py` | Checks document landmarks, form labels, button names, image alt coverage, live region presence, and positive-tabindex regressions in the static app shell. |

## Data And Isolation

- Tests use SQLite via `sqlite:///./data/test_autoposter.db`.
- Test modules reset the SQLAlchemy metadata for isolation.
- Platform cooldowns are disabled for tests with `PLATFORM_RATE_LIMIT_SECONDS=0`.
- Tests do not require browser automation, external marketplace credentials, or real platform network calls.

## Coverage Priorities

1. Owner isolation for every resource mutation and detail route.
2. Idempotency, retries, and worker concurrency for publishing jobs.
3. File safety: upload validation, storage paths, duplicate handling, ordering, and deletion.
4. Data portability and privacy: no password/session/platform secrets in exports.
5. Assisted-posting honesty: tests should verify prepared packages and user-action states instead of fake automated success.

## Remaining Gaps

- Browser end-to-end tests for the static dashboard.
- Browser-based accessibility checks, color contrast checks, and keyboard navigation tests.
- Database-specific worker locking drills against the production database engine.
- PostgreSQL-backed migration and integration test run.
- Frontend state consistency tests for filters, pagination, and edit modes.
- Official API/OAuth sandbox tests when future platform API integrations are added.
