from pathlib import Path


def test_frontend_exposes_explicit_regenerate_package_action():
    html = Path("public/index.html").read_text(encoding="utf-8")
    script = Path("public/app.js").read_text(encoding="utf-8")

    assert 'id="regeneratePackageButton"' in html
    assert "Regenerate package" in html
    assert "force_new_revision" in script
    assert "Fresh assisted package queued" in script
    assert "queueAssistedPackage({ forceNewRevision: true })" in script
