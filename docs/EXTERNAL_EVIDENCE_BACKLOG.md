# External Evidence Backlog

This backlog is the single list of remaining `Partial` phases. A phase can leave this list only when the completion matrix is updated with matching evidence.

| Phase | Evidence required | Capture location |
| --- | --- | --- |
| 4 | Run Alembic migrations against the target PostgreSQL database and record the applied head. | `docs/RELEASE_EVIDENCE_RECORD.md` |
| 5 | Capture deployment-specific environment, production startup, CORS, secret, storage, and log-mode evidence from the chosen host. | `docs/RELEASE_EVIDENCE_RECORD.md` |
| 6 | Capture edge/proxy/CDN/WAF rate-limit evidence for the chosen deployment. | `docs/RELEASE_EVIDENCE_RECORD.md` |
| 18 | Verify concurrent worker claim and recovery behavior against the target PostgreSQL database. | `docs/RELEASE_EVIDENCE_RECORD.md` |
| 70 | Complete final launch evidence and make `python scripts/release_gate.py` report `ready`. | `docs/RELEASE_EVIDENCE_RECORD.md` |
| 74 | Observe a real non-technical user completing the seller flow without substituting internal QA or automation. | `docs/NON_TECHNICAL_USER_WALKTHROUGH_RECORD.md` |
| 81 | Complete or explicitly accept the external implementation-depth gates. | `docs/FINAL_ACCEPTANCE_RECORD.md` |
| 85 | Repeat the final no-excuses search after release evidence exists and before final acceptance. | `docs/FINAL_NO_EXCUSES_SEARCH.md` |
| 87 | Capture an accepted final launch decision with residual risks and owners. | `docs/FINAL_ACCEPTANCE_RECORD.md` |
| 88 | Prepare the final release response only after release gate and final acceptance are ready. | `docs/FINAL_RESPONSE_REQUIREMENTS.md` |

Current status: blocked on external evidence. The local repository has controls and templates for every row above, but it does not contain the external observations or deployment records required to mark these phases done.
