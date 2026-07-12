from pathlib import Path


def test_frontend_product_completion_records_surface_and_browser_evidence():
    content = Path("docs/FRONTEND_PRODUCT_COMPLETION.md").read_text(encoding="utf-8")

    required_phrases = [
        "authentication and session boot",
        "listing creation, editing, duplication, deletion, image upload, and image ordering",
        "deterministic quality assistant",
        "prepublish review",
        "user-confirmed manual completion",
        "JSON/CSV/image export",
        "English/Dutch shell localization",
        "docs/BROWSER_E2E_WORKFLOW.md",
        "docs/BROWSER_PREPUBLISH_WALKTHROUGH.md",
        "docs/BROWSER_ERROR_UX_WALKTHROUGH.md",
        "does not close the full launch browser QA gate",
    ]
    for phrase in required_phrases:
        assert phrase in content
