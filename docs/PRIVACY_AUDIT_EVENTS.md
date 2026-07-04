# Privacy Audit Events

The app records local audit events for user data export, data import, and self-service account deletion. These events are intended for operator troubleshooting and privacy accountability without storing exported payloads, raw platform secrets, or raw user email addresses.

## Recorded Actions

- `data_exported`: written after a successful JSON export.
- `data_imported`: written after import payload processing and before commit.
- `account_deleted`: written before owned user data is purged, and retained after the user row is removed.

## Stored Fields

- `user_id`: the local user ID at the time of the event. It is not a foreign key, so deletion events can remain after account deletion.
- `user_email_hash`: SHA-256 hash of the normalized email address.
- `action`: event type.
- `event_data`: aggregate counts only, such as listings exported or images deleted.
- `created_at`: event timestamp.

## Boundaries

- Audit events do not store passwords, bearer tokens, platform access tokens, platform secret references, exported listing content, imported JSON payloads, or raw email addresses.
- Account deletion removes user-owned business data and sessions, but leaves the sanitized `account_deleted` audit event.
- There is not yet an admin UI or retention policy for audit events; those remain release-hardening work.
