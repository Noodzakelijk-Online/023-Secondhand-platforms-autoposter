# Task Graph And Execution Management

This graph gives future hardening work an execution order. It prevents random polishing from outrunning release blockers.

## Execution Lanes

| Lane | Purpose | Phases | Gate |
| --- | --- | --- | --- |
| Foundation | Keep the app honest, runnable, and safe to inspect. | 0-5, 35-37, 44-49, 61-64, 78-80, 84 | `python scripts/verify.py` passes and docs stay synchronized. |
| Security And Data Control | Protect users, sessions, ownership, exports, deletion, and secrets. | 6-9, 30-32, 38-40, 68, 71-73 | No secret leakage in logs/exports; production startup fails closed. |
| Marketplace Reality | Keep platform behavior compliant and user-controlled unless official APIs are proven. | 11-20, 67, 77 | No adapter marks external success without real official API proof. |
| Product Workflow | Make the day-to-day listing workflow useful. | 10, 14, 21-29, 33-34, 57, 65-66 | Browser walkthrough proves core user flow. |
| Release Evidence | Convert local confidence into launch evidence. | 41-43, 52-56, 70, 74-76, 81, 85-88 | Fresh-clone, browser, accessibility, backup, worker, and deployment evidence captured. |
| Optional Expansion | Decide deliberately, not by drift. | 58-60 | Explicit product decision before implementation. |

## Current Critical Path

1. Finish false-completion controls: phases 80 and 84.
2. Run non-technical user simulation and product reviews: phases 74-76.
3. Execute browser/accessibility/responsive QA: phases 52-54.
4. Prove deployment-dependent items: phases 0, 4-6, 18, 70, 86.
5. Only then run final no-excuses search and final acceptance: phases 85, 87, 88.

## Rules For Future Codex Runs

- Pick the first not-started or highest-risk partial phase that can be improved with local evidence.
- Update `docs/COMPLETION_MATRIX.md`, `docs/REQUIREMENTS_TRACEABILITY.md`, and any specific evidence doc in the same change.
- Add or update tests for machine-checkable evidence.
- Do not mark deployment/browser/platform-proof phases done from local code alone.
- End each run with `python scripts/verify.py`.
