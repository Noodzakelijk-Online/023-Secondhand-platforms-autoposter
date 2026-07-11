# Domain Model

Date: 2026-07-12

## Aggregate Boundaries

The core aggregate is `Listing`. A listing owns:

- uploaded image metadata;
- per-platform listing mappings and overrides;
- saved listing drafts;
- publishing jobs for assisted packages.

Publishing jobs own their logs and publication attempts. Deleting a listing through the API now exercises ORM cascade relationships across this aggregate so stale job/log/attempt records do not survive the listing they describe.

User-owned supporting entities remain scoped by `owner_id`:

- platform accounts;
- listing templates;
- category mappings.

Those entities have separate CRUD and privacy-deletion coverage because they are reusable workspace resources rather than children of a single listing.

## Invariants

The API/schema layer enforces:

- non-negative listing money and weight fields;
- normalized ISO-style currency;
- normalized and bounded tags;
- bounded `category_attributes` JSON objects for item specifics such as vehicle mileage, clothing size, furniture style, electronics accessories, or other category-specific details;
- explicit listing condition and status choices;
- listing revision increments on edits;
- publish idempotency keyed by owner, listing, revision, platform, action, account, and operation mode.

## Regression Evidence

- `tests/test_data_invariants.py` covers field validation and normalization.
- `tests/test_category_mappings.py` covers category attributes in validation and assisted package mapped fields.
- `tests/test_data_portability.py` covers category attributes in JSON and CSV portability.
- `tests/test_listing_revisions.py` covers revisioning and publish idempotency.
- `tests/test_owner_isolation.py` covers owner-scoped resources.
- `tests/test_domain_model.py` covers listing aggregate cascade deletion for images, drafts, mappings, jobs, logs, and attempts.
