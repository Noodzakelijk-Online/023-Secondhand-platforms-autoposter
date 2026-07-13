# Final Response Requirements

Use this checklist for the final release response. It prevents a final answer from overstating what the repository proves.

Run `python scripts/final_response_check.py` before writing any final release response. The command must report `ready`; a `blocked` result means the response must describe remaining launch blockers instead of claiming launch completion. Use `python scripts/final_response_check.py --json` to capture the required final-response statements and release-gate status in machine-readable form.

## Required In Final Response

- State the exact release commit.
- State whether `python scripts/verify.py` passed for that commit.
- State whether `docs/RELEASE_EVIDENCE_RECORD.md` is complete.
- State whether `docs/FINAL_ACCEPTANCE_RECORD.md` is accepted.
- State whether `python scripts/release_gate.py` reports `ready`.
- State whether `python scripts/final_response_check.py` reports `ready`.
- State whether the project is release-ready or not release-ready.
- Name any remaining launch blockers.
- Say that all marketplace posting remains assisted unless official API publishing evidence exists.
- Avoid claiming full automation, production readiness, launch, or completion unless the evidence records support it.

## Current Draft Status

Status: not ready for final release response.

The current response must say the project is suitable for continued demo and hardening work, not a final client launch release.
