from __future__ import annotations

import subprocess
import sys


def main() -> int:
    command = [
        sys.executable,
        "-m",
        "pip_audit",
        "--requirement",
        "requirements.txt",
        "--strict",
    ]
    print(f"==> dependency-audit: {' '.join(command)}", flush=True)
    result = subprocess.run(command, check=False)
    if result.returncode != 0:
        print("Dependency audit failed.", file=sys.stderr)
        return result.returncode
    print("Dependency audit passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
