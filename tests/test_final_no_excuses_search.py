from pathlib import Path


def test_final_no_excuses_search_is_marked_pre_final_until_release_evidence_exists():
    content = Path("docs/FINAL_NO_EXCUSES_SEARCH.md").read_text(encoding="utf-8")

    required_phrases = [
        "pre-final search",
        "not the final release search",
        "not release-ready",
        "Real non-technical user walkthrough is not executed",
        "Fresh-clone dry run is not documented as final",
        "remains partial",
    ]
    for phrase in required_phrases:
        assert phrase in content
