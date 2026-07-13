from pathlib import Path


def test_non_technical_user_simulation_requires_real_user_evidence():
    content = Path("docs/NON_TECHNICAL_USER_SIMULATION.md").read_text(encoding="utf-8")

    required_phrases = [
        "proxy simulation",
        "not a substitute for observing a real non-technical user",
        "docs/NON_TECHNICAL_USER_WALKTHROUGH_RECORD.md",
        "Queue assisted package",
        "understandable without implying automatic marketplace submission",
        "real non-technical user walkthrough must be executed",
        "remains partial until external user evidence exists",
    ]
    for phrase in required_phrases:
        assert phrase in content


def test_non_technical_user_walkthrough_record_captures_required_observations():
    content = Path("docs/NON_TECHNICAL_USER_WALKTHROUGH_RECORD.md").read_text(encoding="utf-8")

    required_phrases = [
        "not a proxy simulation",
        "Walkthrough date",
        "Browser and version",
        "Completed without coaching",
        "Queue assisted package",
        "understand `needs_user_action`",
        "assisted posting does not mean automatic marketplace submission",
        "final marketplace posting remains manual",
        "Confusion points",
        "UI copy changes made afterward",
        "Final acceptance decision",
        "Not captured",
    ]
    for phrase in required_phrases:
        assert phrase in content
