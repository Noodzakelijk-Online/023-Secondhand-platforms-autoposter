# Supply Chain And Dependencies

The production application dependencies are declared in `requirements.txt`. Legacy browser-automation dependencies remain isolated in `requirements-legacy.txt` and are not installed for the FastAPI app.

## Vulnerability Audit

Run the dependency audit with:

```bash
python -m pip install pip-audit==2.9.0
python scripts/audit_dependencies.py
```

The script audits `requirements.txt` with `pip-audit --strict`. The GitHub Actions workflow `.github/workflows/supply-chain.yml` runs the same audit on pushes, pull requests, a weekly schedule, and manual dispatch.

## Dependency Rules

- Pin direct dependencies unless a bounded compatibility range is intentional.
- Keep legacy Selenium/browser automation dependencies out of the production install.
- Do not add marketplace SDKs until official API credentials, sandbox tests, and the credential checklist are ready.
- Treat audit failures as release blockers unless a documented temporary exception is approved.
- Document any exception with package name, advisory ID, reason, compensating controls, owner, and expiry date.

## Current Exceptions

None.
