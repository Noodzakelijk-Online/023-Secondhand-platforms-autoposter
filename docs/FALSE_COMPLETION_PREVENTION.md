# False Completion Prevention

This checklist prevents the project from being described as finished, launched, fully automated, or production-ready before evidence exists.

## Claims That Must Stay Blocked

- Do not claim final release readiness while `docs/RELEASE_READINESS.md` says `Status: not release-ready yet`.
- Do not claim full automatic marketplace publishing while registered adapters remain assisted.
- Do not claim eBay official API publishing until seller policy checks, live sandbox listing proof, quota handling, and official adapter behavior are implemented and tested.
- Do not claim production readiness while the target database is behind Alembic head, production secrets are unproven, or worker status is not captured.
- Do not claim full browser/accessibility completion until `docs/BROWSER_ACCESSIBILITY_QA.md` has completed keyboard, zoom, and screen-reader evidence.
- Do not claim fresh-clone readiness until a fresh-clone dry run is documented.

## Required Before Marking Final Release

- `python scripts/verify.py` passes from a clean checkout.
- Completion matrix, traceability, task graph, and stabilization gates agree.
- Every remaining `Partial` or `Not started` phase has an accepted launch decision or is completed with evidence.
- Final no-excuses search is performed and recorded.
- `docs/FINAL_ACCEPTANCE_RECORD.md` is accepted.
- `docs/FINAL_RESPONSE_REQUIREMENTS.md` can be answered without launch blockers.
- `python scripts/final_response_check.py` reports `ready`.
- Client/user accepts assisted-posting limitations.
- Deployment evidence from `docs/RELEASE_READINESS.md` is captured.

## Wording Rules

Use:

- "assisted posting"
- "local verification passed"
- "OAuth foundation"
- "not release-ready yet"
- "requires deployment evidence"

Avoid unless evidence exists:

- "fully automated"
- "production-ready"
- "complete"
- "launched"
- "official API publishing"

## Current Status

The project is suitable for continued demo and hardening work. It is not a final client launch release.
