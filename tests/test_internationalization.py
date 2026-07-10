from pathlib import Path


def test_internationalization_doc_keeps_translation_status_honest():
    content = Path("docs/INTERNATIONALIZATION.md").read_text(encoding="utf-8")

    required_phrases = [
        "not fully translated",
        "Default locale: `en`",
        "defaulting to `en,nl`",
        "GET /api/localization",
        "Do not claim the app is multilingual",
        "English remains the fallback",
    ]
    for phrase in required_phrases:
        assert phrase in content
