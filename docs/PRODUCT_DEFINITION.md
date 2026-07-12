# Product Definition

## What This Product Is

Secondhand Platforms Autoposter is a central listing manager for people who sell the same secondhand product on multiple marketplaces.

The user creates one reusable master listing with title, description, price, category, condition, location, delivery options, category-specific attributes, tags, and images. The app validates that listing for each selected platform, stores platform-specific overrides, creates publishing jobs, tracks job logs, and prepares platform-ready posting packages.

After a seller completes a marketplace-side assisted posting flow, queue details let the seller record user-confirmed manual completion with the marketplace URL and optional listing ID. That updates the job, attempt history, and platform mapping without pretending the app performed automatic marketplace submission.

Master listing condition values are normalized to `new`, `as_new`, `good`, `used`, `fair`, `damaged`, `for_parts`, or `other`. Master listing status values are normalized to `draft`, `ready`, `published`, or `archived`.

## Target User

The primary user is a non-technical seller or small operator who wants to avoid rewriting the same listing repeatedly for Marktplaats, Koopplein, Nextdoor, eBay, and Tweedehands.

## What "Autoposter" Means Here

In this compliant product, autoposter means:

- Store one master listing.
- Adapt the listing for multiple platforms.
- Validate missing fields before posting.
- Queue and track publishing work.
- Prepare assisted posting packages where automation is not appropriate.
- Use official APIs only when configured and legally/technically available.

It does not mean bypassing platform controls.

## Publishing Modes

- `assisted`: The app prepares fields, images, instructions, and a platform URL. The user completes login, CAPTCHA, payment choices, confirmations, and final submission.
- `official_api`: Future mode for platforms with official APIs, OAuth, and credentials configured.
- `manual_reference`: Legacy or unsupported platform workflows documented for local/manual use only.

The current implementation uses assisted mode for every exposed platform.

## Supported Platforms

- Marktplaats: assisted posting.
- Koopplein: assisted posting.
- Nextdoor: assisted posting.
- eBay: assisted posting, with future official API foundation planned.
- Tweedehands: assisted/manual reference only.

## End-To-End User Flow

1. Register or log in.
2. Create a listing.
3. Upload images.
4. Fill the master listing fields.
5. Select target platforms.
6. Add platform-specific description overrides if needed.
7. Validate readiness.
8. Queue assisted package jobs.
9. Regenerate a fresh assisted package only when the seller intentionally wants a new package revision.
10. Review job logs and assisted posting package data.
11. Complete platform-side actions manually when required.
12. Record the marketplace URL and optional listing ID in the queue after manual completion.

## What The Product Must Never Do

- Bypass CAPTCHAs.
- Bypass anti-bot protections.
- Evade rate limits.
- Store raw platform passwords.
- Submit paid placements without explicit user approval.
- Claim a listing is published unless an official API confirms it or the user manually confirms completion.
- Hide platform-specific compliance limitations.

## Current Production Readiness Meaning

Production-ready currently means the app has a coherent frontend, backend, database model, authentication, image upload, platform adapter contract, validation, job tracking, retry support, personal-account SaaS boundaries without billing, documentation, tests, Docker setup, and honest assisted posting behavior.

It does not yet mean paid subscriptions, organizations, team seats, official API publishing, external object storage, CI/CD, Alembic migrations, full browser/accessibility launch coverage, or third-party credential integrations.
