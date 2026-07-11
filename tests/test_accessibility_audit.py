from html.parser import HTMLParser
from pathlib import Path

CONTROL_TAGS = {"input", "select", "textarea"}
IGNORED_INPUT_TYPES = {"hidden"}


class AccessibilityParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.label_depth = 0
        self.controls: list[dict[str, str | bool]] = []
        self.buttons: list[dict[str, str | bool]] = []
        self.images: list[dict[str, str]] = []
        self.landmarks: list[str] = []
        self.headings: list[str] = []
        self.live_regions: list[str] = []
        self._button_stack: list[dict[str, str | bool]] = []
        self._heading_stack: list[list[str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {name: value or "" for name, value in attrs}
        if tag == "label":
            self.label_depth += 1
        if tag in CONTROL_TAGS:
            input_type = attrs_dict.get("type", "")
            if tag != "input" or input_type not in IGNORED_INPUT_TYPES:
                self.controls.append(
                    {
                        "tag": tag,
                        "id": attrs_dict.get("id", attrs_dict.get("name", "")),
                        "has_label": self.label_depth > 0
                        or bool(attrs_dict.get("aria-label"))
                        or bool(attrs_dict.get("aria-labelledby")),
                    }
                )
        if tag == "button":
            button = {
                "id": attrs_dict.get("id", ""),
                "has_name": bool(attrs_dict.get("aria-label")),
                "text": "",
            }
            self.buttons.append(button)
            self._button_stack.append(button)
        if tag == "img":
            self.images.append({"src": attrs_dict.get("src", ""), "alt": attrs_dict.get("alt", "")})
        if tag in {"main", "nav", "aside"}:
            self.landmarks.append(tag)
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._heading_stack.append([tag, ""])
        if attrs_dict.get("role") in {"status", "alert"} or attrs_dict.get("aria-live"):
            self.live_regions.append(attrs_dict.get("id", tag))

    def handle_data(self, data: str) -> None:
        if self._button_stack:
            self._button_stack[-1]["text"] = str(self._button_stack[-1]["text"]) + data
        if self._heading_stack:
            self._heading_stack[-1][1] += data

    def handle_endtag(self, tag: str) -> None:
        if tag == "label" and self.label_depth:
            self.label_depth -= 1
        if tag == "button" and self._button_stack:
            button = self._button_stack.pop()
            button["has_name"] = bool(button["has_name"]) or bool(str(button["text"]).strip())
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"} and self._heading_stack:
            heading_tag, text = self._heading_stack.pop()
            if heading_tag == tag and text.strip():
                self.headings.append(f"{heading_tag}:{text.strip()}")


def parse_index() -> AccessibilityParser:
    parser = AccessibilityParser()
    parser.feed(Path("public/index.html").read_text(encoding="utf-8"))
    return parser


def test_static_forms_have_accessible_labels():
    parser = parse_index()

    unlabeled = [control for control in parser.controls if not control["has_label"]]

    assert unlabeled == []


def test_static_buttons_images_and_status_regions_are_accessible():
    parser = parse_index()

    unnamed_buttons = [button["id"] or button["text"] for button in parser.buttons if not button["has_name"]]
    images_without_alt = [image["src"] for image in parser.images if "alt" not in image or image["alt"] == ""]

    assert unnamed_buttons == []
    assert images_without_alt == []
    assert "main" in parser.landmarks
    assert "nav" in parser.landmarks
    assert any(heading.startswith("h1:") for heading in parser.headings)
    assert "appMessage" in parser.live_regions
