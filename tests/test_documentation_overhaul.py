from pathlib import Path


def test_user_guide_covers_core_assisted_workflows_and_limits():
    content = Path("docs/USER_GUIDE.md").read_text(encoding="utf-8")

    required_phrases = [
        "Sign In And Create A Listing",
        "Improve Listing Quality",
        "Prepare Platform Packages",
        "Regenerate package",
        "Queue And Job Review",
        "Data Portability And Privacy",
        "final marketplace submission is manual",
        "Deployment-specific PostgreSQL",
    ]
    for phrase in required_phrases:
        assert phrase in content


def test_api_reference_covers_route_groups_and_error_contract():
    content = Path("docs/API_REFERENCE.md").read_text(encoding="utf-8")

    required_phrases = [
        "Error Shape",
        "`POST` | `/api/auth/login`",
        "`GET` | `/api/listings`",
        "`POST` | `/api/listings/{listing_id}/publish`",
        "`GET` | `/api/jobs`",
        "`GET` | `/api/accounts`",
        "`GET` | `/api/templates`",
        "`GET` | `/api/category-mappings`",
        "`GET` | `/api/export`",
        "Registered production platforms are assisted-only",
        "X-Total-Count",
    ]
    for phrase in required_phrases:
        assert phrase in content
