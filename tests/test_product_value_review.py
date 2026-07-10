from pathlib import Path


def test_product_value_review_states_value_and_limits():
    content = Path("docs/PRODUCT_VALUE_REVIEW.md").read_text(encoding="utf-8")

    required_phrases = [
        "non-technical secondhand seller",
        "Current Value Delivered",
        "final marketplace submission remains manual",
        "credible demo value",
        "not yet a final launch product",
        "user-confirmed manual completion",
    ]
    for phrase in required_phrases:
        assert phrase in content
