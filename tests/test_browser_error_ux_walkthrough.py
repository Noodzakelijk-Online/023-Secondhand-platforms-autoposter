import json
from pathlib import Path


def test_browser_error_ux_walkthrough_evidence_is_recorded():
    report = Path("docs/BROWSER_ERROR_UX_WALKTHROUGH.md").read_text(encoding="utf-8")
    evidence = json.loads(Path("docs/browser-evidence/error-ux-walkthrough.json").read_text(encoding="utf-8"))

    required_phrases = [
        "executed browser evidence",
        "invalid login shows an inline auth error",
        "validation of an incomplete Marktplaats package shows missing fields",
        "failed assisted job shows retry guidance",
        "invalid JSON import shows a visible import error",
        "does not close the broader browser/accessibility/responsive launch gate",
    ]
    for phrase in required_phrases:
        assert phrase in report

    assert evidence["browser"] == "chromium"
    assert "invalid login shows inline auth error" in evidence["assertions"]
    assert evidence["recoveryButtons"] >= 1
    assert evidence["focusedAfterRecovery"]
    assert "Retry after fixing" in evidence["retryGuidance"]
    assert "JSON" in evidence["importError"]
    assert Path(evidence["screenshot"]).is_file()
