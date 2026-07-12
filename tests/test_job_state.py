from dataclasses import dataclass

import pytest

from app.services.job_state import (
    FAILED,
    NEEDS_USER_ACTION,
    PUBLISHED,
    QUEUED,
    RUNNING,
    SKIPPED,
    is_terminal_status,
    transition_job,
)


@dataclass
class FakeJob:
    status: str


def test_job_state_allows_expected_worker_flow():
    job = FakeJob(status=QUEUED)

    transition_job(job, RUNNING)
    assert job.status == RUNNING

    transition_job(job, NEEDS_USER_ACTION)
    assert job.status == NEEDS_USER_ACTION
    assert is_terminal_status(job.status)

    transition_job(job, QUEUED)
    assert job.status == QUEUED


def test_job_state_allows_user_confirmed_manual_completion():
    job = FakeJob(status=NEEDS_USER_ACTION)

    transition_job(job, PUBLISHED)

    assert job.status == PUBLISHED


def test_job_state_rejects_unknown_statuses():
    job = FakeJob(status=RUNNING)

    with pytest.raises(ValueError, match="Unknown job status"):
        transition_job(job, "mystery")


def test_job_state_rejects_invalid_transition():
    job = FakeJob(status=QUEUED)

    with pytest.raises(ValueError, match="Invalid job status transition"):
        transition_job(job, PUBLISHED)


def test_job_state_terminal_statuses_are_explicit():
    assert is_terminal_status(PUBLISHED)
    assert is_terminal_status(FAILED)
    assert is_terminal_status(NEEDS_USER_ACTION)
    assert is_terminal_status(SKIPPED)
    assert not is_terminal_status(QUEUED)
    assert not is_terminal_status(RUNNING)
