# Browser End-To-End Workflow

This report captures executed Chromium evidence for a real dashboard workflow.

## Run

- Date: 2026-07-12.
- Commit under test: local working tree after `0d9a913`.
- URL: `http://127.0.0.1:8000`.
- Browser: Playwright Chromium 1.61.1.
- Command:

```powershell
$env:NODE_PATH=(Resolve-Path .tmp\playwright-runner\node_modules); node scripts\browser_e2e_workflow.cjs
```

## Scenario

The script drove the real UI through:

1. fresh user registration;
2. listing creation and save;
3. image upload;
4. Marktplaats validation and prepublish review;
5. assisted job queueing;
6. user-confirmed manual completion;
7. JSON export download;
8. account deletion and return to the auth view.

## Evidence

- Machine-readable result: `docs/browser-evidence/e2e-workflow.json`.
- Export downloaded by the browser: `docs/browser-evidence/e2e-export.json`.
- Final screenshot after account deletion: `docs/browser-evidence/e2e-final-auth.png`.

The final run exported one listing titled `Browser E2E oak lamp` and returned to the auth view after deletion.

## Scope Boundary

This closes the browser E2E evidence gap for Phase 43. It does not replace external non-technical user observation, target deployment evidence, or the full browser/accessibility/responsive launch checklist.
