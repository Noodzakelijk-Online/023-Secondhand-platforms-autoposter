# Release Readiness

This document defines the gate for calling the project release-ready. It is intentionally stricter than "the app runs locally."

## Current Status

Status: not release-ready yet.

The app has a working core, tests, migrations, Docker setup, assisted posting, job tracking, diagnostics, backup guidance, and production-safety documentation. It still needs final security, browser, deployment, and credential checks before a real client launch.

## Required Before Client Launch

- Run `python scripts/verify.py` from a clean checkout.
- Run Alembic migrations against the target database.
- Replace development secrets and disable unsafe development defaults.
- Confirm `APP_ENV=production` startup passes without default `SECRET_KEY`.
- Confirm `JOB_PROCESS_INLINE=false` if background workers are expected.
- Run the worker process with the same environment as the API.
- Confirm upload storage path or object storage is backed up.
- Confirm backup and restore procedure from `docs/BACKUP_RESTORE.md`.
- Confirm operator procedures from `docs/OPERATOR_RUNBOOK.md`.
- Review assisted-posting wording in the UI and README.
- Confirm no platform is described as fully automated without official API evidence.
- Confirm every client-visible platform limitation is documented.
- Run a non-technical user walkthrough with a fresh account.
- Run responsive checks on desktop and mobile viewport sizes.
- Run accessibility checks for form labels, focus order, contrast, and keyboard use.
- Confirm no credentials, tokens, cookies, platform passwords, or image binaries are included in exports or logs.
- Confirm production rate-limit, retry, and job cooldown settings.
- Confirm legal/platform compliance for every enabled marketplace.

## Deployment Evidence

Capture these items for the release record:

- Commit SHA deployed.
- Environment name and deployment URL.
- Database migration head.
- Verification command output.
- Doctor command output.
- Backup location and restore test result.
- Worker process status.
- Known warnings accepted for launch.
- Rollback procedure.

## Launch Blockers

Do not launch if any of these are true:

- `python scripts/verify.py` fails.
- The app starts in production with default development secrets.
- A platform claims automatic publishing without a working official API integration.
- The target database is behind Alembic head.
- Upload storage is not writable or not backed up.
- The worker is required but not running.
- The client has not accepted assisted-posting limitations.

## Post-Launch Checks

- Confirm first user registration and login.
- Create a test listing with images.
- Generate assisted posting packages for each enabled platform.
- Confirm job logs and diagnostics are visible.
- Confirm export works and excludes secrets.
- Confirm account deletion removes owned records and uploaded files.
- Review application logs for errors after the first session.
