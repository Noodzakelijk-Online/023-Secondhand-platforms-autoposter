from pathlib import Path


def test_ui_ux_debugging_rounds_record_executed_browser_evidence_and_limits():
    content = Path("docs/UI_UX_DEBUGGING_ROUNDS.md").read_text(encoding="utf-8")

    required_phrases = [
        "Prepublish review",
        "Error and recovery UX",
        "Seller workflow",
        "validating a selected Marktplaats card expanded the review to all platform adapters",
        "scopes validation requests to selected platforms",
        "completed without a blocking UI issue",
        "does not close Phase 54 or release readiness",
        "keyboard navigation, screen-reader/zoom checks",
    ]
    for phrase in required_phrases:
        assert phrase in content
