# Non-Technical User Simulation

This is a proxy simulation, not a substitute for observing a real non-technical user. It defines the walkthrough that must be executed before final release and records what the current product should be able to support.

## Persona

Mira is a casual secondhand seller who wants to list a desk lamp on several marketplaces. She is comfortable using web forms, but she does not understand API credentials, background workers, migrations, or marketplace automation limits.

## Scenario

Mira wants to:

1. Create an account.
2. Add one reusable listing with a photo.
3. Improve the listing copy.
4. Prepare posting packages for Marktplaats and eBay.
5. Understand why final posting is manual.
6. Check whether any jobs need action.
7. Export her data.
8. Delete her account data.

## Expected Walkthrough

| Step | User action | Expected app behavior | Current status |
| --- | --- | --- | --- |
| 1 | Register with email and password. | Account is created and the dashboard opens. | Supported by auth flow and tests. |
| 2 | Click New listing and fill title, price, condition, category, location, and description. | Listing saves as a draft with revision tracking. | Supported. |
| 3 | Upload a product image. | Image is validated, stored, deduplicated, and shown in the editor. | Supported. |
| 4 | Run Quality assistant. | App shows score, concrete fixes, and optional suggestions. | Supported. |
| 5 | Apply a suggestion. | Suggestion changes form fields only after explicit user action. | Supported. |
| 6 | Select platforms and validate. | App reports missing fields and copy-ready mapped fields. | Supported. |
| 7 | Queue assisted package. | App creates assisted jobs and labels final action as user-controlled. | Supported. |
| 8 | Open Queue. | User can inspect job status, logs, retry where relevant, and see needs-action context. | Partially supported; clearer manual-completion capture is still needed. |
| 9 | Export JSON. | Export excludes secrets, sessions, and image binaries. | Supported. |
| 10 | Delete account data. | Owned records and uploaded images are removed. | Supported. |

## Observed Risk Areas To Test With A Real User

- Whether "Queue assisted package" is understandable without implying automatic marketplace submission.
- Whether `needs_user_action` explains the next manual step clearly enough.
- Whether platform warnings are visible before the user leaves the app.
- Whether the quality assistant feels advisory rather than surprising.
- Whether export/import/delete language is clear enough for a non-technical seller.
- Whether mobile layout remains usable during listing editing.

## Release Gate

Before this phase can be marked `Done`, a real non-technical user walkthrough must be executed and recorded with:

- date
- observer
- browser/device
- whether the user completed each step without coaching
- confusion points
- UI copy changes made afterward
- final acceptance or remaining blockers

## Current Verdict

The core flow is ready for a real non-technical walkthrough, but that walkthrough has not yet been executed. This phase remains partial until external user evidence exists.
