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
