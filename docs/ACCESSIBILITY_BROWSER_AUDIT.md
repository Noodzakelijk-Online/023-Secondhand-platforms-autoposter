# Accessibility And Browser Audit

Audit date: 2026-07-04.

## Automated Static Audit

Run:

```bash
python scripts/audit_static_ui.py
```

The audit parses `public/index.html` and checks the static app shell for:

- document language and title
- `main` and `nav` landmarks
- labelled inputs, selects, and textareas
- named buttons
- image `alt` attributes, including dynamic image-template coverage in `public/app.js`
- absence of positive `tabindex`
- an async message live region
- labelled manual-completion final URL input

The audit is also covered by `tests/test_static_ui_audit.py`, so `python scripts/verify.py` runs it through the pytest suite.

## Finding Fixed

The image upload file input was visually grouped under the Images heading but had no programmatic label. It is now wrapped in a labelled `Upload image` control.

## Remaining Browser Work

This audit does not prove visual layout, keyboard traversal order, color contrast, responsive breakpoints, focus rings, or cross-browser behavior. Those still require a browser E2E/accessibility pass with a tool such as Playwright plus axe or an equivalent manual assistive-technology checklist.

Status: Partial. Static accessibility baseline is automated; real browser E2E and manual accessibility signoff remain open.
