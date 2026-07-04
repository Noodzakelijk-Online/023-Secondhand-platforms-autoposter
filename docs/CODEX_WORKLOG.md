# Codex Worklog

## 2026-07-04

### Pass 9 - Static UI Accessibility Baseline

- Added `scripts/audit_static_ui.py` to check the static app shell for document language/title, landmarks, labelled controls, named buttons, image alt coverage, live region presence, and positive-tabindex regressions.
- Added `tests/test_static_ui_audit.py` so the pytest/verification gate covers the audit.
- Fixed the image upload input by giving it a programmatic label.
- Added `docs/ACCESSIBILITY_BROWSER_AUDIT.md` and updated testing, acceptance, critical-path, completion, runbook, security, API/UI audit, and task-graph docs.
- Kept browser E2E, keyboard traversal, contrast checks, responsive screenshots, and assistive-technology signoff marked as remaining work.

## 2026-07-03

### Pass 5 - Local Backup And Restore

- Added `scripts/backup_local_data.py` for explicit private-data local SQLite/upload backups.
- Added `scripts/restore_local_data.py` for guarded local restore into configured SQLite/upload paths.
- Required confirmation flags for both backup and restore to avoid accidental private data handling.
- Added tests for refusal defaults and SQLite/upload round-trip behavior.
- Updated acceptance, security, runbook, completion, and verification docs.

### Pass 6 - Provider Credential Reality

- Added platform metadata for official API status, credential requirements, and automation blockers.
- Marked eBay as eligible only when real OAuth/app/sandbox/secret-store prerequisites are configured.
- Surfaced credential/compliance reality in platform cards without adding fake connect or publish actions.
- Extended platform metadata tests and provider reality docs.

### Pass 7 - Worker Claiming

- Added a due-job claim step before processing queued jobs.
- Prevented a second worker session from claiming a job already moved out of `queued`.
- Added worker test coverage for claim-once behavior.

### Pass 8 - Stale Worker Recovery

- Added `JOB_RUNNING_TIMEOUT_SECONDS`.
- Requeued jobs left `running` beyond the timeout on later worker passes.
- Logged stale recovery events for operator visibility.
- Added tests for stale and fresh running-job handling.

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
