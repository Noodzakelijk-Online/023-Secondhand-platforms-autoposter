# Goal Completion Matrix

The active completion matrix is maintained in `docs/COMPLETION_MATRIX.md`.

This file exists because the Giant Codex Goal Prompt names `docs/GOAL_COMPLETION_MATRIX.md` as a final artifact. Keep the two files aligned if this repository later renames the primary matrix.

Additional Giant Prompt phase coverage not yet represented as numbered rows in `docs/COMPLETION_MATRIX.md`:

| Prompt Phase | Status | Evidence |
| --- | --- | --- |
| 101. Support/debug bundle design | Partial | `scripts/support_bundle.py` creates a redacted ZIP with doctor output, git state, and selected docs; excludes `.env`, databases, uploads, caches, venvs, and raw credentials. Production incident templates and admin upload flows are not implemented. |
