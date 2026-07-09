# Legacy Selenium Scripts

The old Selenium/browser automation scripts were moved out of the repository root.

They now live under:

```text
legacy/selenium/
```

These scripts are retained only as local reference/manual tooling. They are not part of the FastAPI web app, Docker startup, worker startup, production dependencies, or verification gate.

Use them only in a user-controlled local browser session, and only when platform terms, account permissions, login checks, CAPTCHA flows, payment choices, and anti-abuse controls are respected.

Install `requirements-legacy.txt` only if you deliberately need to inspect or run that old tooling in a compatible local environment.

