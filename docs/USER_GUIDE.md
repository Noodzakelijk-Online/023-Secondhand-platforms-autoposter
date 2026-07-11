# User Guide

This guide explains the current assisted-posting workflow for a seller using the dashboard. It does not describe automatic marketplace submission; every registered platform still requires user-controlled final action on the marketplace.

## Sign In And Create A Listing

1. Register or sign in with email and password.
2. Open Listings.
3. Select New listing.
4. Fill the core fields: title, price, condition, category, location, description, delivery details, and optional item specifics.
5. Upload one or more product images.
6. Save the listing.

The app keeps a revision number for each listing. Editing a listing creates a new revision, and assisted package idempotency uses that revision so repeated queueing does not create duplicate jobs for the same package.

## Improve Listing Quality

Use Quality assistant from the listing editor. It scores buyer-readiness, flags missing or weak fields, and offers deterministic suggestions. Suggestions are not applied automatically; choose Apply for each suggestion you want.

## Prepare Platform Packages

1. Select the target platforms.
2. Add a platform-specific description variant if needed.
3. Select Validate.
4. Review the prepublish cards.
5. Fix missing fields or copy mapped fields from the review panel.
6. Select Queue assisted package.

The queue action prepares a package and job log. It does not log in to marketplaces, bypass account prompts, choose paid placement, or submit the marketplace listing.

Use Regenerate package only when you intentionally want a fresh assisted package for the current listing. It creates a new listing revision before queueing.

## Queue And Job Review

Open Queue to watch assisted package jobs. The queue supports:

- platform, status, sorting, and paging controls;
- manual refresh;
- live refresh with pause/resume;
- job logs;
- retry guidance.

Retry only after fixing the listing, platform account, or validation issue that caused the previous job to fail. For `needs_user_action` jobs, retry is mainly for regenerating package output after a deliberate listing change.

## Accounts, Templates, And Mappings

Accounts identify the platform account context, but the current app does not store raw platform passwords or active marketplace tokens.

Templates help reuse description text. Use variants such as `default`, `short`, `seasonal`, or platform-specific copy styles to keep multiple reusable versions under clear labels. Category mappings translate a master listing category into a platform-specific category. Both settings screens support search/filter/sort/page controls.

## Data Portability And Privacy

Use Export JSON to download portable listing/configuration data. Exports exclude password hashes, sessions, platform tokens, raw secrets, and image binaries. Use Import JSON to restore supported portable data into the current account.

Delete my account data removes owned listings, jobs, templates, mappings, accounts, sessions, and uploaded local image files.

## Diagnostics

Run diagnostics from Settings to inspect startup safety, database, migrations, upload directory, platform adapters, and legacy script isolation. A local-development warning can be acceptable, but production launch requires the release readiness gate.

## Known Limits

- final marketplace submission is manual for all registered production platforms.
- eBay OAuth consent foundation exists, but token exchange and official publishing are not implemented.
- Browser/accessibility walkthrough evidence is still required before final launch.
- Deployment-specific PostgreSQL, edge security, backup, and rate-limit evidence is still required before client launch.
