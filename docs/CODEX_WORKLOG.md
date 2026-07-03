# Codex Worklog

## 2026-07-03

### Pass 3 - Platform Secret Boundary

- Rechecked platform account security and provider credential boundaries.
- Added recursive detection for secret-like keys in platform account `connection_data`.
- Rejected new platform account metadata that includes raw passwords, tokens, API keys, access keys, private keys, or secrets.
- Kept export sanitization coverage for legacy/stored secret-like fields.
- Added API hardening test coverage and updated security/provider docs.

### Pass 4 - Support Bundle

- Added `scripts/support_bundle.py` for redacted support/debug ZIP generation.
- Included doctor output, git state, environment summary with secret-like values redacted, and selected docs.
- Excluded `.env` files, local databases, uploaded media, virtual environments, caches, and raw credentials.
- Added support bundle safety tests and operator documentation.

### Pass 2 - Audit Events

- Re-inspected branch, remotes, PR state, files, migrations, docs, and completion matrix.
- Added persistent `audit_events` model and Alembic migration.
- Added `GET /api/audit-events` with owner-scoped filtering and pagination.
- Recorded audit events for listing/image changes, publish queue actions, manual completion, platform account metadata changes, templates, category mappings, export, import, and self-service account deletion.
- Added tests for audit migration, owner scoping, export/import events, and retained account-deletion evidence.
- Updated README and required Giant Prompt docs.

### Pass 1 - Assisted Completion

- Read the Giant Codex Goal Prompt PDF.
- Audited branch, commit history, repository files, stack, tests, docs, adapters, jobs, schemas, and UI.
- Identified the missing critical-path segment: recording manual completion and final platform URL after assisted posting.
- Added `POST /api/jobs/{job_id}/confirm-completion`.
- Added queue UI package preview and manual completion form.
- Added API tests for happy path, invalid status, and owner isolation.
- Added or updated audit, critical path, acceptance, security, runbook, UI action, completion matrix, and verification docs.
