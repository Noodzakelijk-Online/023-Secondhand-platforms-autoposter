from pathlib import Path


def test_implementation_depth_review_keeps_external_gates_explicit():
    content = Path("docs/IMPLEMENTATION_DEPTH_REVIEW.md").read_text(encoding="utf-8")

    required_phrases = [
        "Phase 81 remains partial",
        "Live PostgreSQL migrations",
        "Concurrent worker proof",
        "Deployment configuration evidence",
        "Edge/proxy rate limiting",
        "Real non-technical walkthrough",
        "keyboard, zoom, and screen-reader QA",
        "not final-launch complete",
    ]
    for phrase in required_phrases:
        assert phrase in content


def test_final_acceptance_record_blocks_launch_until_evidence_exists():
    content = Path("docs/FINAL_ACCEPTANCE_RECORD.md").read_text(encoding="utf-8")

    required_phrases = [
        "must not be marked accepted",
        "Decision | Not accepted",
        "Target database at Alembic head",
        "Edge/proxy rate limits proven",
        "Real non-technical user walkthrough",
        "Assisted-posting limitations accepted",
        "Final no-excuses search complete",
        "Status: not accepted.",
    ]
    for phrase in required_phrases:
        assert phrase in content


def test_final_response_requirements_prevent_overclaiming():
    content = Path("docs/FINAL_RESPONSE_REQUIREMENTS.md").read_text(encoding="utf-8")

    required_phrases = [
        "State the exact release commit",
        "docs/RELEASE_EVIDENCE_RECORD.md",
        "docs/FINAL_ACCEPTANCE_RECORD.md",
        "python scripts/final_response_check.py",
        "not release-ready",
        "all marketplace posting remains assisted",
        "Avoid claiming full automation",
        "not a final client launch release",
    ]
    for phrase in required_phrases:
        assert phrase in content
