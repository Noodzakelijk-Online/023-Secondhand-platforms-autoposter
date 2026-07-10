# Internationalization

The app now has an explicit localization foundation, but the user interface is not fully translated.

## Current Decision

- Default locale: `en`.
- Supported locale codes: configured by `SUPPORTED_LOCALES`, defaulting to `en,nl`.
- Fallback locale: `en`.
- UI catalog status: English is complete; Dutch is declared as supported for future rollout but incomplete.
- `GET /api/localization` exposes the locale contract to clients.

## Current Limits

- Most visible frontend copy remains hardcoded English.
- API validation and operational messages are English-first.
- No per-user language preference is stored yet.
- No translated marketplace category catalogs are included yet.

## Rules

- Do not claim the app is multilingual until visible UI copy has a catalog and browser evidence.
- Any new locale must appear in `SUPPORTED_LOCALES`.
- `DEFAULT_LOCALE` must be included in `SUPPORTED_LOCALES`.
- English remains the fallback for missing translated strings.

## Future Implementation

To complete internationalization:

- Add a frontend copy catalog.
- Store a user or browser-selected locale.
- Localize validation, quality assistant, and job status messages.
- Add locale-aware number, currency, and date formatting where user-visible.
- Add browser walkthrough evidence for each supported locale.
