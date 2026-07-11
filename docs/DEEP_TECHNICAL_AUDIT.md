# Deep Technical Audit

Date: 2026-07-11

This audit reviews the current FastAPI/static-dashboard implementation after the platform contract, wording, query-control, and error-UX hardening slices. It is a repository-level engineering audit, not a deployment penetration test or a claim of final launch readiness.

## Scope Reviewed

- Application entrypoint and middleware: `app/main.py`, `app/middleware.py`.
- API routes and ownership checks: `app/api.py`.
- Database models, migrations, and query helpers: `app/models.py`, `migrations/versions/`, `app/query.py`.
- Authentication, sessions, throttling, and feature flags: `app/security.py`, `app/rate_limit.py`, `app/config.py`, `app/feature_flags.py`.
- Storage and upload validation: `app/storage.py`.
- Platform adapter contract and assisted posting behavior: `app/adapters/`, `app/services/jobs.py`, `app/services/job_state.py`.
- Data portability, audit events, analytics, localization, and diagnostics services.
- Static frontend source: `public/index.html`, `public/app.js`, `public/styles.css`.
- Test and verification gates: `tests/`, `scripts/verify.py`, GitHub workflows.
- Existing risk documents: red-team review, technical debt register, release readiness, no-mocks audit, and platform completion contracts.

## Current Architecture

The app is a FastAPI service with a static HTML/CSS/JavaScript dashboard. It uses SQLAlchemy models, Alembic migrations, bearer-token sessions, local image storage, assisted platform adapters, persistent publishing jobs, and JSON export/import. Route ownership is enforced in the API layer by filtering user-owned resources before read/mutate operations.

The adapter system is intentionally assisted-only for registered production platforms. Jobs prepare copy-ready packages and return `needs_user_action`; no registered production adapter claims API-confirmed publication.

## Strengths

- Authentication uses Argon2 for new passwords and upgrades legacy PBKDF2 hashes on successful login.
- Sessions are bearer-token based, revocable, and not set as cookies.
- Failed-login throttling is persisted and now exposed as retryable structured error metadata.
- Owner-isolation coverage exists for core owned resources and data portability flows.
- Uploads validate size, extension, MIME signature, safe filenames, checksums, and duplicate images.
- Error responses use a structured envelope with code, field errors, retryability, and request IDs.
- Platform adapters expose tested capability metadata, blocked actions, prepared fields, and assisted behavior.
- Publishing jobs have persistent records, idempotency keys, logs, retries, cooldowns, atomic claims, and stale-running recovery.
- The frontend has real API wiring for core CRUD, validation, quality guidance, assisted package review, diagnostics, export/import, and query controls.
- Verification is centralized in `python scripts/verify.py` and currently covers lint, compile, tests, and doctor diagnostics.

## Key Risks And Remaining Work

| Area | Current state | Remaining work |
| --- | --- | --- |
| Deployment database | SQLite/local verification is strong; migrations exist. | Prove Alembic migration and worker behavior against the target PostgreSQL database. |
| Edge security | App-level auth, CSP/security headers, bearer-only posture, and throttling exist. | Capture host/proxy/WAF rate-limit evidence as a release-readiness item. |
| Official APIs | eBay OAuth consent foundation exists. | Token exchange, refresh, secret-manager storage, sandbox publish proof, quota handling, and official adapter behavior remain unimplemented. |
| Storage backend | Local storage is hardened. | Add and test S3/object storage before remote production storage. |
| Browser evidence | Source-level UI wiring and tests exist. | Execute browser, responsive, accessibility, import/export, retry, and prepublish walkthroughs. |
| Frontend architecture | Static frontend is sufficient for current scope. | Split frontend modules only if continued growth makes state/event handling risky. |
| Data portability | Sanitized JSON export/import, listing CSV import/export, and separate image ZIP export exist with tests. | Keep privacy rules explicit as new portable fields are added. |
| Admin/audit review | Sanitized audit events, owner-scoped privacy activity review, and retention purge exist. | Add cross-user admin review only if explicit operator roles are introduced. |
| Type safety | Ruff and compile gates exist. | Decide whether mypy/pyright is worth the added maintenance cost. |

## Audit Findings

No critical local-code blocker was found that invalidates the current assisted-posting demo posture. The strongest unresolved blockers are environment-dependent: PostgreSQL/concurrent-worker proof, deployment-edge controls, browser/accessibility evidence, and real user walkthrough evidence.

The highest product risk remains overclaiming automation. Current UI wording, adapter behavior, and tests now consistently describe assisted package preparation, not automatic marketplace submission.

The largest future implementation risk is official API publishing. It should remain gated behind `docs/OFFICIAL_API_CREDENTIAL_CHECKLIST.md` and must not reuse assisted adapter success semantics.

## Evidence Added Or Referenced

- `docs/RED_TEAM_REVIEW.md`
- `docs/TECHNICAL_DEBT_REGISTER.md`
- `docs/PLATFORM_COMPLETION_CONTRACTS.md`
- `docs/UI_WORDING_AUDIT.md`
- `docs/ERROR_HANDLING_UX.md`
- `docs/RELEASE_READINESS.md`
- `tests/test_owner_isolation.py`
- `tests/test_platform_contracts.py`
- `tests/test_frontend_error_ux.py`
- `tests/test_extended_query_controls.py`
- `scripts/verify.py`

## Release Impact

This audit is enough to close the formal local deep-audit documentation gap. It does not make the project release-ready. The release gate still depends on browser evidence, fresh-clone verification, deployment evidence, target-database migration proof, client acceptance of assisted-posting limits, and any chosen official API/storage work.
