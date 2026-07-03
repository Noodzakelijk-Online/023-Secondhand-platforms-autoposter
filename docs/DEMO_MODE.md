# Demo Mode Without Fake Production

`DEV_AUTO_LOGIN=true` is a local development shortcut only. It is not a production authentication mode and must not be used for client data.

## Behavior

- Demo mode only works when `APP_ENV=development`.
- Requests without a bearer token receive a non-persistent session object for the reserved user `demo@local.autoposter.invalid`.
- The demo user is created on demand with the display name `Local Demo User`.
- The reserved `.invalid` email makes the account visibly non-real and prevents accidental collision with a client email.
- `python -m app.doctor --json` reports whether demo mode is active.

## Safety Rules

- `DEV_AUTO_LOGIN` is blocked by startup safety in production.
- Non-development environments return `403` if `DEV_AUTO_LOGIN=true`.
- Do not use demo mode to seed, import, export, or present real customer data.
- Disable demo mode before running acceptance checks for real authentication.
