import json
import subprocess
import sys

from scripts.release_gate import release_gate_result


def test_release_gate_reports_current_external_evidence_blockers():
    result = release_gate_result()

    assert result.status == "blocked"
    assert "Release readiness still says not release-ready yet." in result.blockers
    assert "Release evidence record still has Not captured entries." in result.blockers
    assert "Non-technical user walkthrough record still has Not captured entries." in result.blockers
    assert "Final acceptance record is not accepted." in result.blockers
    assert "docs/RELEASE_EVIDENCE_RECORD.md" in result.missing_evidence
    assert result.missing_evidence_counts["docs/RELEASE_EVIDENCE_RECORD.md"] == len(
        result.missing_evidence["docs/RELEASE_EVIDENCE_RECORD.md"]
    )
    assert "Release Identity / Commit SHA deployed" in result.missing_evidence["docs/RELEASE_EVIDENCE_RECORD.md"]
    assert (
        "Deployment Evidence / Alembic head on target database"
        in result.missing_evidence["docs/RELEASE_EVIDENCE_RECORD.md"]
    )
    assert "docs/NON_TECHNICAL_USER_WALKTHROUGH_RECORD.md" in result.missing_evidence
    assert (
        "Task Results / Create a listing with title, price, condition, category, location, and description"
        in result.missing_evidence["docs/NON_TECHNICAL_USER_WALKTHROUGH_RECORD.md"]
    )
    assert "docs/FINAL_ACCEPTANCE_RECORD.md" in result.missing_evidence
    assert "Acceptance Summary / Acceptance date" in result.missing_evidence["docs/FINAL_ACCEPTANCE_RECORD.md"]
    assert result.total_missing_evidence == sum(result.missing_evidence_counts.values())
    assert result.total_missing_evidence > 0


def test_release_gate_json_cli_reports_missing_evidence():
    completed = subprocess.run(
        [sys.executable, "scripts/release_gate.py", "--json"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 1
    payload = json.loads(completed.stdout)
    assert payload["status"] == "blocked"
    assert "missing_evidence" in payload
    assert payload["missing_evidence_counts"]["docs/RELEASE_EVIDENCE_RECORD.md"] == len(
        payload["missing_evidence"]["docs/RELEASE_EVIDENCE_RECORD.md"]
    )
    assert payload["total_missing_evidence"] == sum(payload["missing_evidence_counts"].values())
    assert "Release Identity / Commit SHA deployed" in payload["missing_evidence"]["docs/RELEASE_EVIDENCE_RECORD.md"]
