from datetime import UTC, datetime

from app.services.platform_rate_limits import quota_retry_at_from_headers, quota_retry_at_from_outcome


def test_retry_after_seconds_sets_quota_retry_time():
    now = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)

    retry_at = quota_retry_at_from_headers({"Retry-After": "90"}, http_status=429, now=now)

    assert retry_at == datetime(2026, 1, 1, 12, 1, 30, tzinfo=UTC)


def test_reset_header_requires_exhausted_quota_or_429():
    now = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)

    assert (
        quota_retry_at_from_headers({"X-RateLimit-Remaining": "1", "X-RateLimit-Reset": "120"}, now=now)
        is None
    )
    retry_at = quota_retry_at_from_headers(
        {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "120"},
        now=now,
    )

    assert retry_at == datetime(2026, 1, 1, 12, 2, tzinfo=UTC)


def test_outcome_quota_headers_support_common_response_keys():
    now = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)

    retry_at = quota_retry_at_from_outcome(
        {"http_status": 429, "response_headers": {"RateLimit-Reset": "45"}},
        now=now,
    )

    assert retry_at == datetime(2026, 1, 1, 12, 0, 45, tzinfo=UTC)
