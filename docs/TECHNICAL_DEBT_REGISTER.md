# Technical Debt Register

This register tracks known debt that remains after the current implementation slices. It is intentionally concrete: each item has an owner area, severity, related PDF phase, and next action.

| ID | Severity | Area | Related phase | Debt | Next action |
| --- | --- | --- | --- | --- | --- |
| TD-001 | High | Auth/session security | 6, 32 | Bearer-token auth works, but cookie mode, CSRF posture, and distributed rate limiting are not complete. | Decide cookie vs bearer deployment mode, then add CSRF/cookie hardening or documented bearer-only deployment controls. |
| TD-002 | High | Platform integrations | 16, 68 | eBay official API/OAuth foundations are not implemented; the credential checklist exists and raw secrets are rejected from account metadata, but no OAuth flow or secret-manager reference model exists. | Add OAuth config model, callback flow, token reference strategy, and sandbox-only tests before any production automation. |
| TD-003 | High | Job processing | 18, 20 | Worker is database-backed, but lacks row-level locking and multi-worker concurrency tests. | Add claim/lock semantics and tests that simulate concurrent workers. |
| TD-004 | Medium | Data deletion/privacy | 30 | Export/import, self-service account deletion, raw secret rejection, and summary audit events exist; formal retention/privacy impact review is still incomplete. | Add privacy impact assessment, retention policy, and admin/operator review guidance. |
| TD-005 | Medium | File storage | 9 | Local image storage is hardened, but no S3/object-storage adapter exists. | Add storage backend interface config, S3-compatible implementation, and migration notes. |
| TD-006 | Medium | Frontend product depth | 23, 34, 66 | UI covers core flows, but diagnostics, prepublish safety checklist, richer manual posting package views, and field-level recovery are shallow. | Add diagnostics/about panel and a prepublish review panel with copy-ready mapped fields. |
| TD-007 | Medium | API route coverage | 7, 25, 41 | Several endpoints are documented but lack direct tests or frontend controls. | Work through `docs/API_USAGE_AUDIT.md` follow-ups route by route. |
| TD-008 | Medium | Templates/productivity | 26 | Templates can be saved but not applied to listings or managed as variants. | Add apply-template action, edit/delete template flows, and tests. |
| TD-009 | Medium | Type checking | 44 | Ruff, CI verification, and dependency audit exist; no type-checking gate exists yet. | Add a mypy/pyright decision and targeted typing fixes before enabling a type-check gate. |
| TD-010 | Medium | Backups/restore | 55, 72 | Local SQLite/upload backup and restore scripts exist with guardrails, but production PostgreSQL/object-storage backups are not tested. | Run provider-native backup/restore drills once hosting, object storage, retention, and encryption custody are approved. |
| TD-011 | Medium | Observability | 56, 73 | Job logs, diagnostics, support bundles, audit events, and runbook exist, but app-level structured logging and metrics are incomplete. | Add logging config and metrics decision. |
| TD-012 | Medium | Accessibility/browser QA | 52, 53, 54 | Basic semantic HTML exists, but there is no browser/a11y audit report. | Add manual QA checklist and automated accessibility smoke checks. |
| TD-013 | Low | Legacy scripts | 17 | Legacy scripts are quarantined by docs/guards, but not physically separated from the main root. | Move legacy scripts into a clearly marked folder after confirming user workflows. |
| TD-014 | Low | Internationalization | 60 | UI text is English-only and hardcoded. | Add copy catalog decision once product language requirements are settled. |
| TD-015 | Low | Release evidence | 48, 70, 84, 85, 86, 87, 88 | Final verification, fresh-clone dry run, and release checklist are not complete. | Create final verification report after remaining high/medium debt is reduced. |

## Maintenance Rules

- Add an item when a known limitation remains after a phase is marked partial or done.
- Close an item only when code, tests, and docs make the debt materially resolved.
- Keep IDs stable so future commits and reports can reference them.
