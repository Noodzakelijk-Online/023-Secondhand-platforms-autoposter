from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path

CONTROL_TAGS = {"input", "select", "textarea"}


@dataclass(frozen=True)
class UiViolation:
    code: str
    message: str


@dataclass
class Control:
    tag: str
    attrs: dict[str, str]
    nested_label: bool


@dataclass
class Button:
    attrs: dict[str, str]
    text: list[str] = field(default_factory=list)


class StaticUiParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.controls: list[Control] = []
        self.buttons: list[Button] = []
        self.images: list[dict[str, str]] = []
        self.labels_for: set[str] = set()
        self.has_main = False
        self.has_nav = False
        self.title_text: list[str] = []
        self.html_attrs: dict[str, str] = {}
        self._label_depth = 0
        self._title_depth = 0
        self._button_stack: list[Button] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        normalized = {key: value or "" for key, value in attrs}
        if tag == "html":
            self.html_attrs = normalized
        if tag == "main":
            self.has_main = True
        if tag == "nav":
            self.has_nav = True
        if tag == "title":
            self._title_depth += 1
        if tag == "label":
            self._label_depth += 1
            if normalized.get("for"):
                self.labels_for.add(normalized["for"])
        if tag in CONTROL_TAGS:
            self.controls.append(Control(tag=tag, attrs=normalized, nested_label=self._label_depth > 0))
        if tag == "button":
            button = Button(attrs=normalized)
            self.buttons.append(button)
            self._button_stack.append(button)
        if tag == "img":
            self.images.append(normalized)

    def handle_endtag(self, tag: str) -> None:
        if tag == "label":
            self._label_depth = max(0, self._label_depth - 1)
        if tag == "title":
            self._title_depth = max(0, self._title_depth - 1)
        if tag == "button" and self._button_stack:
            self._button_stack.pop()

    def handle_data(self, data: str) -> None:
        if self._title_depth:
            self.title_text.append(data)
        for button in self._button_stack:
            button.text.append(data)


def _has_accessible_name(control: Control, labels_for: set[str]) -> bool:
    attrs = control.attrs
    if attrs.get("type") == "hidden":
        return True
    return bool(
        control.nested_label
        or attrs.get("aria-label", "").strip()
        or attrs.get("aria-labelledby", "").strip()
        or (attrs.get("id") and attrs["id"] in labels_for)
    )


def audit_static_ui(root: Path) -> list[UiViolation]:
    index_path = root / "public" / "index.html"
    app_path = root / "public" / "app.js"
    html = index_path.read_text(encoding="utf-8")
    js = app_path.read_text(encoding="utf-8")

    parser = StaticUiParser()
    parser.feed(html)

    violations: list[UiViolation] = []
    if not parser.html_attrs.get("lang"):
        violations.append(UiViolation("html-lang", "The HTML document must declare a language."))
    if not "".join(parser.title_text).strip():
        violations.append(UiViolation("document-title", "The HTML document must have a non-empty title."))
    if not parser.has_main:
        violations.append(UiViolation("main-landmark", "The authenticated app shell must expose a main landmark."))
    if not parser.has_nav:
        violations.append(UiViolation("nav-landmark", "The app shell must expose a navigation landmark."))

    for control in parser.controls:
        if not _has_accessible_name(control, parser.labels_for):
            identifier = control.attrs.get("id") or control.attrs.get("name") or control.tag
            violations.append(UiViolation("control-name", f"{control.tag} `{identifier}` needs an accessible name."))

    for button in parser.buttons:
        text = " ".join(part.strip() for part in button.text).strip()
        if not text and not button.attrs.get("aria-label", "").strip():
            identifier = button.attrs.get("id") or button.attrs.get("class") or "button"
            violations.append(UiViolation("button-name", f"Button `{identifier}` needs visible text or aria-label."))

    for image in parser.images:
        if "alt" not in image:
            src = image.get("src", "img")
            violations.append(UiViolation("image-alt", f"Image `{src}` needs alt text."))

    if "<img" in js and not re.search(r"<img[^>]+alt=", js):
        violations.append(UiViolation("dynamic-image-alt", "Dynamic image templates must include alt text."))
    if re.search(r'tabindex=["\'][1-9]', html + js):
        violations.append(UiViolation("positive-tabindex", "Positive tabindex values are not allowed."))
    if "aria-live" not in html:
        violations.append(UiViolation("live-region", "The app should expose a live region for async messages."))
    if "Manual completion" in js and "Final platform URL" not in js:
        violations.append(
            UiViolation("manual-completion-label", "Manual completion form needs a labelled final URL input.")
        )

    return violations


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    violations = audit_static_ui(root)
    if violations:
        for violation in violations:
            print(f"{violation.code}: {violation.message}", file=sys.stderr)
        return 1
    print("Static UI accessibility audit passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
