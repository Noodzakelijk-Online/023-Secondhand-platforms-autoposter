# Operator Runbook

This runbook is for deploying and operating the production-safe assisted-posting app.

## Pre-Deploy Checks

1. Set production environment values:
   - `APP_ENV=production`
   - strong `SECRET_KEY`
   - production `DATABASE_URL`
   - persistent `UPLOAD_DIR`
   - restrictive `CORS_ORIGINS`
   - `AUTH_TRANSPORT=bearer`
   - `AUTO_CREATE_TABLES=false`
   - `JOB_PROCESS_INLINE=false`
   - `LOG_LEVEL=INFO`
   - `LOG_FORMAT=json` when logs are collected by a structured log system
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
python -m app.worker
```

Docker Compose:

```bash
docker compose up --build
```

## Health Checks

- App health: `GET /api/health`
- Diagnostics: `GET /api/diagnostics`
- Metrics snapshot: `GET /api/metrics`
- CLI diagnostics: `python -m app.doctor --json`

Expected production status is `ok`. A warning requires operator review. An error requires rollback or repair.

## Logs

- Web requests are logged on `autoposter.requests` with `request_id`, method, path, status code, and duration.
- Worker lifecycle and batch activity are logged on `autoposter.worker`.
- Set `LOG_FORMAT=json` in production when the process manager or hosting platform collects stdout.
- Use the `X-Request-ID` response header to connect API errors, browser reports, and server logs.
- Poll `GET /api/metrics` for lightweight JSON counters covering users, listings, platform accounts, publishing jobs, listing statuses, and publishing job statuses.

## Auth And CSRF

- The supported auth mode is bearer tokens in the `Authorization` header.
- The app does not set authenticated session cookies, so CSRF token middleware is intentionally not enabled.
- Keep `CORS_ORIGINS` restricted in production and serve the app only over HTTPS.
- Do not enable cookie auth without adding CSRF validation and a new security review.

## Routine Operations

- Check the Queue screen for `failed` and `needs_user_action` jobs.
- Use job retry only after confirming the listing and platform account state.
- eBay OAuth consent can create an account with `status=needs_token_exchange` when `EBAY_OAUTH_CLIENT_SECRET` is absent, or `status=connected` when token exchange succeeds through the configured secret store. Official eBay listing publication remains disabled until live sandbox listing proof and seller-policy checks are added.
- Investigate repeated stale-running recovery logs; they can indicate worker crashes, timeouts, or deployment restarts during publishing work.
- Keep uploads on persistent storage and include them in backups.
- Keep database backups separate from application deploy artifacts.
- Run `python -m app.audit_retention` on the chosen retention schedule to purge audit events older than `AUDIT_RETENTION_DAYS`.
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
