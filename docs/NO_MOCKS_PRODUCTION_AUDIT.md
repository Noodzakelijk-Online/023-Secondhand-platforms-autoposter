# No Mocks In Production Audit

This audit records the current production integration posture: registered marketplace adapters are assisted-only and do not fake external marketplace success.

## Current Findings

- Registered adapters: Marktplaats, Koopplein, Nextdoor, eBay, Tweedehands.
- All registered adapters expose `automation_mode="assisted"`.
- A ready listing returns `needs_user_action`, not `published`.
- Assisted adapters do not create fake platform listing IDs.
- Legacy Selenium scripts are not imported by the FastAPI app.
- Official API automation remains blocked until real credential, sandbox, and checklist work is complete.

## Test Coverage

`tests/test_no_mocks_production.py` verifies that every registered production adapter:

- remains in assisted mode,
- does not return `published` for a prepared listing,
- does not invent a platform listing ID,
- includes assisted-mode metadata in the prepared package.

## Rules

- Production adapters must not use fake external success responses.
- Fake local API responses are allowed only inside tests for future official API providers.
- A job can be marked `published` only after an official API confirms publication or a future explicit user-confirmation flow records the platform URL.
- Documentation and UI copy must say `needs_user_action` for assisted packages.
