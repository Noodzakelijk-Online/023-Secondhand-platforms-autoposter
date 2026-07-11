# API Reference

This reference summarizes the implemented FastAPI surface. Interactive OpenAPI docs are available at `/docs` while the app is running.

All authenticated endpoints use bearer tokens returned by `POST /api/auth/register` or `POST /api/auth/login`.

## Error Shape

Errors use a structured envelope:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request contains invalid fields.",
    "details": {},
    "field_errors": {},
    "retryable": false,
    "request_id": "..."
  }
}
```

Use `request_id` when matching browser reports to server logs. Retry only when `retryable` is true or after correcting user input.

## Public And Diagnostic Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Health check with current server time. |
| `GET` | `/api/localization` | Current locale metadata and catalog status. |
| `GET` | `/api/metrics` | Lightweight operational counts. |
| `GET` | `/api/diagnostics` | Doctor checks plus local object counts. |

## Authentication

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/auth/register` | Create a user and bearer session. |
| `POST` | `/api/auth/login` | Create a bearer session. |
| `POST` | `/api/auth/logout` | Revoke the current session. |
| `GET` | `/api/auth/me` | Read the current user. |
| `DELETE` | `/api/auth/me` | Delete the current user and owned data. |

## Listings And Images

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/listings` | List owned listings with `search`, `status`, `sort`, `limit`, and `offset`. |
| `POST` | `/api/listings` | Create a listing. |
| `GET` | `/api/listings/{listing_id}` | Read one owned listing. |
| `PATCH` | `/api/listings/{listing_id}` | Update a listing and increment revision when data changes. |
| `DELETE` | `/api/listings/{listing_id}` | Delete a listing. |
| `POST` | `/api/listings/{listing_id}/duplicate` | Duplicate a listing. |
| `POST` | `/api/listings/{listing_id}/images` | Upload a validated image. |
| `PATCH` | `/api/listings/{listing_id}/images/order` | Reorder uploaded images. |
| `DELETE` | `/api/listings/{listing_id}/images/{image_id}` | Delete an image. |

## Platform Preparation

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/platforms` | Registered platform metadata, capabilities, required fields, supported categories, and compliance notes. |
| `POST` | `/api/listings/{listing_id}/platforms` | Save platform selection and overrides. |
| `GET` | `/api/listings/{listing_id}/validate` | Validate readiness and return mapped fields. |
| `GET` | `/api/listings/{listing_id}/quality` | Run deterministic listing quality analysis with category-specific local guidance. |
| `POST` | `/api/listings/{listing_id}/publish` | Queue assisted package jobs. Use `force_new_revision=true` to intentionally regenerate a fresh package. |

Registered production platforms are assisted-only. A successful assisted job returns `needs_user_action`, not API-confirmed marketplace publication.

## Jobs

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/jobs` | List owned jobs with platform/status/sort/page controls. |
| `GET` | `/api/jobs/{job_id}` | Read one owned job. |
| `POST` | `/api/jobs/{job_id}/retry` | Requeue a job after correcting the underlying issue. |

## Accounts, Templates, And Category Mappings

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/accounts` | List platform accounts with platform/status/sort/page controls. |
| `POST` | `/api/accounts` | Create a platform account record. |
| `DELETE` | `/api/accounts/{account_id}` | Delete a platform account record. |
| `POST` | `/api/accounts/ebay/oauth/start` | Start eBay OAuth consent foundation when configured. |
| `GET` | `/api/accounts/ebay/oauth/callback` | Consume eBay OAuth callback state and record setup handoff. |
| `GET` | `/api/templates` | List templates with search/platform/variant/sort/page controls. |
| `POST` | `/api/templates` | Create a template with `name`, `variant`, optional `platform`, and `body`. |
| `PATCH` | `/api/templates/{template_id}` | Update a template, including its variant. |
| `DELETE` | `/api/templates/{template_id}` | Delete a template. |
| `GET` | `/api/category-mappings` | List mappings with source/platform/sort/page controls. |
| `POST` | `/api/category-mappings` | Create or upsert a mapping. |
| `PATCH` | `/api/category-mappings/{mapping_id}` | Update a mapping. |
| `DELETE` | `/api/category-mappings/{mapping_id}` | Delete a mapping. |

## Data Portability

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/export` | Export portable JSON data without secrets or image binaries. |
| `POST` | `/api/import` | Import supported portable JSON data. |

## Pagination

List endpoints return `X-Total-Count`, `X-Limit`, and `X-Offset` headers. Use `limit` and `offset` to page through results.
