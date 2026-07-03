# Rate Limits And Cooldowns

The app includes a conservative per-platform cooldown for publishing jobs. This is designed to prevent rapid repeat attempts and to avoid implying that the app can evade marketplace restrictions.

## Current Configuration

- Environment variable: `PLATFORM_RATE_LIMIT_SECONDS`
- Default: `60`
- Scope: shared per platform across jobs
- Behavior: if another job for the same platform started within the cooldown window, the next job remains queued and receives `next_retry_at`.

## Current Limitations

- There are no per-platform override variables yet.
- The worker loop is still simple; delayed jobs are persisted but not automatically resumed by a separate production worker process.
- The frontend can show queued job state and logs, but does not yet show a dedicated countdown.
- Official API-specific rate-limit headers are not consumed because official API integrations are not implemented yet.

## Compliance Rule

Rate limiting must never be treated as something to bypass. If an official API later exposes quota headers or documented marketplace limits, the platform adapter must obey them and log delayed retries.

## Future Tests

- A second job for the same platform is delayed.
- The job log includes the cooldown reason.
- `next_retry_at` is set.
- Permanent validation failures do not retry rapidly.
- Per-platform configured limits override the default.
