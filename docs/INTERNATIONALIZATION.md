# Internationalization

The app now has an explicit localization foundation and a frontend copy catalog for the primary dashboard shell.

## Current Decision

- Default locale: `en`.
- Supported locale codes: configured by `SUPPORTED_LOCALES`, defaulting to `en,nl`.
- Fallback locale: `en`.
- UI catalog status: English is complete; Dutch covers the primary dashboard chrome, forms, filters, actions, and settings panels.
- `GET /api/localization` exposes the locale contract to clients.
- The sidebar language selector stores the user's locale in browser local storage.
- English remains the fallback for untranslated dynamic API or operational messages.

## Current Limits

- API validation and operational messages are English-first.
- User language preference is stored in browser local storage, not yet on the user account.
- Some dynamic data-driven labels, marketplace statuses, and diagnostics payloads fall back to English.
- No translated marketplace category catalogs are included yet.

## Rules

- Do not claim server-side/API messages or marketplace catalogs are fully translated.
- Any new locale must appear in `SUPPORTED_LOCALES`.
- `DEFAULT_LOCALE` must be included in `SUPPORTED_LOCALES`.
- English remains the fallback for missing translated strings.

## Future Implementation

To complete internationalization:

- Localize validation, quality assistant, and job status messages.
- Add locale-aware number, currency, and date formatting where user-visible.
- Add browser walkthrough evidence for each supported locale.
