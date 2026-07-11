from pathlib import Path


def frontend_script() -> str:
    return Path("public/app.js").read_text(encoding="utf-8")


def test_frontend_centralizes_listing_review_state_resets():
    script = frontend_script()

    required_fragments = [
        "function resetListingReviewState()",
        "state.validationResults = {};",
        "state.qualityResult = null;",
        "function selectListing(listingId",
        "function markSelectedListingMutated()",
        "selectListing(null)",
        "selectListing(clone.id)",
        "markSelectedListingMutated();",
    ]
    for fragment in required_fragments:
        assert fragment in script


def test_frontend_invalidates_prepublish_state_when_platform_inputs_change():
    script = frontend_script()

    required_fragments = [
        '$(\"#platformList\").addEventListener("change"',
        '$(\"#platformList\").addEventListener("input"',
        "state.selectedPlatforms.add",
        "state.selectedPlatforms.delete",
        "resetListingReviewState();",
        "renderPrepublishReview(listing)",
        "[data-platform-description]",
    ]
    for fragment in required_fragments:
        assert fragment in script
