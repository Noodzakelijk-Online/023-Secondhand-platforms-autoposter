from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELEASE_READINESS = ROOT / "docs" / "RELEASE_READINESS.md"
RELEASE_EVIDENCE = ROOT / "docs" / "RELEASE_EVIDENCE_RECORD.md"
USER_WALKTHROUGH = ROOT / "docs" / "NON_TECHNICAL_USER_WALKTHROUGH_RECORD.md"
FINAL_ACCEPTANCE = ROOT / "docs" / "FINAL_ACCEPTANCE_RECORD.md"


@dataclass(frozen=True)
class ReleaseGateResult:
    status: str
    blockers: list[str]
    missing_evidence: dict[str, list[str]]
    missing_evidence_counts: dict[str, int]
    total_missing_evidence: int


def _missing_evidence_rows(markdown: str) -> list[str]:
    missing = []
    section = ""
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            section = stripped.removeprefix("## ").strip()
            continue
        if not stripped.startswith("|") or "Not captured" not in stripped:
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if not cells or cells[0] == "---":
            continue
        if cells[0].isdigit() and len(cells) > 1:
            field = cells[1]
        else:
            field = cells[0]
        missing.append(f"{section} / {field}" if section else field)
    return missing


def release_gate_result() -> ReleaseGateResult:
    blockers = []
    missing_evidence = {}
    release_readiness = RELEASE_READINESS.read_text(encoding="utf-8")
    release_evidence = RELEASE_EVIDENCE.read_text(encoding="utf-8")
    user_walkthrough = USER_WALKTHROUGH.read_text(encoding="utf-8")
    final_acceptance = FINAL_ACCEPTANCE.read_text(encoding="utf-8")
    release_missing = _missing_evidence_rows(release_evidence)
    walkthrough_missing = _missing_evidence_rows(user_walkthrough)
    acceptance_missing = _missing_evidence_rows(final_acceptance)

    if "Status: not release-ready yet." in release_readiness:
        blockers.append("Release readiness still says not release-ready yet.")
    if release_missing:
        blockers.append("Release evidence record still has Not captured entries.")
        missing_evidence["docs/RELEASE_EVIDENCE_RECORD.md"] = release_missing
    if walkthrough_missing:
        blockers.append("Non-technical user walkthrough record still has Not captured entries.")
        missing_evidence["docs/NON_TECHNICAL_USER_WALKTHROUGH_RECORD.md"] = walkthrough_missing
    if acceptance_missing:
        missing_evidence["docs/FINAL_ACCEPTANCE_RECORD.md"] = acceptance_missing
    if "Status: not accepted." in final_acceptance or "Decision | Not accepted" in final_acceptance:
        blockers.append("Final acceptance record is not accepted.")

    missing_evidence_counts = {source: len(fields) for source, fields in missing_evidence.items()}

    return ReleaseGateResult(
        status="blocked" if blockers else "ready",
        blockers=blockers,
        missing_evidence=missing_evidence,
        missing_evidence_counts=missing_evidence_counts,
        total_missing_evidence=sum(missing_evidence_counts.values()),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Check whether final release evidence gates are complete.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args()
    result = release_gate_result()

    if args.json:
        print(json.dumps(asdict(result), indent=2))
    else:
        print(f"Release gate status: {result.status}")
        for blocker in result.blockers:
            print(f"- {blocker}")
        if result.missing_evidence:
            print(f"Missing evidence: {result.total_missing_evidence} item(s)")
            for source, fields in result.missing_evidence.items():
                print(f"- {source}: {result.missing_evidence_counts[source]} item(s)")
                for field in fields:
                    print(f"  - {field}")
    return 0 if result.status == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
