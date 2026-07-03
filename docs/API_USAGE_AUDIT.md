# API Usage Audit

This audit maps the FastAPI surface to visible frontend usage, tests, and remaining gaps.

## Summary

- Frontend entrypoint: `public/app.js`
- API implementation: `app/api.py`
- Current UI coverage: dashboard, listings, queue, accounts, settings, export/import
- Current test coverage: API smoke flow, hardening, auth, storage, worker, revisions, category mappings, data portability, diagnostics
- Operator-only local backup/restore is intentionally implemented as scripts, not API routes, because private backup archives include database rows and uploaded media.

## Route Map

| Method | Route | Frontend usage | Test coverage | Notes |
| --- | --- | --- | --- | --- |
| `GET` | `/api/health` | Boot health badge | `test_api_hardening.py` | Public endpoint. |
| `GET` | `/api/diagnostics` | Settings diagnostics panel | `test_doctor.py` | Visible and tested through doctor coverage. |
| `POST` | `/api/auth/register` | Auth form create account | `test_api.py`, `test_auth_security.py` | Visible and tested. |
| `POST` | `/api/auth/login` | Auth form sign in | `test_api.py`, `test_auth_security.py` | Visible and tested. |
| `POST` | `/api/auth/logout` | Sidebar sign out | `test_auth_security.py` | Visible and tested. |
| `GET` | `/api/auth/me` | Boot current user | `test_auth_security.py` | Visible through user email. |
| `DELETE` | `/api/auth/me` | Settings privacy delete action | `test_data_portability.py` | Visible and tested. |
| `GET` | `/api/audit-events` | API/diagnostic audit history; no dedicated UI yet | `test_data_portability.py` | Owner-scoped and tested. Useful for privacy/export/import/delete evidence. |
| `GET` | `/api/platforms` | Account, template, mapping, listing platform controls plus credential/compliance reality text | `test_api.py` | Visible and tested. Includes `official_api_status`, `credential_requirements`, and `automation_blockers`. |
| `GET` | `/api/listings` | Dashboard/listing list with search/filter/sort/page controls | `test_api_hardening.py` | Visible and tested. |
| `POST` | `/api/listings` | New listing button | `test_api.py` | Visible and tested. |
| `GET` | `/api/listings/{listing_id}` | Not directly used | `test_api.py` | Useful for future deep-linking. |
| `PATCH` | `/api/listings/{listing_id}` | Listing editor save | `test_listing_revisions.py`, `test_api.py` | Visible and tested. |
| `DELETE` | `/api/listings/{listing_id}` | Listing editor delete | `test_api.py` | Visible and tested. |
| `POST` | `/api/listings/{listing_id}/duplicate` | Listing editor duplicate | `test_listing_revisions.py` | Visible and tested. |
| `POST` | `/api/listings/{listing_id}/images` | Listing image upload | `test_storage_uploads.py`, `test_api.py` | Visible and tested. |
| `PATCH` | `/api/listings/{listing_id}/images/order` | Image tile up/down buttons | `test_storage_uploads.py` | Visible and tested. |
| `DELETE` | `/api/listings/{listing_id}/images/{image_id}` | Image tile delete | `test_storage_uploads.py` | Visible and tested. |
| `POST` | `/api/listings/{listing_id}/platforms` | Platform selection and description overrides | `test_listing_revisions.py`, `test_category_mappings.py` | Visible and tested. |
| `GET` | `/api/listings/{listing_id}/validate` | Validate button | `test_api.py`, `test_category_mappings.py` | Visible and tested. |
| `POST` | `/api/listings/{listing_id}/publish` | Queue publish button | `test_api.py`, `test_category_mappings.py`, `test_worker.py` | Visible and tested. |
| `GET` | `/api/jobs` | Dashboard/latest jobs and queue view with platform/status/sort/page controls | `test_worker.py` | Visible and tested. |
| `GET` | `/api/jobs/{job_id}` | Not directly used | `test_worker.py` | Useful for future deep-linking. |
| `POST` | `/api/jobs/{job_id}/retry` | Queue job detail retry button | `test_worker.py` | Visible and tested. |
| `POST` | `/api/jobs/{job_id}/confirm-completion` | Queue job detail manual completion form | `test_api.py` | Visible and tested. Records user-confirmed final platform URL; does not automate platform publish. |
| `GET` | `/api/accounts` | Accounts list | `test_api.py` | Visible and tested. |
| `POST` | `/api/accounts` | Account form | `test_api.py` | Visible and tested. |
| `DELETE` | `/api/accounts/{account_id}` | Account list delete button | `test_api.py` | Visible and tested. |
| `GET` | `/api/templates` | Settings template list | `test_api.py`, `test_data_portability.py` | Visible and tested. |
| `POST` | `/api/templates` | Settings template form | `test_api.py`, `test_data_portability.py` | Visible and tested. |
| `GET` | `/api/category-mappings` | Settings mapping list | `test_category_mappings.py`, `test_data_portability.py` | Visible and tested. |
| `POST` | `/api/category-mappings` | Settings mapping form | `test_category_mappings.py`, `test_data_portability.py` | Visible and tested. |
| `PATCH` | `/api/category-mappings/{mapping_id}` | Settings mapping edit flow | `test_category_mappings.py` | Visible and tested. |
| `DELETE` | `/api/category-mappings/{mapping_id}` | Settings mapping delete | `test_category_mappings.py` | Visible and tested. |
| `GET` | `/api/export` | Settings export JSON | `test_data_portability.py` | Visible and tested. |
| `POST` | `/api/import` | Settings import JSON | `test_data_portability.py` | Visible and tested. |

## Required Follow-Up

- Keep query controls aligned as additional list screens are added.
- Keep image reorder coverage aligned if drag-and-drop replaces the current up/down controls.
- Keep backup/restore outside the user API unless a future admin role, encryption design, and production storage policy are implemented.
- Keep this audit updated whenever a route is added, removed, or made visible in the UI.
