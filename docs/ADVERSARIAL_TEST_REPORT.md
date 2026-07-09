# Adversarial Test Report

Date: 2026-07-09

This report maps adversarial concerns to current automated coverage. It is not a penetration test; it records what the repository can prove locally today.

## Automated Coverage

| Area | Test evidence | Result |
| --- | --- | --- |
| Bearer-only auth posture | `tests/test_auth_security.py` | Cookies alone do not authenticate; logout revokes sessions. |
| Password storage | `tests/test_auth_security.py` | New passwords use Argon2; legacy PBKDF2 hashes upgrade after successful login. |
| Login throttling | `tests/test_auth_security.py` | Failed attempts are persisted in `login_throttles` and rate-limited. |
| Owner isolation | `tests/test_owner_isolation.py` | Cross-user reads and mutations are blocked for core owned resources. |
| API hardening | `tests/test_api_hardening.py` | Request IDs, structured errors, route tags, metrics, pagination, and filters are covered. |
| Upload safety | `tests/test_storage_uploads.py` | Filename sanitization, MIME/signature checks, duplicate handling, deletion, and ordering are covered. |
| Export privacy | `tests/test_data_portability.py` | Exports exclude password hashes, sessions, and sensitive account fields. |
| Platform honesty | `tests/test_no_mocks_production.py`, `tests/test_fake_provider_lab.py` | Production adapters do not fake published success; fake provider stays test-only. |
| Job state safety | `tests/test_worker.py`, `tests/test_job_state.py` | Queue claims, retries, cooldowns, stale recovery, and state transitions are covered. |
| Startup safety | `tests/test_startup_safety.py` | Unsafe production defaults and unsupported modes are rejected. |
| Migration safety | `tests/test_migrations.py` | Empty-database migration reaches current head and includes security tables. |
| Legacy isolation | `tests/test_legacy_quarantine.py`, `tests/test_doctor.py` | Web app import path does not load Selenium, LastPass, spaCy, or legacy modules. |

## Manual Gaps

- Browser-based accessibility and keyboard walkthroughs are not executed in automated tests.
- Multi-worker PostgreSQL locking behavior is not proven by the SQLite suite.
- Deployment-edge throttling, CORS, TLS, backup location, and worker supervision depend on target infrastructure.
- Official API OAuth flows do not exist yet and therefore have no sandbox adversarial tests.

## Current Command Evidence

The current local verification gate is:

```bash
python scripts/verify.py
```

At the time of this report, the gate passed with 73 tests. Doctor returned a local-development warning that the SQLite database is not stamped at the latest Alembic revision; this is expected for the current local database and remains a release-readiness item.

