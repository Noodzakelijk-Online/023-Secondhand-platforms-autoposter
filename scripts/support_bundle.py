from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import zipfile


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import get_settings
from app.doctor import run_checks

DEFAULT_DOCS = [
    "Readme.md",
    "docs/TECHNICAL_AUDIT.md",
    "docs/CRITICAL_PATH.md",
    "docs/ACCEPTANCE_TESTS.md",
    "docs/FINAL_VERIFICATION_REPORT.md",
    "docs/SECURITY.md",
    "docs/OPERATOR_RUNBOOK.md",
    "docs/COMPLETION_MATRIX.md",
]
SENSITIVE_ENV_FRAGMENTS = ("SECRET", "TOKEN", "PASSWORD", "KEY", "CREDENTIAL")


def run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return result.stderr.strip()
    return result.stdout.strip()


def safe_environment_summary() -> dict:
    settings = get_settings()
    configured_names = []
    for name in sorted(type(settings).model_fields):
        env_name = name.upper()
        if any(fragment in env_name for fragment in SENSITIVE_ENV_FRAGMENTS):
            configured_names.append({"name": env_name, "value": "<redacted>"})
        else:
            configured_names.append({"name": env_name, "value": str(getattr(settings, name))})
    return {
        "note": "Secret-like settings are redacted; .env files are not included in support bundles.",
        "settings": configured_names,
    }


def build_manifest() -> dict:
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "purpose": "Secondhand Autoposter support/debug bundle",
        "exclusions": [
            ".env files",
            "local databases",
            "uploaded media",
            "virtual environments",
            "pytest/cache files",
            "raw platform credentials",
        ],
        "git": {
            "branch": run_git(["branch", "--show-current"]),
            "head": run_git(["rev-parse", "HEAD"]),
            "status": run_git(["status", "--short", "--branch"]),
            "remotes": run_git(["remote", "-v"]),
            "recent_commits": run_git(["log", "--oneline", "--decorate", "-n", "10"]),
        },
        "doctor": run_checks(),
        "environment": safe_environment_summary(),
    }


def create_support_bundle(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bundle_path = output_dir / f"secondhand-autoposter-support-{stamp}.zip"
    manifest = build_manifest()

    with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest, indent=2, sort_keys=True))
        for relative_path in DEFAULT_DOCS:
            path = ROOT / relative_path
            if path.exists() and path.is_file():
                archive.write(path, relative_path)

    return bundle_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a redacted support/debug bundle.")
    parser.add_argument(
        "--output-dir",
        default="tmp/support-bundles",
        help="Directory for the generated ZIP bundle.",
    )
    args = parser.parse_args()
    bundle_path = create_support_bundle(ROOT / args.output_dir)
    print(bundle_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
