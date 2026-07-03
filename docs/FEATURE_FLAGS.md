# Feature Flags

The app uses a small explicit feature-flag registry in `app.feature_flags`. Flags are still configured through environment variables, but production safety checks and diagnostics now read from one typed source.

## Current Flags

| Flag | Environment variable | Default | Production allowed | Purpose |
| --- | --- | --- | --- | --- |
| `dev_auto_login` | `DEV_AUTO_LOGIN` | `false` | No | Local-only demo session shortcut. |
| `auto_create_tables` | `AUTO_CREATE_TABLES` | `true` | No | Development convenience for creating tables without running Alembic manually. |
| `inline_job_processing` | `JOB_PROCESS_INLINE` | `true` | Yes, with review | Processes publish jobs inside the API request for local simplicity. Production deployments normally run a worker with this disabled. |

## Rules

- Add new runtime flags to `app.feature_flags` before using them elsewhere.
- Each flag must name its environment variable, production posture, and user-facing purpose.
- Production-blocked flags are enforced through `validate_startup_safety`.
- `python -m app.doctor --json` includes the current feature-flag summary.
- Do not use feature flags to hide incomplete or misleading marketplace automation.
