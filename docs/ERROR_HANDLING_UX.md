# Error Handling And Retry UX

The API returns a structured error envelope for HTTP, validation, and unexpected server errors. The frontend preserves that metadata instead of flattening it into plain text.

## API Contract

Each error response includes:

- `code`: stable machine-readable error code.
- `message`: user-facing summary.
- `details`: non-secret contextual details.
- `field_errors`: validation messages keyed by request field.
- `retryable`: whether retrying the same request can be reasonable.
- `request_id`: value that can be matched to logs and the `X-Request-ID` header.

Rate-limit and transient server-style statuses are marked retryable. Validation and authorization errors are not retryable until the user changes input or signs in again.

## Frontend Contract

The global banner shows the message, the first field-level validation hints, retry guidance when available, and the request ID. Import failures use the same metadata in the data portability panel.

Job details include explicit retry guidance:

- failed jobs: retry after fixing the listing, platform account, or validation issue;
- `needs_user_action` jobs: retry only to regenerate an assisted package after listing changes;
- cooldown jobs: wait until the recorded `next_retry_at` time.

## Coverage

- `tests/test_api_hardening.py` covers the structured envelope and request IDs.
- `tests/test_auth_security.py` verifies rate-limit errors are marked retryable.
- `tests/test_frontend_error_ux.py` guards frontend metadata preservation and visible retry guidance.
