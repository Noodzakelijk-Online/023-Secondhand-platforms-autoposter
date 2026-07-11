# Accessibility Audit

Date: 2026-07-12

Commit baseline: `1306d33`

## Automated Static Smoke Coverage

The repository now includes `tests/test_accessibility_audit.py` for source-level accessibility checks on `public/index.html`.

The test verifies:

- form controls have an enclosing label, `aria-label`, or `aria-labelledby`;
- static buttons have visible text or an ARIA label;
- static images provide `alt` text;
- the app shell includes core landmarks such as `main` and `nav`;
- the page has a top-level heading;
- the global app message area is exposed as a live status region.

## Finding Fixed

The listing image upload input was visible beside the Images heading but did not have its own accessible label. It is now wrapped in an `Upload image` label.

## Scope

This closes the automated accessibility smoke-evidence gap for the static dashboard source. It does not replace the manual browser, keyboard, screen-reader, zoom, responsive, and cross-browser walkthroughs in `docs/BROWSER_ACCESSIBILITY_QA.md`.
