# Autonomy-First Design Review

The product should reduce repetitive listing work without taking control away from the seller or bypassing marketplace rules.

## Autonomy Principles

- The user owns the listing data, account data, exports, imports, and deletion decision.
- The app can prepare, validate, score, and organize listings.
- The app must not bypass login checks, CAPTCHA, two-factor prompts, paid placement choices, neighborhood confirmations, seller policy setup, or marketplace anti-abuse systems.
- Assisted posting packages should be copy-ready, but the user performs final submission on each marketplace unless an official API integration has been proven.
- Suggestions should be reviewable and reversible before save or publish.

## Current Autonomy-Supporting Flows

| Flow | Current behavior | User control point |
| --- | --- | --- |
| Listing creation | User enters master listing data and images. | User saves, edits, duplicates, or deletes listing. |
| Quality assistant | Local deterministic assistant scores readiness and suggests copy. | User chooses whether to apply suggestions. |
| Platform validation | Adapters identify missing fields and mapped fields. | User fixes fields and chooses target platforms. |
| Assisted publishing | Jobs prepare posting packages and links. | User completes login, confirmation, payment, and final posting manually. |
| eBay OAuth foundation | Consent URL and callback state exist. | Token exchange and official API publishing remain blocked until explicitly implemented. |
| Data portability | Export/import and account deletion are self-service. | User initiates export, import, or deletion. |
| Local analytics | Dashboard derives aggregate insights locally. | No external tracking or cross-user analytics. |

## Automation Boundaries

Allowed now:

- Drafting structured field packages.
- Running local validation and quality checks.
- Queueing assisted jobs.
- Recording job logs and attempts.
- Producing local analytics.

Blocked until further evidence:

- Automatic marketplace submission.
- Browser automation against protected platform flows.
- eBay official API publishing.
- Storing raw OAuth access or refresh tokens in app tables.
- Claims that a marketplace listing is published without official API success or user-confirmed manual completion.

## Design Risks

- A button labeled too strongly could imply automatic posting. UI and docs must keep assisted wording.
- Applying quality suggestions should never overwrite user copy without a visible action.
- Analytics should remain aggregate and local to avoid becoming hidden behavior tracking.
- Official API foundations must stay fail-closed until secret-manager-backed token exchange exists.

## Next Improvements

- Add explicit user-confirmed manual completion for assisted jobs, including platform URL capture.
- Add clearer UI text around `needs_user_action` jobs.
- Add browser walkthrough evidence proving non-technical users understand where manual action is required.
- Keep this review aligned with `docs/FALSE_COMPLETION_PREVENTION.md`.
