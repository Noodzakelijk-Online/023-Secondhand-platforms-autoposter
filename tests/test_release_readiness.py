from pathlib import Path


def test_release_readiness_points_to_evidence_record_and_keeps_blocker_language():
    content = Path("docs/RELEASE_READINESS.md").read_text(encoding="utf-8")

    required_phrases = [
        "Status: not release-ready yet.",
        "docs/RELEASE_EVIDENCE_RECORD.md",
        "Not captured",
        "must either remain a blocker or have an explicit accepted-risk decision",
        "Completed `docs/RELEASE_EVIDENCE_RECORD.md`",
    ]
    for phrase in required_phrases:
        assert phrase in content


def test_release_evidence_record_covers_launch_critical_gates():
    content = Path("docs/RELEASE_EVIDENCE_RECORD.md").read_text(encoding="utf-8")

    required_phrases = [
        "Commit SHA deployed",
        "Deployment URL",
        "`python scripts/verify.py` output",
        "`python -m app.doctor --json` output",
        "Alembic head on target database",
        "Worker process status",
        "Edge/proxy rate-limit evidence",
        "Real non-technical user walkthrough",
        "Keyboard navigation evidence",
        "Screen-reader evidence",
        "Assisted-posting limitations accepted",
        "Remaining accepted risks",
    ]
    for phrase in required_phrases:
        assert phrase in content
