import sys
from pathlib import Path


def test_web_app_does_not_import_legacy_browser_stack():
    import app.main  # noqa: F401

    forbidden_modules = ["selenium", "lastpass", "spacy", "decouple"]
    loaded = [module for module in forbidden_modules if module in sys.modules]

    assert loaded == []


def test_legacy_browser_scripts_are_not_at_repository_root():
    root = Path(__file__).resolve().parent.parent
    legacy_files = [
        "main.py",
        "markplaats.py",
        "nlp_hanlder.py",
        "post_ebay.py",
        "post_koopplein.py",
        "post_nextdoor.py",
        "scrape_second_hand.py",
        "test.py",
        "setup.sh",
        "start.desktop",
        "stop.desktop",
        "stop.sh",
        "main.spec",
    ]

    for filename in legacy_files:
        assert not (root / filename).exists()
        assert (root / "legacy" / "selenium" / filename).exists()


def test_duplicate_old_source_tree_is_archived():
    root = Path(__file__).resolve().parent.parent

    assert not (root / "023-Secondhand-platforms-autoposter-main").exists()
    assert (root / "legacy" / "archive" / "023-Secondhand-platforms-autoposter-main").is_dir()
