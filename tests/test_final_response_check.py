import json
import subprocess
import sys

from scripts.final_response_check import final_response_check_result


def test_final_response_check_blocks_unsafe_final_release_answer():
    result = final_response_check_result()

    assert result.status == "blocked"
    assert "Final response requirements say the final release response is not ready." in result.blockers
    assert "Final acceptance record is not accepted." in result.blockers
    assert "Release gate is not ready." in result.blockers
    assert result.release_gate_status == "blocked"
    assert result.total_missing_evidence > 0
    assert "exact release commit" in result.required_statements
    assert "assisted marketplace posting unless official API publishing evidence exists" in result.required_statements


def test_final_response_check_json_cli_reports_blockers_and_required_statements():
    completed = subprocess.run(
        [sys.executable, "scripts/final_response_check.py", "--json"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 1
    payload = json.loads(completed.stdout)
    assert payload["status"] == "blocked"
    assert "Release gate is not ready." in payload["blockers"]
    assert payload["release_gate_status"] == "blocked"
    assert payload["total_missing_evidence"] > 0
    assert "remaining launch blockers" in payload["required_statements"]
