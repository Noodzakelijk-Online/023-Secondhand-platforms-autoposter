# UI Wording Audit

This audit records the current user-facing wording rules for assisted marketplace posting.

## Current Decision

The frontend must describe marketplace work as assisted package preparation, not automatic marketplace publishing. The primary action is labeled `Queue assisted package`, the queue page is labeled `Assisted package queue`, and the post-action message says `Assisted package queued`.

## Required Wording

- Use "assisted package" when the app prepares fields, links, and instructions.
- Use "manual submit" when a marketplace still requires the seller's final action.
- Use `needs_user_action` for job states that require platform-side completion.
- Keep eBay described as a future official API candidate, not an active official publishing integration.

## Blocked Wording

- "Queue publish" as a visible primary UI action.
- "Publishing queue" as the page title for assisted jobs.
- "Fully automated" for current registered platforms.
- "Automatic marketplace publishing" without official API proof.
- Any wording that implies the app completes login, CAPTCHA, payment, policy setup, or final marketplace submission for assisted adapters.

## Regression Coverage

`tests/test_ui_wording.py` scans the frontend source for required assisted-package wording and blocks the riskiest automatic-publishing claims.
