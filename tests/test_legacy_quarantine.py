import sys


def test_web_app_does_not_import_legacy_browser_stack():
    import app.main  # noqa: F401

    forbidden_modules = ["selenium", "lastpass", "spacy", "decouple"]
    loaded = [module for module in forbidden_modules if module in sys.modules]

    assert loaded == []
