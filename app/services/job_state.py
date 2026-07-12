from __future__ import annotations

from typing import Protocol


class JobLike(Protocol):
    status: str


QUEUED = "queued"
RUNNING = "running"
PUBLISHED = "published"
FAILED = "failed"
NEEDS_USER_ACTION = "needs_user_action"
SKIPPED = "skipped"

VALID_JOB_STATUSES = frozenset(
    {
        QUEUED,
        RUNNING,
        PUBLISHED,
        FAILED,
        NEEDS_USER_ACTION,
        SKIPPED,
    }
)
TERMINAL_JOB_STATUSES = frozenset({PUBLISHED, FAILED, NEEDS_USER_ACTION, SKIPPED})
ACTIVE_IDEMPOTENCY_STATUSES = (QUEUED, RUNNING, PUBLISHED, NEEDS_USER_ACTION)

ALLOWED_JOB_TRANSITIONS = {
    QUEUED: frozenset({QUEUED, RUNNING, FAILED}),
    RUNNING: frozenset({PUBLISHED, FAILED, NEEDS_USER_ACTION, SKIPPED, QUEUED}),
    FAILED: frozenset({QUEUED, RUNNING}),
    NEEDS_USER_ACTION: frozenset({QUEUED, PUBLISHED}),
    PUBLISHED: frozenset({QUEUED}),
    SKIPPED: frozenset({QUEUED}),
}


def is_terminal_status(status: str) -> bool:
    return status in TERMINAL_JOB_STATUSES


def transition_job(job: JobLike, new_status: str) -> None:
    if new_status not in VALID_JOB_STATUSES:
        raise ValueError(f"Unknown job status: {new_status}")
    current_status = job.status
    allowed = ALLOWED_JOB_TRANSITIONS.get(current_status)
    if allowed is None:
        raise ValueError(f"Unknown current job status: {current_status}")
    if new_status not in allowed:
        raise ValueError(f"Invalid job status transition: {current_status} -> {new_status}")
    job.status = new_status
