# Backup, Restore, And Disaster Recovery

This runbook defines the minimum backup set and restore procedure for production operation.

## Backup Scope

Back up these items together:

- production database
- upload directory configured by `UPLOAD_DIR`
- deployed git commit SHA
- environment/secret references, excluding raw secret values from ordinary backup logs
- Alembic revision at backup time

User JSON exports are useful for portability, but they are not a replacement for operator backups because image binaries and job history are intentionally excluded.

## Backup Cadence

- Database: at least daily, plus before migrations.
- Uploads: at least daily and after large import/upload batches.
- Configuration references: after every deployment or secret rotation.
- Test restore: monthly, and before major releases.

## Pre-Migration Backup

Before `alembic upgrade head` in production:

1. Stop the worker.
2. Take a database backup.
3. Snapshot/copy uploads.
4. Record current git SHA and Alembic revision.
5. Run the migration.
6. Run `python -m app.doctor --json`.
7. Start the worker only after diagnostics are acceptable.

## Restore Order

1. Stop worker and web processes.
2. Restore database.
3. Restore uploads to the configured `UPLOAD_DIR`.
4. Deploy the matching git commit, or a commit known to support the restored schema.
5. Run `alembic upgrade head`.
6. Run `python -m app.doctor --json`.
7. Start web process.
8. Start worker process.

## Reconciliation Checks

After restore, verify:

- `GET /api/health` returns `ok`.
- `GET /api/diagnostics` has no `error` status.
- Listing image tiles load for a restored listing.
- Queue counts are plausible and no duplicate worker is running.
- A test export for a non-sensitive account returns sanitized JSON.

## Disaster Recovery Notes

- If duplicate posting risk is suspected, keep the worker stopped until queue state is reviewed.
- If uploads are missing, do not run cleanup jobs that could remove image metadata before investigating backups.
- If migration state is uncertain, prefer restoring to the recorded backup commit and revision instead of forcing schema changes.
- Keep legacy Selenium scripts out of production recovery paths.
