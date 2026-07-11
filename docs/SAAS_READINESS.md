# SaaS Readiness Without Billing

Date: 2026-07-12

## Current Product Boundary

The app is ready for a single-account SaaS shape without adding billing, workspaces, or team seats.

Current account model:

- each user owns their listings, jobs, platform accounts, templates, category mappings, exports, imports, analytics, and deletion flow;
- API queries scope business data by `owner_id`;
- `GET /api/account/readiness` exposes the current user's personal-account usage counts;
- billing is explicitly reported as not configured and not required;
- workspaces are explicitly disabled and deferred in `docs/WORKSPACES_OPTIONAL_REVIEW.md`.

## Account Readiness Contract

`GET /api/account/readiness` returns:

- authenticated user identity;
- `scope=personal_account`;
- `billing_required=false`;
- `billing_status=not_configured`;
- `workspaces_enabled=false`;
- `data_isolation=owner_id`;
- user-scoped usage counts for listings, publishing jobs, platform accounts, templates, and category mappings.

## What This Does Not Add

This phase does not add subscriptions, payment providers, invoices, metered billing, organizations, shared seats, or role-based team access. Those remain product decisions for later, not hidden requirements for the assisted-posting app.

## Regression Evidence

`tests/test_saas_readiness.py` proves that the readiness contract is authenticated, billing-free, workspace-free, and scoped to each user's own business data.
