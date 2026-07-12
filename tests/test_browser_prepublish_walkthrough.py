import json
from pathlib import Path


def test_browser_prepublish_walkthrough_evidence_is_recorded():
    report = Path("docs/BROWSER_PREPUBLISH_WALKTHROUGH.md").read_text(encoding="utf-8")
    evidence_path = Path("docs/browser-evidence/prepublish-walkthrough.json")
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))

    required_phrases = [
        "executed browser evidence",
        "Playwright Chromium",
        "prepublish review",
        "20 field-copy controls",
        "does not close the broader browser/accessibility/responsive launch gate",
    ]
    for phrase in required_phrases:
        assert phrase in report

    assert evidence["browser"] == "chromium"
    assert evidence["baseUrl"] == "http://127.0.0.1:8000"
    assert "validation populates ready state and mapped category" in evidence["assertions"]
    assert {item["viewport"] for item in evidence["results"]} == {"desktop", "mobile"}
    for item in evidence["results"]:
        assert item["prepublishVisible"] is True
        assert item["copyButtons"] == 20
        assert item["packageButtons"] == 1
        assert Path(item["screenshot"]).is_file()
