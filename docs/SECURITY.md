# Security

## Current Controls

- Argon2 password hashing for new passwords.
- Legacy PBKDF2 password verification with rehash on login.
- Bearer sessions stored as token hashes with expiration and revocation.
- Owner checks on user-owned records.
- Failed login throttling per email/IP in process memory.
- Upload filename sanitization, size checks, MIME/signature validation, checksums, and listing-scoped storage paths.
- Security headers and request IDs in middleware.
- No raw platform passwords are stored by the web app.
- Security and privacy-sensitive user actions are recorded in `audit_events` with summary-only details.
- Export/import and account deletion produce audit evidence without storing exported payloads, passwords, bearer tokens, or platform secrets.
- New platform account metadata requests reject raw secret-like keys in `connection_data`; use an external secret manager for real credentials.

## Operational Requirements

- Set a strong `SECRET_KEY` before production use.
- Use HTTPS and restrict `CORS_ORIGINS`.
- Run Alembic migrations explicitly with `AUTO_CREATE_TABLES=false`.
- Store official provider secrets only in environment variables or a managed secret store.
- Do not send raw provider passwords, OAuth access tokens, API keys, or private keys in `connection_data`; the API rejects those keys for new account metadata.
- Do not enable unsupported browser automation in production.

## Known Gaps

- Distributed rate limiting is not implemented.
- Cookie/CSRF deployment mode is not implemented.
- Formal threat model and penetration test are not complete.
- Audit events are application-level records, not immutable append-only ledger storage.
