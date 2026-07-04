# Fake Provider Lab

The fake provider lab is a test-only harness for future official API integrations. It lets tests exercise successful publishes, idempotency replay, and API failures without adding fake success behavior to production adapters.

## Location

- `tests/fake_provider_lab.py`
- `tests/test_fake_provider_lab.py`

The lab is intentionally under `tests/`. It is not imported by `app.adapters.registry`, is not returned by `GET /api/platforms`, and is not available to production publishing jobs.

## What It Provides

- `FakeOfficialApiClient`: deterministic fake API client with queued responses.
- `FakeOfficialApiAdapter`: `PlatformAdapter` implementation with `automation_mode="official_api"` for tests only.
- Deterministic default success responses with fake listing IDs and URLs.
- Idempotency replay for repeated publish requests using the same key.
- Queued failure responses for negative-path official API tests.

## Rules

- Do not register the fake provider in `app.adapters.registry.ADAPTERS`.
- Do not import the fake provider from application code.
- Use it only for official API provider tests that need deterministic local responses.
- Assisted production adapters must continue to return `needs_user_action`, not fake `published`.
- Real official API adapters must replace fake responses with sandbox-backed and credential-gated behavior before production use.
