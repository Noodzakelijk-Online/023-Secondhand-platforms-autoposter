from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import sys
import tempfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from app.config import get_settings


PURPOSE = "Secondhand Autoposter private operator backup"


def sqlite_path_from_url(database_url: str) -> Path:
    if not database_url.startswith("sqlite:///"):
        raise ValueError("Only sqlite:/// database URLs are supported by this local backup script.")
    raw_path = database_url.replace("sqlite:///", "", 1)
    if raw_path == ":memory:":
        raise ValueError("In-memory SQLite databases cannot be backed up.")
    return Path(raw_path)


def create_backup(
    output_dir: Path,
    *,
    database_url: str | None = None,
    upload_dir: Path | None = None,
    confirm_private_data: bool = False,
) -> Path:
    if not confirm_private_data:
        raise PermissionError(
            "Refusing to create a private-data backup without --confirm-private-data."
        )

    settings = get_settings()
    source_db = sqlite_path_from_url(database_url or settings.database_url)
    source_upload_dir = upload_dir or settings.upload_path
    if not source_db.exists():
        raise FileNotFoundError(f"SQLite database does not exist: {source_db}")

    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    backup_path = output_dir / f"secondhand-autoposter-private-backup-{timestamp}.zip"

    manifest = {
        "purpose": PURPOSE,
        "created_at": timestamp,
        "database": {"type": "sqlite", "filename": "database.sqlite3"},
        "uploads": {
            "included": source_upload_dir.exists(),
            "path_in_archive": "uploads/",
        },
        "contains_private_data": True,
        "handling": [
            "Store encrypted.",
            "Share only with authorized operators.",
            "Do not attach to support tickets or public issues.",
            "Delete when the recovery window expires.",
        ],
    }

    with tempfile.TemporaryDirectory() as tmp_name:
        tmp_dir = Path(tmp_name)
        database_copy = tmp_dir / "database.sqlite3"
        backup_sqlite_database(source_db, database_copy)

        with zipfile.ZipFile(backup_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("manifest.json", json.dumps(manifest, indent=2, sort_keys=True))
            archive.write(database_copy, "database.sqlite3")
            if source_upload_dir.exists():
                for path in sorted(source_upload_dir.rglob("*")):
                    if path.is_file():
                        archive.write(path, Path("uploads") / path.relative_to(source_upload_dir))

    return backup_path


def backup_sqlite_database(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(source) as source_connection:
        with sqlite3.connect(target) as target_connection:
            source_connection.backup(target_connection)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create a private local SQLite/upload backup.")
    parser.add_argument("--output-dir", type=Path, default=Path("tmp/backups"))
    parser.add_argument("--database-url", default=None)
    parser.add_argument("--upload-dir", type=Path, default=None)
    parser.add_argument(
        "--confirm-private-data",
        action="store_true",
        help="Required. Acknowledge the backup contains private user data and uploaded media.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        backup_path = create_backup(
            args.output_dir,
            database_url=args.database_url,
            upload_dir=args.upload_dir,
            confirm_private_data=args.confirm_private_data,
        )
    except (FileNotFoundError, PermissionError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(backup_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
