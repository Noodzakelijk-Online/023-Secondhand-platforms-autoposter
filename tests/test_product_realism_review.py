from pathlib import Path


def test_product_realism_review_separates_real_from_aspirational_claims():
    content = Path("docs/PRODUCT_REALISM_REVIEW.md").read_text(encoding="utf-8")

    required_phrases = [
        "Real Today",
        "Aspirational Or Not Yet Real",
        "Fully automated marketplace publishing",
        "Not real",
        "assisted listing preparation tool",
        "does not currently perform automatic marketplace submission",
    ]
    for phrase in required_phrases:
        assert phrase in content
