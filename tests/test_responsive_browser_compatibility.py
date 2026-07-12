import json
from pathlib import Path


def test_responsive_browser_compatibility_evidence_is_recorded():
    report = Path("docs/RESPONSIVE_BROWSER_COMPATIBILITY.md").read_text(encoding="utf-8")
    evidence = json.loads(Path("docs/browser-evidence/responsive-matrix.json").read_text(encoding="utf-8"))

    required_phrases = [
        "Chromium, Firefox, WebKit",
        "mobile: 390 x 844",
        "tablet: 768 x 1024",
        "document and body width within the viewport width",
        "cramped navigation labels",
        "12 passing browser/viewport records",
        "does not close release readiness",
    ]
    for phrase in required_phrases:
        assert phrase in report

    assert evidence["browsers"] == ["chromium", "firefox", "webkit"]
    assert {item["name"] for item in evidence["viewports"]} == {"mobile", "tablet", "laptop", "desktop"}
    assert len(evidence["results"]) == 12
    for result in evidence["results"]:
        assert Path(result["screenshot"]).is_file()
        for metrics in result["viewMetrics"].values():
            assert metrics["documentWidth"] <= metrics["innerWidth"]
            assert metrics["bodyWidth"] <= metrics["innerWidth"]
