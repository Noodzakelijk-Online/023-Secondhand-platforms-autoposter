import json
from pathlib import Path


def test_browser_e2e_workflow_evidence_is_recorded():
    report = Path("docs/BROWSER_E2E_WORKFLOW.md").read_text(encoding="utf-8")
    evidence = json.loads(Path("docs/browser-evidence/e2e-workflow.json").read_text(encoding="utf-8"))
    export = json.loads(Path("docs/browser-evidence/e2e-export.json").read_text(encoding="utf-8"))

    required_phrases = [
        "executed Chromium evidence",
        "fresh user registration",
        "listing creation and save",
        "user-confirmed manual completion",
        "JSON export download",
        "account deletion and return to the auth view",
    ]
    for phrase in required_phrases:
        assert phrase in report

    assert evidence["browser"] == "chromium"
    assert evidence["exportedListings"] == 1
    assert evidence["exportedTitle"] == "Browser E2E oak lamp"
    assert "account deletion returns to the auth view" in evidence["assertions"]
    assert Path(evidence["screenshot"]).is_file()
    assert Path(evidence["download"]).is_file()
    assert export["listings"][0]["title"] == "Browser E2E oak lamp"
