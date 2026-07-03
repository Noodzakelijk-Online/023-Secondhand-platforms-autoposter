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

## Operational Requirements

- Set a strong `SECRET_KEY` before production use.
- Use HTTPS and restrict `CORS_ORIGINS`.
- Run Alembic migrations explicitly with `AUTO_CREATE_TABLES=false`.
- Store official provider secrets only in environment variables or a managed secret store.
- Do not enable unsupported browser automation in production.

## Known Gaps

- Distributed rate limiting is not implemented.
- Cookie/CSRF deployment mode is not implemented.
- Formal threat model and penetration test are not complete.

