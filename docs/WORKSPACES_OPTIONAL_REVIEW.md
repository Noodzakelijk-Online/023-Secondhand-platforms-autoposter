# Workspaces Optional Review

Workspaces are not part of the current release scope.

## Decision

Keep the product single-user-account scoped for now. Do not add shared workspaces, teams, roles, invitations, billing seats, or organization-level administration until there is a clear product requirement.

## Rationale

- The current target user is a non-technical seller or small operator managing their own listings.
- Existing owner isolation already protects user-owned listings, jobs, templates, category mappings, platform accounts, exports, imports, analytics, and deletion.
- Adding workspaces would expand the authorization model, data deletion rules, export scope, audit review, billing expectations, and UI complexity.
- Marketplace account credentials and OAuth flows become more sensitive when multiple people can act through a shared account.

## Current Scope Boundaries

| Area | Current behavior | Workspace implication |
| --- | --- | --- |
| Users | Each account owns its own data. | No shared organization owner exists. |
| Listings | Filtered by `owner_id`. | No cross-user listing library. |
| Jobs | Derived from owned listings. | No team queue or assignment model. |
| Platform accounts | Owned by one user. | No shared credential vault. |
| Analytics | User-scoped local aggregates. | No organization analytics. |
| Export/delete | Acts on the authenticated user's data. | No workspace-level retention or legal hold. |

## If Workspaces Are Added Later

Required foundations:

- `Workspace` and `WorkspaceMember` models.
- Role policy for owner/admin/editor/viewer behavior.
- Migration plan from user-owned rows to workspace-owned rows.
- Export, import, and deletion rules for personal versus workspace data.
- Audit events that record actor, workspace, and target resource without leaking secrets.
- UI for switching workspace context and managing members.
- Regression tests for cross-workspace isolation.

## Current Status

Workspaces are deliberately deferred. The app should continue improving single-account owner isolation and assisted-posting workflows before adding team collaboration.

The current single-account SaaS boundary is exposed through `GET /api/account/readiness` and documented in `docs/SAAS_READINESS.md`.
