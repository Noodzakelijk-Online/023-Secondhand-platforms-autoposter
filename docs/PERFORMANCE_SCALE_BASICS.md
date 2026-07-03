# Performance And Scale Basics

This project is still a small-operator app, but the core API should stay predictable as listings, images, and jobs grow.

## Current Baseline

- List endpoints use bounded `limit` and `offset` parameters.
- The frontend requests paged listing and job data instead of loading unbounded records.
- Jobs are processed by a separate worker when `JOB_PROCESS_INLINE=false`.
- Large binary image files are kept out of JSON export/import.
- Publishing jobs use idempotency keys to prevent duplicate work for the same listing revision and platform.

## Database Indexes

The schema now includes indexes for common read and maintenance paths:

- Listings by owner, status, and recent update order.
- Listing images by listing and display position.
- Platform accounts by owner, platform, status, and creation order.
- Category mappings by owner, platform, and source category.
- Publishing jobs by listing, platform, status, creation order, and due queue order.
- Job logs, attempts, drafts, and sessions by their parent records.

The index migration is idempotent because the initial Alembic revision creates current metadata on fresh databases.

## Operational Limits

- Keep API list limits capped at 100 unless a specific route has a measured need for larger batches.
- Keep worker batches controlled by `WORKER_BATCH_SIZE`.
- Prefer background job processing in production-style deployments.
- Do not add marketplace polling loops without platform-specific cooldowns and quota handling.
- Do not include image binaries in normal JSON exports.

## Remaining Scale Work

- Add PostgreSQL-specific migration verification before production launch.
- Add query timing or metrics around list endpoints and worker batches.
- Add row-claiming semantics before running multiple workers concurrently.
- Move local uploads to object storage for larger deployments.
