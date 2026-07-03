# Technical Audit

Audit date: 2026-07-03.

## Repository State

- Branch inspected: `main`.
- Starting commit for first implementation pass: `bad1e2b Add CI verification workflow`.
- Starting commit for audit-event pass: `2898fe4 Add assisted posting completion workflow`.
- Stack: FastAPI, SQLAlchemy, Alembic, static HTML/CSS/JavaScript, pytest, Docker Compose.
- Default branch matches current working branch: yes, `origin/HEAD -> origin/main`.

## Product State

Implemented foundations:

- Authenticated user accounts and bearer sessions.
- Owner-scoped listings, images, platform mappings, jobs, accounts, templates, category mappings, export/import, and deletion.
- Assisted platform adapters for Marktplaats, Koopplein, Nextdoor, eBay, and Tweedehands.
- Platform metadata that exposes official API status, credential requirements, and automation blockers.
- Persistent jobs, job logs, publication attempts, idempotency keys, cooldowns, worker entrypoint, and due-job claiming.
- Persistent owner-scoped audit events for state-changing and privacy-sensitive actions.
- Redacted support/debug bundle generation for operator handoff.
- Guarded local SQLite/upload private backup and restore scripts.
- Local validated image storage.
- API error envelope, request IDs, and security headers.

Known gaps:

- No official marketplace API/OAuth publishing integration is enabled.
- eBay is only marked eligible when configured; provider OAuth/app/sandbox/secret-store prerequisites remain external blockers.
- No browser E2E suite or accessibility automation yet.
- Local filesystem storage only.
- Production backup/restore still needs provider-native drills for PostgreSQL/object storage.
- Worker claiming exists, but stale running-job recovery and distributed rate limits need production hardening.
- The legacy script folder remains in the repo for reference and should stay out of default runtime paths.
- Audit events are summary records and are not tamper-proof immutable ledger entries.
