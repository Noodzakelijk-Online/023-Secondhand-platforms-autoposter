from pathlib import Path


def test_deep_technical_audit_covers_core_review_areas_and_limits():
    content = Path("docs/DEEP_TECHNICAL_AUDIT.md").read_text(encoding="utf-8")

    required_phrases = [
        "FastAPI/static-dashboard implementation",
        "API routes and ownership checks",
        "Database models, migrations, and query helpers",
        "Authentication, sessions, throttling, and feature flags",
        "Storage and upload validation",
        "Platform adapter contract and assisted posting behavior",
        "No critical local-code blocker",
        "does not make the project release-ready",
        "PostgreSQL",
        "browser, responsive, accessibility",
        "official API publishing",
    ]
    for phrase in required_phrases:
        assert phrase in content
