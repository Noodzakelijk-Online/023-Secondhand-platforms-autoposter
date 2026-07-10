from pathlib import Path


def test_autonomy_first_design_documents_user_control_boundaries():
    content = Path("docs/AUTONOMY_FIRST_DESIGN.md").read_text(encoding="utf-8")

    required_phrases = [
        "user owns the listing data",
        "must not bypass login checks",
        "User chooses whether to apply suggestions",
        "Automatic marketplace submission",
        "eBay official API publishing",
        "explicit user-confirmed manual completion",
    ]
    for phrase in required_phrases:
        assert phrase in content
