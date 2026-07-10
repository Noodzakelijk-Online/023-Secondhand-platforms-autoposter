from pathlib import Path


def test_repository_provenance_records_branch_remote_and_release_rules():
    text = Path("docs/REPOSITORY_PROVENANCE.md").read_text(encoding="utf-8")

    required_phrases = [
        "Local branch: `main`",
        "Remote: `origin`",
        "Baseline commit",
        "git status --short --branch",
        "python scripts/verify.py",
        "must show the intended branch",
        "no unexpected tracked changes",
        "must be refreshed if the branch, remote, or release baseline changes",
    ]

    for phrase in required_phrases:
        assert phrase in text
