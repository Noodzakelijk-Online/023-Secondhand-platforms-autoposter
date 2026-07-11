# Platform Completion Contracts

This document defines the current completion contract for every registered marketplace adapter. It is intentionally stricter than "a platform appears in the UI": each adapter must validate a listing, map copy-ready fields, return an assisted posting package, and preserve the user's control over marketplace-side actions.

## Shared Contract

- Mode is `assisted` for every registered production adapter.
- A ready listing returns `needs_user_action`, mapped fields, compliance notes when relevant, and a platform posting URL.
- An incomplete listing reports missing fields and does not create a posting package that looks final.
- The app must not mark a job as published for assisted adapters.
- The app must not invent platform listing IDs or platform URLs for listings it did not actually publish through an official API.
- Final marketplace submission, login, CAPTCHA or anti-abuse checks, two-factor prompts, paid placement choices, policy setup, and confirmation screens remain user-controlled.
- Official API work must pass the official API credential checklist before any adapter changes mode or returns API-confirmed publication.

## Platform Contracts

| Platform | Current contract | Prepared fields | User-controlled boundary |
| --- | --- | --- | --- |
| Marktplaats | Assisted posting package with category, delivery, and pricing review. | Title, description, price, currency, condition, category, location, delivery options, shipping details, item details, category attributes, tags, image filenames. | Login, two-factor or anti-abuse checks, category/payment choices, paid placement, final submission. |
| Koopplein | Assisted posting package with category and price-type review. | Title, description, price, currency, condition, category, location, delivery options, shipping details, item details, category attributes, tags, image filenames. | Account/session prompts, category confirmation, price type, final submission. |
| Nextdoor | Assisted local listing package. | Title, description, price, currency, category, location, tags, image filenames. | Neighborhood access, local visibility, account controls, anti-abuse checks, final submission. |
| eBay | Assisted package only; future official API candidate. | Title, description, price, currency, condition, category, location, delivery options, shipping details, item details, category attributes, tags, image filenames. | OAuth token exchange, seller policy setup, payment/shipping/return settings, fee confirmation, final submission. |
| Tweedehands | Assisted/manual reference package. | Title, description, price, currency, condition, category, location, delivery options, shipping details, item details, category attributes, tags, image filenames. | Account session, platform-rule compliance, scraping/posting decisions, final submission. |

## Regression Coverage

`tests/test_platform_contracts.py` verifies that every registered adapter:

- validates a complete listing successfully,
- reports missing required fields and missing images,
- maps buyer-facing fields and image filenames,
- returns `needs_user_action` rather than `published`,
- exposes platform-specific capability metadata through `GET /api/platforms`,
- keeps eBay marked as an official API candidate without claiming official API support.

`tests/test_no_mocks_production.py` continues to guard against fake marketplace success in production adapters.
