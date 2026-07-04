# Acceptance Tests

Run:

```bash
python scripts/verify.py
```

Core acceptance coverage currently includes:

| Area | Evidence |
| --- | --- |
| Auth/session flow | `tests/test_api.py`, `tests/test_auth_security.py` |
| Listing CRUD and owner isolation | `tests/test_api.py`, `tests/test_api_hardening.py` |
| Image upload safety | `tests/test_storage_uploads.py` |
| Platform validation and assisted publish package | `tests/test_api.py`, `tests/test_category_mappings.py` |
| Worker/job processing, claim-once behavior, and stale recovery | `tests/test_worker.py` |
| Manual completion/final URL/history | `tests/test_api.py::test_manual_completion_records_final_url_and_history` |
| Privacy audit events | `tests/test_data_portability.py` |
| Platform account secret rejection | `tests/test_api_hardening.py::test_platform_account_rejects_raw_secret_connection_data` |
| Platform credential reality metadata | `tests/test_api.py::test_platform_metadata_contract` |
| Static UI accessibility baseline | `tests/test_static_ui_audit.py`, `scripts/audit_static_ui.py` |
| Support/debug bundle safety | `tests/test_support_bundle.py` |
| Local backup/restore guardrails | `tests/test_local_backup_restore.py` |
| Migration smoke | `tests/test_migrations.py` |
| Doctor diagnostics | `tests/test_doctor.py` |

## Manual Smoke

1. Start the app with `uvicorn app.main:app --reload`.
2. Register a user.
3. Create a listing with title, description, category, price, condition, location, and at least one image.
4. Select Marktplaats and validate.
5. Queue publish.
6. Open the queue item and confirm it is `needs_user_action`.
7. Complete the external platform step manually.
8. Paste the final platform URL into the manual completion form.
9. Confirm the job becomes `published`, the mapping stores the URL, and the log says manual completion was confirmed by the user.
10. Call `GET /api/audit-events` and confirm owner-scoped audit events exist for the listing, publish, export/import, or manual completion actions performed.
11. For a local SQLite install, run `python scripts/backup_local_data.py --confirm-private-data`, restore into a disposable target with `python scripts/restore_local_data.py <backup> --confirm-overwrite`, and verify the database plus uploads round trip before relying on the backup.
12. Run `python scripts/audit_static_ui.py` and confirm the static accessibility baseline passes before any browser/manual accessibility review.
