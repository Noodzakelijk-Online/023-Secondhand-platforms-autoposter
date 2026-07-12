# Platform Reality Review

This document records the current integration reality for each platform. It intentionally avoids claiming automation that is not implemented or not safe.

## Marktplaats

- Current app mode: assisted.
- Official API status: not configured in this repository.
- Account requirements: platform account, possible login checks, possible confirmation steps.
- What can be prepared: title, description, price, condition, category, location, delivery options, images, tags.
- What cannot be automated here: login, CAPTCHA or anti-abuse checks, SMS/two-factor prompts, paid promotion choices, final submission.
- Current tests: platform validation and assisted job flow are covered through the shared adapter/API tests.
- Future work: research official or partner API availability, add OAuth/API credentials only through environment/secret storage, then implement a separate official provider.

## Koopplein

- Current app mode: assisted.
- Official API status: not configured in this repository.
- Account requirements: platform account and manual confirmation.
- What can be prepared: listing fields, category mapping hints, price and delivery details, images.
- What cannot be automated here: final submission and account security prompts.
- Current tests: covered through shared validation and job flow.
- Future work: document exact category constraints and add platform-specific tests.

## Nextdoor

- Current app mode: assisted.
- Official API status: not configured in this repository.
- Account requirements: Nextdoor account, neighborhood/account restrictions, user-controlled confirmation.
- What can be prepared: title, description, price, category, location, images.
- What cannot be automated here: neighborhood-specific permissions, platform confirmations, anti-abuse controls.
- Current tests: covered through shared validation and job flow.
- Future work: add clearer manual posting steps and user confirmation workflow.

## eBay

- Current app mode: assisted.
- Official API status: future candidate. No real OAuth, sandbox credentials, Sell API client, or production publishing implementation exists yet.
- Account requirements: eBay seller account, policies, shipping/payment setup, possible OAuth for future official integration.
- What can be prepared: title, description, price, condition, category, location, delivery/shipping options, images.
- What cannot be automated here: official marketplace publish without OAuth/API credentials; final listing confirmation in assisted mode.
- Current tests: assisted validation and job flow only.
- Future work: add official API provider interface, sandbox configuration, token model, mocked Sell API tests, and a real credential runbook using `docs/OFFICIAL_API_CREDENTIAL_CHECKLIST.md`.

## Tweedehands

- Current app mode: assisted/manual reference.
- Official API status: not configured in this repository.
- Account requirements: platform account and manual session.
- What can be prepared: listing data from the central app.
- What cannot be automated here: compliant account login, scraping/posting flows, final submission.
- Current tests: shared adapter validation only.
- Future work: keep legacy scraper/poster scripts separate from the web app and document local-only use.

## Cross-Platform Compliance Position

All current platform integrations are assisted. Jobs may prepare a platform posting package and return `needs_user_action`; they must not claim `published` unless a real official API confirms publication or the user records manual completion with the published URL.

Each registered adapter exposes capability metadata through `GET /api/platforms`. That metadata records prepared fields, account requirements, manual steps, blocked actions, official API status, and final-submission responsibility so the UI can describe platform limits from the same source of truth used by validation and publishing.

The tested platform-by-platform completion contract is maintained in `docs/PLATFORM_COMPLETION_CONTRACTS.md`.
