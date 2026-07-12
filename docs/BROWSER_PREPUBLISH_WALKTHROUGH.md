# Browser Prepublish Walkthrough

This report captures executed browser evidence for the prepublish safety review.

## Run

- Date: 2026-07-12.
- Commit under test: local working tree after `fbe19aa`.
- URL: `http://127.0.0.1:8000`.
- Browser: Playwright Chromium 1.61.1.
- Command:

```powershell
$env:NODE_PATH=(Resolve-Path .tmp\playwright-runner\node_modules); node scripts\browser_prepublish_walkthrough.cjs
```

## Scenario

The script registered a fresh seller, created a complete listing with one image, added a Marktplaats category mapping, opened the real dashboard in Chromium, selected the listing from the Listings view, selected Marktplaats, ran validation, and asserted that the prepublish review showed:

- a visible ready review card;
- the mapped category `Huis en Inrichting`;
- the open-platform link;
- copy-ready field buttons;
- a package copy button.

## Evidence

- Machine-readable result: `docs/browser-evidence/prepublish-walkthrough.json`.
- Desktop screenshot: `docs/browser-evidence/prepublish-desktop.png`.
- Mobile screenshot: `docs/browser-evidence/prepublish-mobile.png`.

The final run captured one Marktplaats review card with 20 field-copy controls and one package-copy control at both 1440 x 1000 and 390 x 844.

## Scope Boundary

This closes the executed browser evidence gap for Phase 66, Prepublish Safety Review. It does not close the broader browser/accessibility/responsive launch gate, because that still requires the full checklist in `docs/BROWSER_ACCESSIBILITY_QA.md` across the release browser matrix.
