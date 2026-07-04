# Auth Security Posture

The current deployment mode is bearer-token authentication only.

## Current Mode

- `AUTH_TRANSPORT=bearer` is the only supported value.
- Login and registration return a bearer token in the JSON response body.
- Authenticated requests must send `Authorization: Bearer <token>`.
- The application does not set session cookies.
- Logout revokes the server-side session record for the bearer token.
- Session expiry is controlled by `SESSION_EXPIRE_HOURS`.

Because browsers do not automatically attach bearer tokens from application state the way they attach cookies, API authentication is not currently exposed to normal cookie-based CSRF. The app still restricts CORS in production and sends security headers, but there is no CSRF token middleware because there are no authenticated cookie sessions to protect.

## Production Controls

- Set `APP_ENV=production`.
- Keep `AUTH_TRANSPORT=bearer`.
- Restrict `CORS_ORIGINS` to trusted frontend origins.
- Serve the app only over HTTPS so bearer tokens are not sent over plaintext connections.
- Store bearer tokens only in the frontend runtime needed by the static dashboard; do not copy them into logs, URLs, analytics, screenshots, or exports.
- Use `POST /api/auth/logout` to revoke a session when the user signs out.

## If Cookie Auth Is Added Later

Cookie-based auth must not be enabled by configuration alone. It requires a code change and a new security review covering:

- `HttpOnly`, `Secure`, and `SameSite` cookie attributes
- CSRF token generation, storage, and validation for unsafe HTTP methods
- login/logout cookie rotation and clearing behavior
- CORS and credentialed request settings
- tests proving cross-site unsafe requests are rejected

Until that work exists, startup rejects unsupported `AUTH_TRANSPORT` values.
