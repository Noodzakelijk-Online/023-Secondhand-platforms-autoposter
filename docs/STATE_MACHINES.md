# State Machines

The app stores status values as strings in the database, but the job lifecycle is now enforced through `app.services.job_state`.

## Publishing Job Statuses

- `queued`: waiting for worker or inline processing.
- `running`: adapter execution is in progress.
- `needs_user_action`: assisted posting package is ready and the user must finish platform-side steps.
- `published`: official API or future user-confirmation flow has recorded a successful publication.
- `failed`: processing failed and may be retried.
- `skipped`: processing was intentionally skipped.

## Transition Rules

- `queued` can remain `queued`, move to `running`, or fail defensively.
- `running` can finish as `published`, `failed`, `needs_user_action`, `skipped`, or return to `queued` for cooldown.
- Terminal statuses can only return to `queued` through an explicit retry path.
- Unknown statuses and invalid transitions raise an error instead of silently mutating the job.

The state-machine tests live in `tests/test_job_state.py`, and worker/API coverage verifies the normal queue-to-assisted flow.
