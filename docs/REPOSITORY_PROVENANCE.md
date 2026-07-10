# Repository Provenance

This document records the repository baseline used for the current completion work. It is evidence for Phase 0, not a final release certificate.

## Current Baseline

- Captured date: 2026-07-10.
- Local branch: `main`.
- Remote: `origin` at `https://github.com/Noodzakelijk-Online/023-Secondhand-platforms-autoposter`.
- Baseline commit before the current local documentation slice: `c96fa18561a1386e3ab2f4da94588f2307427efe`.
- Tracking posture: local `main` tracks `origin/main`; local in-progress phase changes can be dirty until verified, committed, and pushed.

## Evidence Commands

Run these commands when refreshing this artifact:

```bash
git rev-parse --abbrev-ref HEAD
git rev-parse HEAD
git remote -v
git status --short --branch
python scripts/verify.py
```

## Release Rule

A release candidate must not rely on this snapshot alone. Before any final release claim:

- `git status --short --branch` must show the intended branch and no unexpected tracked changes.
- The pushed commit must be the commit that passed `python scripts/verify.py`.
- `docs/COMPLETION_MATRIX.md` and `docs/REQUIREMENTS_TRACEABILITY.md` must agree.
- Local-only files such as `.env`, SQLite data, uploads, caches, and other generated state must remain outside the release evidence.
- This document must be refreshed if the branch, remote, or release baseline changes.
