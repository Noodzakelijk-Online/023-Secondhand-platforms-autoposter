# Requirements Traceability

This document maps the 89 goal phases to concrete repository evidence. It is not a claim that every phase is complete; it is a release-control index for finding the code, tests, and documents that support each status in `docs/COMPLETION_MATRIX.md`.

Legend:

- `Evidence`: primary file, test, or document supporting the current status.
- `Remaining gate`: the next proof required before the phase can be considered stronger than its current status.

| Phase | Status | Evidence | Remaining gate |
| --- | --- | --- | --- |
| 0 | Done | `docs/REPOSITORY_PROVENANCE.md`, `docs/COMPLETION_MATRIX.md`, `git status` practice in local verification | Refresh provenance when branch, remote, or release baseline changes. |
| 1 | Done | `docs/DEEP_TECHNICAL_AUDIT.md`, `docs/RED_TEAM_REVIEW.md`, `docs/TECHNICAL_DEBT_REGISTER.md`, `tests/test_deep_technical_audit.py` | Refresh audit after major route, model, storage, auth, adapter, worker, or deployment changes. |
| 2 | Done | `docs/PRODUCT_DEFINITION.md` | Keep aligned when product scope changes. |
| 3 | Partial | `app/main.py`, `app/api.py`, `app/services/` | Split large route module if product surface grows. |
| 4 | Partial | `app/models.py`, `migrations/versions/`, `tests/test_migrations.py` | Prove migrations on PostgreSQL target. |
| 5 | Partial | `app/config.py`, `.env.example`, `tests/test_startup_safety.py` | Capture deployment-specific env evidence. |
| 6 | Partial | `app/security.py`, `app/rate_limit.py`, `tests/test_auth_security.py` | Add edge/proxy rate-limit evidence. |
| 7 | Done | `tests/test_owner_isolation.py`, owner filters in `app/api.py` | Keep coverage aligned with new owner-owned routes. |
| 8 | Done | `app/middleware.py`, `app/rate_limit.py`, `tests/test_api_hardening.py`, `tests/test_api_rate_limit.py` | Keep API limits aligned with deployment edge throttling and traffic patterns. |
| 9 | Partial | `app/storage.py`, `tests/test_storage_uploads.py` | Add object storage adapter and image-processing policy. |
| 10 | Partial | `app/models.py`, `app/schemas.py`, `tests/test_data_invariants.py` | Expand category-specific field depth. |
| 11 | Done | `app/adapters/base.py`, `app/adapters/assisted.py`, `app/adapters/registry.py`, `tests/test_api.py` | Keep capability metadata aligned when adapters or platform modes change. |
| 12 | Done | `docs/PLATFORM_COMPLETION_CONTRACTS.md`, `tests/test_platform_contracts.py`, `app/adapters/` | Keep platform contracts current when adapters, categories, blocked actions, or official API modes change. |
| 13 | Done | `docs/PLATFORM_REALITY_REVIEW.md` | Re-review if platform policies change. |
| 14 | Partial | `app/services/jobs.py`, `public/app.js` prepublish review | Add executed browser evidence. |
| 15 | Done | `docs/UI_WORDING_AUDIT.md`, `tests/test_ui_wording.py`, `public/index.html`, `public/app.js` | Re-audit wording when platform modes, official API behavior, or primary job actions change. |
| 16 | Partial | `app/services/oauth.py`, `tests/test_ebay_oauth.py` | Add token exchange, refresh, sandbox API proof. |
| 17 | Done | `docs/LEGACY_SCRIPT_QUARANTINE.md`, `tests/test_legacy_quarantine.py` | Remove archive later only by explicit decision. |
| 18 | Partial | `app/services/jobs.py`, `app/worker.py`, `tests/test_worker.py` | Verify concurrent workers on PostgreSQL. |
| 19 | Done | `app/services/jobs.py`, `app/api.py`, `public/index.html`, `public/app.js`, `tests/test_listing_revisions.py`, `tests/test_regenerate_package_ui.py` | Keep regenerate/repost semantics explicit if future official API publishing or manual completion confirmation is added. |
| 20 | Partial | `docs/RATE_LIMITS.md`, `tests/test_worker.py` | Add official API quota-header handling. |
| 21 | Done | `GET /api/jobs`, queue polling in `public/app.js`, `public/index.html`, `tests/test_job_polling_ui.py` | Revisit only if SSE/WebSocket delivery becomes necessary for deployment scale. |
| 22 | Done | Static frontend in `public/`, README architecture notes | Revisit only if frontend complexity changes. |
| 23 | Partial | `public/index.html`, `public/app.js`, `public/styles.css` | Add executed browser QA evidence. |
| 24 | Done | `docs/UI_ACTION_AUDIT.md`, `tests/test_ui_action_audit.py` | Keep action audit current when visible controls change. |
| 25 | Done | `docs/API_USAGE_AUDIT.md` | Keep updated with routes and UI changes. |
| 26 | Done | Template variants in `app/models.py`, `app/schemas.py`, `app/api.py`, `public/index.html`, `public/app.js`, `tests/test_template_variants.py` | Keep template variant controls aligned with export/import and UI filters. |
| 27 | Done | Category-specific local quality rules in `app/services/quality.py`, API/UI quality flow, `tests/test_listing_quality.py` | Keep heuristics local, explainable, and user-applied as categories expand. |
| 28 | Done | `app/query.py`, `app/api.py`, `public/index.html`, `public/app.js`, `tests/test_extended_query_controls.py` | Keep query controls and route parameters aligned when list screens or sortable fields change. |
| 29 | Done | JSON, CSV, and image ZIP portability routes in `app/api.py`, Settings UI controls, `tests/test_data_portability.py` | Keep JSON privacy boundary, CSV fields, and image ZIP manifest aligned as listing fields change. |
| 30 | Done | Data delete/export/import audit events, owner-scoped `/api/audit-events`, Settings privacy activity UI, retention purge, `tests/test_data_portability.py` | Keep audit events sanitized and scoped as new privacy-sensitive actions are added. |
| 31 | Done | Account CRUD/status routes and UI, connection metadata scrubbing, eBay OAuth handoff records, `tests/test_api.py`, `tests/test_ebay_oauth.py` | Keep raw platform secrets out of app tables/API responses; real token exchange remains tracked under phase 16. |
| 32 | Done | Security headers in `app/middleware.py`, bearer-only CSRF posture in `docs/AUTH_SECURITY_POSTURE.md`, `tests/test_api_hardening.py` | Keep CSP and auth transport reviewed when frontend assets or auth mode change. |
| 33 | Done | `docs/ERROR_HANDLING_UX.md`, `app/middleware.py`, `public/app.js`, `tests/test_api_hardening.py`, `tests/test_frontend_error_ux.py` | Keep error codes, retryability, and frontend display aligned when new error classes are introduced. |
| 34 | Partial | Global message/banner, import error handling, retry guidance, and field recovery in `public/app.js` | Add executed browser evidence for error, retry, import, and validation recovery flows. |
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
| 46 | Done | `Readme.md`, `docs/USER_GUIDE.md`, `docs/API_REFERENCE.md`, `tests/test_documentation_overhaul.py` | Keep user guide and API reference aligned when workflows, endpoints, or launch limits change. |
| 47 | Done | `docs/COMPLETION_MATRIX.md` | Keep counts synchronized. |
| 48 | Done | `docs/FINAL_VERIFICATION_REPORT.md` | Refresh before final release. |
| 49 | Done | `docs/TECHNICAL_DEBT_REGISTER.md` | Keep debt items current. |
| 50 | Done | `docs/RED_TEAM_REVIEW.md` | Re-review after sensitive changes. |
| 51 | Done | `docs/ADVERSARIAL_TEST_REPORT.md` | Re-run adversarial review near release. |
| 52 | Partial | `docs/BROWSER_ACCESSIBILITY_QA.md` | Execute walkthrough and record evidence. |
| 53 | Done | `docs/ACCESSIBILITY_AUDIT.md`, `tests/test_accessibility_audit.py`, `public/index.html` | Keep smoke checks aligned with new visible controls and still execute the broader browser checklist before launch. |
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
| 65 | Done | Explicit listing state transition helpers in `public/app.js`, `tests/test_frontend_state_consistency.py` | Keep stale review-state invalidation aligned with new listing mutation paths. |
| 66 | Partial | Prepublish review panel in UI | Add executed walkthrough evidence. |
| 67 | Done | Adapter compliance notes from `GET /api/platforms`, platform/prepublish UI in `public/app.js`, `tests/test_ui_wording.py` | Keep notes visible when adapters or compliance language change. |
| 68 | Done | `docs/OFFICIAL_API_CREDENTIAL_CHECKLIST.md` | Update with each official API candidate. |
| 69 | Done | Performance indexes migration and docs | Benchmark against production-like data later. |
| 70 | Partial | `docs/RELEASE_READINESS.md` | Capture final launch evidence. |
| 71 | Done | `scripts/audit_dependencies.py`, supply-chain workflow/docs | Keep audits current with dependencies. |
| 72 | Done | `docs/BACKUP_RESTORE.md` | Prove restore in target environment. |
| 73 | Done | `docs/OPERATOR_RUNBOOK.md` | Update when operations change. |
| 74 | Partial | `docs/NON_TECHNICAL_USER_SIMULATION.md`, `tests/test_non_technical_user_simulation.py` | Execute and record a real non-technical user walkthrough. |
| 75 | Done | `docs/AUTONOMY_FIRST_DESIGN.md`, `tests/test_autonomy_first_design.py` | Keep user-control boundaries aligned with UI wording and adapter behavior. |
| 76 | Done | `docs/PRODUCT_VALUE_REVIEW.md`, `tests/test_product_value_review.py` | Revisit after non-technical simulation and browser evidence. |
| 77 | Done | `docs/PRODUCT_REALISM_REVIEW.md`, `docs/PLATFORM_REALITY_REVIEW.md`, `tests/test_product_realism_review.py` | Revisit if product positioning or automation scope changes. |
| 78 | Done | This traceability document plus `tests/test_requirements_traceability.py` | Keep synchronized with completion matrix. |
| 79 | Done | `docs/TASK_GRAPH_AND_EXECUTION.md` | Keep execution lanes and critical path aligned with the matrix. |
| 80 | Done | `docs/PROGRESSIVE_STABILIZATION_GATES.md` | Keep gate status aligned with release readiness evidence. |
| 81 | Partial | Core app and many docs/tests | Continue replacing partials with evidence. |
| 82 | Done | `docs/API_USAGE_AUDIT.md`, visible UI/API wiring | Keep route/UI audit current. |
| 83 | Done | `docs/API_USAGE_AUDIT.md` | Keep purposeful endpoint mapping current. |
| 84 | Done | `docs/FALSE_COMPLETION_PREVENTION.md`, `tests/test_false_completion_prevention.py` | Keep blocked claims aligned with release readiness status. |
| 85 | Partial | `docs/FINAL_NO_EXCUSES_SEARCH.md`, `tests/test_final_no_excuses_search.py` | Repeat the no-excuses search at final release time after launch evidence exists. |
| 86 | Done | `docs/FRESH_CLONE_DRY_RUN.md` | Repeat after release-blocking changes or immediately before final launch. |
| 87 | Partial | Completion matrix and product definition | Final acceptance remains pending. |
| 88 | Partial | Prior turn summaries and docs | Final release response pending. |

## Traceability Maintenance

- Update this file in the same change that updates `docs/COMPLETION_MATRIX.md`.
- Keep each phase number present exactly once.
- Prefer concrete files over broad claims.
- Do not mark a phase `Done` here unless the completion matrix agrees.
