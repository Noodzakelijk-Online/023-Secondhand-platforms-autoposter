# Progressive Stabilization Gates

These gates define how the project moves from local hardening to a real launch candidate. A later gate cannot compensate for a failed earlier gate.

## Gate 1: Local Integrity

Required evidence:

- `python scripts/verify.py` passes.
- `docs/COMPLETION_MATRIX.md` and `docs/REQUIREMENTS_TRACEABILITY.md` are synchronized.
- No production-facing docs claim full automation for assisted platforms.
- New endpoints have tests or a documented reason they are operator-only.

Exit rule: local development may continue, but no release candidate can be named until this gate is green.

## Gate 2: Data And Security Safety

Required evidence:

- Production startup rejects default secrets, wildcard CORS, and unsupported auth/storage/log modes.
- Exports omit passwords, session tokens, platform tokens, secret references, and image binaries.
- Account deletion removes owned business data and uploaded files.
- OAuth/API foundations store only secret references, not raw access or refresh tokens.

Exit rule: deployment dry runs may begin only after this gate is green.

## Gate 3: Workflow Completeness

Required evidence:

- A non-technical user can register, create a listing, upload an image, use quality guidance, validate platforms, queue assisted posting, inspect job output, export data, and delete the account.
- Browser, responsive, and accessibility walkthrough findings are recorded.
- Any visible action either works against a real endpoint or is removed from the UI.

Exit rule: release-readiness review may begin only after this gate is green.

## Gate 4: Deployment Proof

Required evidence:

- Fresh-clone verification passes.
- Alembic head is applied to the target database.
- API and worker process status are captured.
- Upload storage is persistent and covered by backup/restore evidence.
- Production doctor output has no launch-blocking errors.

Exit rule: final acceptance may begin only after this gate is green.

## Gate 5: Marketplace And Launch Acceptance

Required evidence:

- Assisted-posting limitations are accepted by the client/user.
- No platform is represented as fully automated without official API credential, sandbox, quota, and policy evidence.
- Final no-excuses search is complete.
- Final acceptance criteria and known residual risks are documented.

Exit rule: launch can proceed only with explicit acceptance of remaining partial phases.

## Current Gate Status

| Gate | Status | Reason |
| --- | --- | --- |
| Gate 1 | Passing locally | Verification passes; matrix and traceability are guarded by tests. |
| Gate 2 | Partial | Core safety tests and OAuth token-exchange foundations exist; deployment-specific secret-manager proof remains. |
| Gate 3 | Partial | Core workflow exists; executed browser/accessibility walkthrough evidence remains. |
| Gate 4 | Partial | Local verification exists; fresh-clone and target deployment evidence remain. |
| Gate 5 | Not started | Final search and acceptance are intentionally release-end activities. |
