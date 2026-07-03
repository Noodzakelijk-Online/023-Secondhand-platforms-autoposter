# UI Action Audit

Visible actions and backing API routes:

| UI Action | API Route | Status |
| --- | --- | --- |
| Register/login/logout | `/api/auth/*` | Wired |
| Create/edit/delete listing | `/api/listings*` | Wired |
| Upload/reorder/delete image | `/api/listings/{id}/images*` | Wired |
| Validate platform readiness | `/api/listings/{id}/validate` | Wired |
| Queue publish package | `/api/listings/{id}/publish` | Wired |
| Retry job | `/api/jobs/{id}/retry` | Wired |
| Confirm manual completion | `/api/jobs/{id}/confirm-completion` | Wired |
| Create/delete platform account | `/api/accounts*` | Wired |
| Export/import/delete account data | `/api/export`, `/api/import`, `/api/auth/me` | Wired |
| Inspect audit history | `/api/audit-events` | API-only; no dedicated UI yet |

No visible action is intended to claim automatic platform publishing in assisted mode.
