from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class Check:
    name: str
    command: list[str]


CHECKS = [
    Check("compile", [sys.executable, "-m", "compileall", "app", "tests", "migrations"]),
    Check("tests", [sys.executable, "-m", "pytest"]),
    Check("doctor", [sys.executable, "-m", "app.doctor", "--json"]),
]


def main() -> int:
    for check in CHECKS:
        print(f"==> {check.name}: {' '.join(check.command)}", flush=True)
        result = subprocess.run(check.command, check=False)
        if result.returncode != 0:
            print(f"Verification failed during {check.name}.", file=sys.stderr)
            return result.returncode
    print("Verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
