# Technical Debt Register

This register tracks known debt that remains after the current implementation slices. It is intentionally concrete: each item has an owner area, severity, related PDF phase, and next action.

| ID | Severity | Area | Related phase | Debt | Next action |
| --- | --- | --- | --- | --- | --- |
| TD-001 | Medium | Auth/session security | 6, 32 | Bearer-only auth, CSRF posture, and database-backed login throttling are documented and tested, but deployment-edge limits are not proven. | Add proxy/WAF or platform-level rate-limit evidence before multi-instance production deployment. |
| TD-002 | High | Platform integrations | 16 | eBay OAuth consent, token exchange, refresh, secret-store, sandbox Inventory API probe, and quota backoff foundations exist, but no official listing adapter or live sandbox listing proof exists. | Add seller policy checks, live sandbox listing proof, and official publish adapter behavior before any production automation. |
| TD-003 | Medium | Job processing | 18, 20 | Worker now uses atomic due-job claims and stale-running recovery with tests, but production database-specific locking verification is still incomplete. | Verify claim and recovery behavior against PostgreSQL under concurrent workers. |
| TD-004 | Low | Data deletion/privacy | 30 | Export/import/delete and portability actions write sanitized audit events with a user privacy activity review and retention purge; no cross-user admin console exists. | Add a role-based admin console only if future workspace/operator requirements need cross-user review. |
| TD-005 | Medium | File storage | 9 | Local image storage is hardened, but no S3/object-storage adapter exists. | Add storage backend interface config, S3-compatible implementation, and migration notes. |
| TD-006 | Medium | Frontend product depth | 23, 34, 66 | UI covers core flows, diagnostics, structured error banners, retry guidance, prepublish review, copy-ready mapped fields, and focused validation recovery, but executed browser evidence is still shallow. | Run browser/accessibility walkthroughs for error, retry, prepublish, mobile, and keyboard flows. |
| TD-007 | Low | API route coverage | 25, 41 | Route usage is documented and owner isolation has direct regression coverage; remaining gaps are mostly future UI controls and browser-level coverage. | Keep `docs/API_USAGE_AUDIT.md` and browser tests aligned as new routes or controls are added. |
| TD-008 | Low | Templates/productivity | 26 | Template variants are implemented across API, UI, export/import, and tests; future productivity automation helpers remain optional. | Add workflow automation helpers only after observing repeated seller workflows. |
| TD-009 | Medium | Type checking | 44 | Ruff, CI verification, and dependency audit exist; no type-checking gate exists yet. | Add a mypy/pyright decision and targeted typing fixes before enabling a type-check gate. |
| TD-010 | Medium | Backups/restore | 55, 72 | Export/import is user-facing portability, not an operator backup/restore strategy. | Add database backup/restore runbook and reconciliation checks. |
| TD-011 | Low | Observability | 56, 73 | Request/job logging, JSON/text formatting, and lightweight JSON metrics exist; no Prometheus exporter is included. | Add Prometheus/OpenTelemetry only if the deployment target requires it. |
| TD-012 | Medium | Accessibility/browser QA | 52, 54 | Automated static accessibility smoke checks exist, but executed browser, keyboard, zoom, and responsive walkthrough evidence is not captured. | Run the checklist in `docs/BROWSER_ACCESSIBILITY_QA.md` and capture findings. |
| TD-013 | Low | Legacy scripts | 17 | Legacy runtime scripts and the duplicate old source tree are separated from the app root. | Keep the archive only while it has reference value; remove it later by explicit product decision. |
| TD-014 | Low | Internationalization | 60 | UI text is English-only and hardcoded. | Add copy catalog decision once product language requirements are settled. |
| TD-015 | Low | Release evidence | 70, 84, 85, 87, 88 | Local and fresh-clone verification reports exist, but browser evidence and deployment-specific launch evidence are not complete. | Capture production-target launch evidence when environment details are available. |
| TD-016 | Low | Listing quality | 27 | The listing quality assistant has local category-specific heuristics for common categories, but does not use external AI or marketplace-specific search data. | Expand heuristics from real seller outcomes; add optional AI only after privacy, cost, and prompt-safety requirements are defined. |

## Maintenance Rules

- Add an item when a known limitation remains after a phase is marked partial or done.
- Close an item only when code, tests, and docs make the debt materially resolved.
- Keep IDs stable so future commits and reports can reference them.
