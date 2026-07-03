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
- Official API status: eligible when configured. eBay's official developer documentation describes OAuth tokens, developer application keys, scopes, Sandbox/Production environments, and a Sell Inventory `publishOffer` endpoint, but this repository has no real OAuth, sandbox credentials, Sell API client, or production publishing implementation yet.
- Account requirements: eBay seller account, policies, shipping/payment setup, possible OAuth for future official integration.
- What can be prepared: title, description, price, condition, category, location, delivery/shipping options, images.
- What cannot be automated here: official marketplace publish without OAuth/API credentials; final listing confirmation in assisted mode.
- Current tests: assisted validation, job flow, and platform credential metadata contract.
- Future work: add official API provider interface, sandbox configuration, token reference model, official-doc-linked Sell API tests, and real credential runbook using `docs/OFFICIAL_API_CREDENTIAL_CHECKLIST.md`.
- External blockers: approved eBay developer application, OAuth scopes/RuName, sandbox/production credential access, marketplace policy approval, and managed secret storage.

## Tweedehands

- Current app mode: assisted/manual reference.
- Official API status: not configured in this repository.
- Account requirements: platform account and manual session.
- What can be prepared: listing data from the central app.
- What cannot be automated here: compliant account login, scraping/posting flows, final submission.
- Current tests: shared adapter validation only.
- Future work: keep legacy scraper/poster scripts separate from the web app and document local-only use.

## Cross-Platform Compliance Position

All current platform integrations are assisted. Jobs may prepare a platform posting package and return `needs_user_action`; they must not claim `published` unless a real official API confirms publication or a user confirmation feature is added and records the published URL.

Platform account records are metadata only. New account metadata requests reject raw secret-like keys such as passwords, access tokens, API keys, and private keys in `connection_data`. Future official API integrations must store credentials in a real secret manager and reference them without exposing raw values to exports, audit logs, or frontend responses.

`GET /api/platforms` exposes `official_api_status`, `credential_requirements`, and `automation_blockers` so the UI can show provider reality without creating fake connect or publish controls.
