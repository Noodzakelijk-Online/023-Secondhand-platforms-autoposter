# State Machines

The app stores status values as strings in the database, but the job lifecycle is now enforced through `app.services.job_state`.

## Publishing Job Statuses

- `queued`: waiting for worker or inline processing.
- `running`: adapter execution is in progress.
- `needs_user_action`: assisted posting package is ready and the user must finish platform-side steps.
- `published`: official API success or user-confirmed manual completion has recorded a successful publication.
- `failed`: processing failed and may be retried.
- `skipped`: processing was intentionally skipped.

## Transition Rules

- `queued` can remain `queued`, move to `running`, or fail defensively.
- `running` can finish as `published`, `failed`, `needs_user_action`, `skipped`, or return to `queued` for cooldown.
- `needs_user_action` can move to `published` only through explicit user-confirmed manual completion.
- Terminal statuses can only return to `queued` through an explicit retry path.
- Unknown statuses and invalid transitions raise an error instead of silently mutating the job.

## Worker Claiming

Workers claim due jobs with a conditional `queued -> running` database update before adapter execution. If two worker sessions race for the same queued job, only the session that updates the row processes it; the other sees no claimed work. Cooldown checks can move a claimed job back to `queued` with `next_retry_at` set before any adapter attempt is counted.

## Stale Running Recovery

Before claiming due jobs, the worker returns `running` jobs older than `JOB_STALE_RUNNING_SECONDS` to `queued` and writes a warning log. This handles worker crashes or process exits that leave a job claimed but unfinished. Fresh `running` jobs remain untouched.

The state-machine tests live in `tests/test_job_state.py`, and worker/API coverage verifies the normal queue-to-assisted flow, user-confirmed manual completion, atomic due-job claims, cooldowns, and stale-running recovery.
