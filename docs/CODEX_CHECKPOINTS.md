# Codex Checkpoints

## Checkpoint 2026-07-03

### After Platform-Secret-Boundary Pass

- Current branch: `main`.
- Starting commit for this pass: `17365fb`.
- PR: `https://github.com/Noodzakelijk-Online/023-Secondhand-platforms-autoposter/pull/1`.
- Added raw secret rejection for new platform account metadata.
- Verification target: `.venv/bin/python scripts/verify.py`.
- Remaining high-value next work: official OAuth/secret-manager references, browser E2E, accessibility audit, worker locking, distributed rate limits, backup/restore, and final release dry run.

### After Local-Backup-Restore Pass

- Current branch: `main`.
- Starting commit for this pass: `59079f9`.
- PR: `https://github.com/Noodzakelijk-Online/023-Secondhand-platforms-autoposter/pull/1`.
- Added guarded local SQLite/upload private backup and restore scripts with tests.
- Verification target: `.venv/bin/python scripts/verify.py`.
- Remaining high-value next work: browser E2E, official API credential checklist, storage abstraction beyond local filesystem, production backup drills, worker concurrency locking, distributed rate limits, and final release dry run.

### After Provider-Credential-Reality Pass

- Current branch: `main`.
- Starting commit for this pass: `6d19f32`.
- PR: `https://github.com/Noodzakelijk-Online/023-Secondhand-platforms-autoposter/pull/1`.
- Added platform official API status, credential requirements, automation blockers, UI display, and API tests.
- Verification target: `.venv/bin/python scripts/verify.py`.
- Remaining high-value next work: browser E2E, accessibility audit, actual OAuth/secret-manager implementation, worker concurrency locking, distributed rate limits, and final release dry run.

### After Worker-Claiming Pass

- Current branch: `main`.
- Starting commit for this pass: `3678c0f`.
- PR: `https://github.com/Noodzakelijk-Online/023-Secondhand-platforms-autoposter/pull/1`.
- Added database due-job claiming and test coverage that a second worker session cannot claim the same queued job.
- Verification target: `.venv/bin/python scripts/verify.py`.
- Remaining high-value next work: stale running-job recovery, browser E2E, accessibility audit, actual OAuth/secret-manager implementation, distributed rate limits, and final release dry run.

### After Support-Bundle Pass

- Current branch: `main`.
- Starting commit for this pass: `7a10f82`.
- PR: `https://github.com/Noodzakelijk-Online/023-Secondhand-platforms-autoposter/pull/1`.
- Added redacted support/debug bundle generation and tests.
- Verification target: `.venv/bin/python scripts/verify.py`.
- Remaining high-value next work: backup/restore, official OAuth/secret-manager references, browser E2E, accessibility audit, worker locking, distributed rate limits, and final release dry run.

### After Audit-Event Pass

- Current branch: `main`.
- Starting commit for this pass: `2898fe4`.
- PR: `https://github.com/Noodzakelijk-Online/023-Secondhand-platforms-autoposter/pull/1`.
- Added audit events for state-changing and privacy-sensitive workflows.
- Verification target: `.venv/bin/python scripts/verify.py`.
- Remaining high-value next work: browser E2E, accessibility audit, provider credential checklist, worker locking, distributed rate limits, backup/restore, and final release dry run.

### After Assisted-Completion Pass

- Current branch: `main`.
- Starting commit: `bad1e2b`.
- Critical path focus: assisted job final URL confirmation.
- Verification target: `python scripts/verify.py`.
- Remaining high-value next work: browser E2E, official API credential checklist, storage abstraction beyond local filesystem, production backup drills, worker concurrency locking, distributed rate limits, and final release dry run.
