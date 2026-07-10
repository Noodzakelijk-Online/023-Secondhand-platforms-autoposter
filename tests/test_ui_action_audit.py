from pathlib import Path


def test_ui_action_audit_covers_visible_workflows_and_limits():
    content = Path("docs/UI_ACTION_AUDIT.md").read_text(encoding="utf-8")

    required_phrases = [
        "Sign in",
        "New listing",
        "Run quality check",
        "Upload images",
        "Validate platforms",
        "Queue publish",
        "Retry job",
        "Save account",
        "Export JSON",
        "Delete my account data",
        "not an executed browser walkthrough",
    ]
    for phrase in required_phrases:
        assert phrase in content
