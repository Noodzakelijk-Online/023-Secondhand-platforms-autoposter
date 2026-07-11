# Product Realism Review

This review checks whether the current product story matches what the repository can actually do.

## Real Today

| Claim | Reality | Evidence |
| --- | --- | --- |
| A user can manage reusable listings. | Real. The app supports listing CRUD, images, revisions, templates, category mappings, and search/filter/page controls. | `app/api.py`, `public/app.js`, `tests/test_api.py` |
| A user can prepare multi-platform posting packages. | Real as assisted posting. Adapters validate and map fields; jobs produce `needs_user_action` packages. | `app/adapters/assisted.py`, `tests/test_no_mocks_production.py` |
| A user can improve listing readiness. | Real within deterministic local limits. The quality assistant adds category-specific checks, does not invent facts, and does not call external AI. | `app/services/quality.py`, `tests/test_listing_quality.py` |
| A user can understand local business state. | Real. Local analytics derive owner-scoped aggregates without external tracking. | `app/services/analytics.py`, `tests/test_analytics.py` |
| A user can export/import/delete owned data. | Real for JSON business data and account deletion; image binaries are not included in export. | `tests/test_data_portability.py` |
| The app has release-control documentation. | Real. Matrix, traceability, task graph, gates, and false-completion docs exist. | `docs/REQUIREMENTS_TRACEABILITY.md` |

## Aspirational Or Not Yet Real

| Claim | Status | Why it is not yet real |
| --- | --- | --- |
| Fully automated marketplace publishing | Not real | All registered adapters are assisted; no official API publish adapter exists. |
| eBay official API listing creation | Not real | OAuth consent foundation exists, but token exchange, refresh, seller policy checks, and sandbox listing proof are missing. |
| Production launch readiness | Not real | Deployment database, worker, secrets, CORS, backup, browser, and fresh-clone evidence are missing. |
| Non-technical user-proven usability | Not real | Only a proxy simulation exists; no observed external user walkthrough is recorded. |
| Full multilingual UI | Not real | Locale metadata exists, but visible UI copy is mostly English. |
| Team/workspace collaboration | Deliberately out of scope | Workspaces are deferred by product decision. |

## Marketplace Realism

The product is realistic if sold as an assisted listing preparation tool. It is unrealistic if sold as an autoposter that independently logs in, bypasses platform controls, chooses paid options, or completes final marketplace submissions.

## Operational Realism

The app is realistic for local demo and continued hardening. It should not be represented as a client launch until:

- production startup and target database evidence are captured,
- worker deployment is confirmed,
- backup/restore is proven,
- browser/accessibility/responsive walkthroughs are executed,
- a real non-technical user walkthrough is recorded,
- remaining partial phases are accepted or closed.

## Verdict

The current product is coherent and useful as a local-first assisted-posting workflow. The name "autoposter" remains risky unless paired with clear assisted-posting wording, because the product does not currently perform automatic marketplace submission.
