from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.release_gate import release_gate_result  # noqa: E402

FINAL_RESPONSE_REQUIREMENTS = ROOT / "docs" / "FINAL_RESPONSE_REQUIREMENTS.md"
FINAL_ACCEPTANCE = ROOT / "docs" / "FINAL_ACCEPTANCE_RECORD.md"


REQUIRED_STATEMENTS = [
    "exact release commit",
    "verification result for that commit",
    "release evidence record completeness",
    "final acceptance status",
    "release gate status",
    "release-ready or not release-ready decision",
    "remaining launch blockers",
    "assisted marketplace posting unless official API publishing evidence exists",
]


@dataclass(frozen=True)
class FinalResponseCheckResult:
    status: str
    blockers: list[str]
    required_statements: list[str]
    release_gate_status: str
    release_gate_blockers: list[str]
    total_missing_evidence: int


def final_response_check_result() -> FinalResponseCheckResult:
    blockers = []
    requirements = FINAL_RESPONSE_REQUIREMENTS.read_text(encoding="utf-8")
    acceptance = FINAL_ACCEPTANCE.read_text(encoding="utf-8")
    release_gate = release_gate_result()

    if "Status: not ready for final release response." in requirements:
        blockers.append("Final response requirements say the final release response is not ready.")
    if "Status: not accepted." in acceptance or "Decision | Not accepted" in acceptance:
        blockers.append("Final acceptance record is not accepted.")
    if release_gate.status != "ready":
        blockers.append("Release gate is not ready.")

    return FinalResponseCheckResult(
        status="blocked" if blockers else "ready",
        blockers=blockers,
        required_statements=REQUIRED_STATEMENTS,
        release_gate_status=release_gate.status,
        release_gate_blockers=release_gate.blockers,
        total_missing_evidence=release_gate.total_missing_evidence,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Check whether a final release response can be safely written.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args()
    result = final_response_check_result()

    if args.json:
        print(json.dumps(asdict(result), indent=2))
    else:
        print(f"Final response status: {result.status}")
        for blocker in result.blockers:
            print(f"- {blocker}")
        print("Required statements:")
        for statement in result.required_statements:
            print(f"- {statement}")
        print(f"Release gate status: {result.release_gate_status}")
        print(f"Total missing evidence: {result.total_missing_evidence}")
    return 0 if result.status == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
