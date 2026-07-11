# Rate Limits And Cooldowns

The app includes a conservative per-platform cooldown for publishing jobs. This is designed to prevent rapid repeat attempts and to avoid implying that the app can evade marketplace restrictions.

## Current Configuration

- Environment variables: `PLATFORM_RATE_LIMIT_SECONDS`, `PLATFORM_RATE_LIMIT_OVERRIDES`
- Default: `60`
- Scope: shared per platform across jobs
- Override format: comma-separated `platform=seconds`, for example `marktplaats=120,ebay=300`
- Behavior: if another job for the same platform started within the cooldown window, the next job remains queued and receives `next_retry_at`.

## Official API Quota Headers

Future official API adapters can return response metadata in `PublishOutcome.data` under one of these keys:

- `rate_limit_headers`
- `quota_headers`
- `response_headers`
- `headers`

The worker understands `Retry-After`, `RateLimit-Reset`, `X-RateLimit-Reset`, `RateLimit-Remaining`, and common dashed variants. If an adapter reports a `429` status or zero remaining quota with a reset time, the job is returned to `queued`, `next_retry_at` is persisted, and a warning log records the quota source. This keeps official API quota handling centralized instead of burying it inside each future adapter.

## Current Limitations

- The worker loop is still simple; delayed jobs are persisted but not automatically resumed by a separate production worker process.
- The frontend can show queued job state and logs, but does not yet show a dedicated countdown.
- Official API integrations are not implemented yet, so quota-header behavior is currently covered by adapter-level tests and worker simulation rather than live marketplace calls.

## Compliance Rule

Rate limiting must never be treated as something to bypass. If an official API later exposes quota headers or documented marketplace limits, the platform adapter must obey them and log delayed retries.

## Regression Tests

- A second job for the same platform is delayed.
- The job log includes the cooldown reason.
- `next_retry_at` is set.
- Permanent validation failures do not retry rapidly.
- Per-platform configured limits override the default.
- Official API `Retry-After` and reset headers requeue a job instead of retrying immediately.
