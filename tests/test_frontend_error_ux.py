from pathlib import Path


def frontend_source() -> str:
    return "\n".join(
        [
            Path("public/app.js").read_text(encoding="utf-8"),
            Path("public/styles.css").read_text(encoding="utf-8"),
        ]
    )


def test_frontend_preserves_structured_api_error_metadata():
    content = frontend_source()

    required_fragments = [
        "class ApiError extends Error",
        "request_id",
        "field_errors",
        "retryable",
        "Request ID:",
        "You can retry this request.",
        "showAppError",
    ]
    for fragment in required_fragments:
        assert fragment in content


def test_frontend_explains_job_retry_behavior():
    content = frontend_source()

    required_fragments = [
        "jobRetryGuidance",
        "Retry after fixing the listing",
        "regenerate the assisted package",
        "waiting for its cooldown",
        "retry-guidance",
    ]
    for fragment in required_fragments:
        assert fragment in content
