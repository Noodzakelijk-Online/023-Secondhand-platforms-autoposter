from pathlib import Path


def test_false_completion_prevention_blocks_overclaims():
    content = Path("docs/FALSE_COMPLETION_PREVENTION.md").read_text(encoding="utf-8")

    required_phrases = [
        "not release-ready yet",
        "full automatic marketplace publishing",
        "eBay official API publishing",
        "fresh-clone dry run",
        "assisted-posting limitations",
        "not a final client launch release",
    ]
    for phrase in required_phrases:
        assert phrase in content
