# Product Analytics Local-First

The app provides local, user-scoped analytics through `GET /api/analytics` and the dashboard Insights panel.

## What It Measures

- Listing status counts.
- Inventory value and average listing price.
- Publishing job counts by status and platform.
- Selected platform coverage from listing mappings.
- Listing quality aggregates, including average score, grade counts, missing images, and recurring issue fields.

## Privacy Posture

- Analytics are derived from the authenticated user's own database records.
- No external analytics provider, tracking pixel, browser fingerprinting, or cross-user event stream is used.
- The response is aggregate-only and does not expose another user's listings, jobs, accounts, or pricing.
- The endpoint explicitly returns `source=local_database` and `external_tracking=false`.

## Current Limits

- Analytics are current-state aggregates, not historical funnels.
- There is no cohort tracking, conversion attribution, or per-session behavior timeline.
- Operator-wide metrics remain separate at `/api/metrics`; user product insights live at `/api/analytics`.
