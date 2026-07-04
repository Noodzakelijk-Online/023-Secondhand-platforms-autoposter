# Critical Path

The protected workflow is:

1. User account: register or log in with bearer-session authentication.
2. Listing: create or edit a reusable master listing.
3. Images: upload validated image files tied to the listing owner.
4. Platform selection: choose supported assisted platforms and optional overrides.
5. Readiness validation: run adapter validation before posting work.
6. Platform overrides: store platform-specific drafts and category mappings.
7. Assisted/API job: queue a persistent publishing job.
8. Job logs: process through the worker or inline local mode and record logs.
9. Manual completion/final URL: for assisted jobs, the user completes the platform-side action and records the final platform URL through `POST /api/jobs/{job_id}/confirm-completion`.
10. History: publication attempts, job logs, mappings, audit events, and final URL remain queryable.

## Safety Boundary

Current platform adapters are assisted-only. The app prepares fields and instructions, but does not bypass marketplace login, CAPTCHA, payment, verification, or final submit flows.

The only path from `needs_user_action` to `published` for assisted jobs is explicit owner confirmation with a final URL. The confirmation payload records that the user completed the external action and that the app did not publish automatically.

Audit events are recorded for listing changes, image changes, publish queue actions, manual completion, export/import, and account deletion. They provide user-owned operational history without storing raw credentials or full exported payloads.

Local backup/restore is an operator recovery path and does not change the user critical path. Backup archives contain private database and upload data, so they are intentionally separate from user-facing JSON export/import and redacted support bundles.

Static UI accessibility checks now guard the critical path shell against missing control labels and landmark regressions, including image upload and manual completion controls. They do not replace a browser keyboard or assistive-technology pass.
