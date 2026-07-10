from pathlib import Path


def test_workspaces_optional_review_defers_team_scope():
    content = Path("docs/WORKSPACES_OPTIONAL_REVIEW.md").read_text(encoding="utf-8")

    required_phrases = [
        "not part of the current release scope",
        "single-user-account scoped",
        "owner isolation",
        "WorkspaceMember",
        "cross-workspace isolation",
        "deliberately deferred",
    ]
    for phrase in required_phrases:
        assert phrase in content
