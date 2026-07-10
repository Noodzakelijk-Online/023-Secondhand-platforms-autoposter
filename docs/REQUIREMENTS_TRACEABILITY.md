# Requirements Traceability

This document maps the 89 goal phases to concrete repository evidence. It is not a claim that every phase is complete; it is a release-control index for finding the code, tests, and documents that support each status in `docs/COMPLETION_MATRIX.md`.

Legend:

- `Evidence`: primary file, test, or document supporting the current status.
- `Remaining gate`: the next proof required before the phase can be considered stronger than its current status.

| Phase | Status | Evidence | Remaining gate |
| --- | --- | --- | --- |
| 0 | Partial | `docs/COMPLETION_MATRIX.md`, `git status` practice in local verification | Add branch/PR provenance artifact before release. |
| 1 | Partial | `docs/RED_TEAM_REVIEW.md`, `docs/TECHNICAL_DEBT_REGISTER.md` | Add formal deep audit report with route/model/storage review. |
| 2 | Done | `docs/PRODUCT_DEFINITION.md` | Keep aligned when product scope changes. |
| 3 | Partial | `app/main.py`, `app/api.py`, `app/services/` | Split large route module if product surface grows. |
| 4 | Partial | `app/models.py`, `migrations/versions/`, `tests/test_migrations.py` | Prove migrations on PostgreSQL target. |
| 5 | Partial | `app/config.py`, `.env.example`, `tests/test_startup_safety.py` | Capture deployment-specific env evidence. |
| 6 | Partial | `app/security.py`, `app/rate_limit.py`, `tests/test_auth_security.py` | Add edge/proxy rate-limit evidence. |
| 7 | Done | `tests/test_owner_isolation.py`, owner filters in `app/api.py` | Keep coverage aligned with new owner-owned routes. |
| 8 | Partial | `app/middleware.py`, `tests/test_api_hardening.py` | Add broader endpoint throttling if needed. |
| 9 | Partial | `app/storage.py`, `tests/test_storage_uploads.py` | Add object storage adapter and image-processing policy. |
| 10 | Partial | `app/models.py`, `app/schemas.py`, `tests/test_data_invariants.py` | Expand category-specific field depth. |
| 11 | Partial | `app/adapters/base.py`, `app/adapters/assisted.py` | Expand adapter capability metadata. |
| 12 | Partial | `app/adapters/`, `docs/PLATFORM_REALITY_REVIEW.md` | Add deeper platform contract tests/docs. |
| 13 | Done | `docs/PLATFORM_REALITY_REVIEW.md` | Re-review if platform policies change. |
| 14 | Partial | `app/services/jobs.py`, `public/app.js` prepublish review | Add executed browser evidence. |
| 15 | Partial | `Readme.md`, `docs/OFFICIAL_API_CREDENTIAL_CHECKLIST.md` | Complete UI wording audit. |
| 16 | Partial | `app/services/oauth.py`, `tests/test_ebay_oauth.py` | Add token exchange, refresh, sandbox API proof. |
| 17 | Done | `docs/LEGACY_SCRIPT_QUARANTINE.md`, `tests/test_legacy_quarantine.py` | Remove archive later only by explicit decision. |
| 18 | Partial | `app/services/jobs.py`, `app/worker.py`, `tests/test_worker.py` | Verify concurrent workers on PostgreSQL. |
| 19 | Partial | `app/services/jobs.py`, `tests/test_worker.py` | Add polished explicit repost/regenerate UI. |
| 20 | Partial | `docs/RATE_LIMITS.md`, `tests/test_worker.py` | Add official API quota-header handling. |
| 21 | Partial | `GET /api/jobs`, queue UI in `public/app.js` | Add robust polling/SSE behavior evidence. |
| 22 | Done | Static frontend in `public/`, README architecture notes | Revisit only if frontend complexity changes. |
| 23 | Partial | `public/index.html`, `public/app.js`, `public/styles.css` | Add executed browser QA evidence. |
| 24 | Partial | `docs/API_USAGE_AUDIT.md` | Complete formal visible-action audit. |
| 25 | Done | `docs/API_USAGE_AUDIT.md` | Keep updated with routes and UI changes. |
| 26 | Partial | Template/category mapping routes and UI, `tests/test_api.py` | Add variants/automation helpers. |
| 27 | Partial | `app/services/quality.py`, `tests/test_listing_quality.py` | Add richer per-category or optional AI provider. |
| 28 | Partial | `app/query.py`, listing/job controls in UI | Add deeper query controls to account/template/mapping screens. |
| 29 | Partial | Export/import routes, `tests/test_data_portability.py` | Add image binary export and CSV tools. |
| 30 | Partial | Data delete/export/import, audit events, retention purge | Add admin/operator audit review UI if required. |
| 31 | Partial | Account routes/UI, eBay OAuth foundation | Add secure token setup and secret-manager exchange. |
| 32 | Partial | `app/middleware.py`, `docs/AUTH_SECURITY_POSTURE.md` | Capture deployment web-security review. |
| 33 | Partial | Structured errors in middleware/tests | Improve UX copy and endpoint-specific messages. |
| 34 | Partial | Global message/banner and field recovery in `public/app.js` | Add retry guidance and browser evidence. |
| 35 | Done | `Dockerfile`, `docker-compose.yml` | Keep in sync with runtime dependencies. |
| 36 | Done | `app/doctor.py`, `tests/test_doctor.py` | Add checks as new infrastructure appears. |
| 37 | Done | `scripts/verify.py` | Keep quality gate current. |
| 38 | Done | `app/demo.py`, `docs/DEMO_MODE.md`, tests | Keep demo mode development-only. |
| 39 | Done | `docs/FAKE_PROVIDER_LAB.md`, `tests/fake_provider_lab.py` | Keep fake providers out of production registry. |
| 40 | Done | `docs/NO_MOCKS_PRODUCTION_AUDIT.md`, `tests/test_no_mocks_production.py` | Re-run when adapters change. |
| 41 | Done | `docs/TESTING_STRATEGY.md` | Update strategy as coverage changes. |
| 42 | Partial | API smoke tests in `tests/test_api.py` | Add full browser acceptance suite. |
| 43 | Partial | Worker/API smoke coverage | Add true browser E2E workflows. |
| 44 | Done | `pyproject.toml`, `scripts/verify.py` | Consider type-check gate later. |
| 45 | Done | `.github/workflows/verify.yml` | Keep CI matrix aligned with verify script. |
| 46 | Partial | README plus `docs/` set | Add richer API/user docs as needed. |
| 47 | Done | `docs/COMPLETION_MATRIX.md` | Keep counts synchronized. |
| 48 | Done | `docs/FINAL_VERIFICATION_REPORT.md` | Refresh before final release. |
| 49 | Done | `docs/TECHNICAL_DEBT_REGISTER.md` | Keep debt items current. |
| 50 | Done | `docs/RED_TEAM_REVIEW.md` | Re-review after sensitive changes. |
| 51 | Done | `docs/ADVERSARIAL_TEST_REPORT.md` | Re-run adversarial review near release. |
| 52 | Partial | `docs/BROWSER_ACCESSIBILITY_QA.md` | Execute walkthrough and record evidence. |
| 53 | Partial | Accessibility checklist in docs | Add automated or executed accessibility evidence. |
| 54 | Partial | Responsive checklist in docs | Execute browser matrix. |
| 55 | Done | `docs/BACKUP_RESTORE.md` | Validate restore against deployment target. |
| 56 | Done | `app/observability.py`, `/api/metrics`, runbook | Add Prometheus/OTel only if required. |
| 57 | Done | `app/services/analytics.py`, `docs/PRODUCT_ANALYTICS_LOCAL_FIRST.md` | Keep local-only analytics posture. |
| 58 | Partial | User-owned data model and auth boundaries | Finish SaaS policies if multi-tenant launch is planned. |
| 59 | Done | `docs/WORKSPACES_OPTIONAL_REVIEW.md`, `tests/test_workspaces_optional_review.py` | Reopen only if team collaboration enters scope. |
| 60 | Partial | `app/services/localization.py`, `/api/localization`, `docs/INTERNATIONALIZATION.md`, `tests/test_internationalization.py` | Add full frontend copy catalog, user locale preference, translated messages, and browser evidence. |
| 61 | Done | `app/feature_flags.py`, `docs/FEATURE_FLAGS.md` | Keep flags safety-reviewed. |
| 62 | Done | `app/services/job_state.py`, `docs/STATE_MACHINES.md` | Keep transition docs aligned. |
| 63 | Partial | SQLAlchemy domain models and schema invariants | Refine aggregate boundaries if needed. |
| 64 | Done | Schema validators, `tests/test_data_invariants.py` | Keep invariants aligned with new fields. |
| 65 | Partial | Central frontend state object in `public/app.js` | Add deeper consistency rules/tests. |
| 66 | Partial | Prepublish review panel in UI | Add executed walkthrough evidence. |
| 67 | Partial | Adapter compliance notes in UI metadata | Add richer compliance UI if required. |
| 68 | Done | `docs/OFFICIAL_API_CREDENTIAL_CHECKLIST.md` | Update with each official API candidate. |
| 69 | Done | Performance indexes migration and docs | Benchmark against production-like data later. |
| 70 | Partial | `docs/RELEASE_READINESS.md` | Capture final launch evidence. |
| 71 | Done | `scripts/audit_dependencies.py`, supply-chain workflow/docs | Keep audits current with dependencies. |
| 72 | Done | `docs/BACKUP_RESTORE.md` | Prove restore in target environment. |
| 73 | Done | `docs/OPERATOR_RUNBOOK.md` | Update when operations change. |
| 74 | Not started | No non-technical simulation report yet. | Run and document a fresh user walkthrough. |
| 75 | Done | `docs/AUTONOMY_FIRST_DESIGN.md`, `tests/test_autonomy_first_design.py` | Keep user-control boundaries aligned with UI wording and adapter behavior. |
| 76 | Not started | No product value review yet. | Document whether current feature set solves the target job. |
| 77 | Partial | `docs/PLATFORM_REALITY_REVIEW.md` | Add broader product realism review. |
| 78 | Done | This traceability document plus `tests/test_requirements_traceability.py` | Keep synchronized with completion matrix. |
| 79 | Done | `docs/TASK_GRAPH_AND_EXECUTION.md` | Keep execution lanes and critical path aligned with the matrix. |
| 80 | Done | `docs/PROGRESSIVE_STABILIZATION_GATES.md` | Keep gate status aligned with release readiness evidence. |
| 81 | Partial | Core app and many docs/tests | Continue replacing partials with evidence. |
| 82 | Done | `docs/API_USAGE_AUDIT.md`, visible UI/API wiring | Keep route/UI audit current. |
| 83 | Done | `docs/API_USAGE_AUDIT.md` | Keep purposeful endpoint mapping current. |
| 84 | Done | `docs/FALSE_COMPLETION_PREVENTION.md`, `tests/test_false_completion_prevention.py` | Keep blocked claims aligned with release readiness status. |
| 85 | Not started | No final no-excuses search yet. | Run near release only. |
| 86 | Partial | Local verification gate passes | Perform and document fresh-clone dry run. |
| 87 | Partial | Completion matrix and product definition | Final acceptance remains pending. |
| 88 | Partial | Prior turn summaries and docs | Final release response pending. |

## Traceability Maintenance

- Update this file in the same change that updates `docs/COMPLETION_MATRIX.md`.
- Keep each phase number present exactly once.
- Prefer concrete files over broad claims.
- Do not mark a phase `Done` here unless the completion matrix agrees.
