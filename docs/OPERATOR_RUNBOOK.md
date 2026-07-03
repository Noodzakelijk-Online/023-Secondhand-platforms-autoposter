# Operator Runbook

This runbook is for deploying and operating the production-safe assisted-posting app.

## Pre-Deploy Checks

1. Set production environment values:
   - `APP_ENV=production`
   - strong `SECRET_KEY`
   - production `DATABASE_URL`
   - persistent `UPLOAD_DIR`
   - restrictive `CORS_ORIGINS`
   - `AUTO_CREATE_TABLES=false`
   - `JOB_PROCESS_INLINE=false`
2. Install dependencies from `requirements.txt`.
3. Run migrations:

```bash
alembic upgrade head
```

4. Run the verification gate:

```bash
python scripts/verify.py
```

Doctor warnings must be understood before release; doctor errors block release.

## Start Services

Web process:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Worker process:

```bash
JOB_PROCESS_INLINE=false python -m app.worker
```

Workers claim due queued jobs before processing. If a worker exits after claiming a job, a later worker pass requeues jobs that have remained `running` longer than `JOB_RUNNING_TIMEOUT_SECONDS` so they can be retried. Tune the timeout above the longest expected assisted/API preparation duration.

Docker Compose:

```bash
docker compose up --build
```

## Health Checks

- App health: `GET /api/health`
- Diagnostics: `GET /api/diagnostics`
- CLI diagnostics: `python -m app.doctor --json`

Expected production status is `ok`. A warning requires operator review. An error requires rollback or repair.

## Routine Operations

- Check the Queue screen for `failed` and `needs_user_action` jobs.
- Use job retry only after confirming the listing and platform account state.
- Keep uploads on persistent storage and include them in backups.
- Keep database backups separate from application deploy artifacts.
- Do not run legacy Selenium scripts inside the web or worker process.

## Backup And Restore

Minimum backup set:

- production database
- upload directory
- deployed `.env` or secret-manager references
- current git commit SHA

Restore order:

1. Restore database.
2. Restore uploads to `UPLOAD_DIR`.
3. Deploy the matching git commit.
4. Run `alembic upgrade head`.
5. Run `python -m app.doctor --json`.
6. Start web and worker services.

## Diagnostics

```bash
python -m app.doctor
python -m app.doctor --json
```

Use `/api/health` for a lightweight API liveness check and `/api/diagnostics` for authenticated operational diagnostics.

## Support Bundle

Create a redacted support/debug ZIP:

```bash
python scripts/support_bundle.py
```

The bundle is written under `tmp/support-bundles/` by default. It includes doctor output, git state, and selected docs. It intentionally excludes `.env` files, local databases, uploaded media, virtual environments, caches, and raw credentials.

## Local Backup And Restore

The local backup scripts are for SQLite plus local filesystem uploads only. They intentionally require explicit confirmation because the archive contains private user data and uploaded images.

Create a private backup:

```bash
python scripts/backup_local_data.py --confirm-private-data
```

Restore a private backup:

```bash
python scripts/restore_local_data.py tmp/backups/<backup>.zip --confirm-overwrite
```

Handling rules:

- Store backup ZIPs encrypted and outside the repository.
- Do not attach private backups to support tickets, public issues, pull requests, or redacted support bundles.
- Stop the web and worker processes before restoring local data.
- Run `alembic upgrade head` and `python -m app.doctor` after restoring.
- Verify a sample listing, image URL, platform mapping, and job history before resuming worker processing.

External blocker for production-grade backup: PostgreSQL and object-storage deployments need provider-native backup/restore tooling, retention policy, encryption controls, and a tested restore drill in the target hosting environment.

## Audit Events

Authenticated users can inspect their action history with:

```bash
curl -H "Authorization: Bearer <token>" http://127.0.0.1:8000/api/audit-events
```

Use query parameters such as `event_type=data_exported` or `resource_type=listing` during support investigations. Audit events are summary records only; they should not contain raw passwords, bearer tokens, platform API tokens, or exported data bundles.

## Safety Stop

If platform policy, credentials, or user account safety is uncertain, leave jobs in `needs_user_action` and do not add automated provider clients. The operator can disable workers by stopping `python -m app.worker`; queued jobs remain persisted.

## Incident Checklist

- Capture current git SHA and environment name.
- Run `python -m app.doctor --json`.
- Check app logs, worker logs, and recent failed job logs.
- Pause the worker if duplicate posting risk is suspected.
- Export affected user data before destructive repair when possible.
- Prefer rollback to the last known good commit if startup, auth, or migration safety is uncertain.

## Rollback

1. Stop worker first.
2. Stop web process.
3. Deploy last known good commit.
4. Restore database only if the failed release changed data incompatibly.
5. Run diagnostics.
6. Start web, then worker.
