from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

from app.config import get_settings
from scripts.backup_local_data import PURPOSE, sqlite_path_from_url


def restore_backup(
    backup_path: Path,
    *,
    database_url: str | None = None,
    upload_dir: Path | None = None,
    confirm_overwrite: bool = False,
) -> None:
    if not confirm_overwrite:
        raise PermissionError("Refusing to restore without --confirm-overwrite.")
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup archive does not exist: {backup_path}")

    settings = get_settings()
    target_db = sqlite_path_from_url(database_url or settings.database_url)
    target_upload_dir = upload_dir or settings.upload_path

    with tempfile.TemporaryDirectory() as tmp_name:
        tmp_dir = Path(tmp_name)
        with zipfile.ZipFile(backup_path) as archive:
            manifest = json.loads(archive.read("manifest.json"))
            if manifest.get("purpose") != PURPOSE:
                raise ValueError("Archive is not a Secondhand Autoposter private operator backup.")
            archive.extract("database.sqlite3", tmp_dir)
            for name in archive.namelist():
                if name.startswith("uploads/") and not name.endswith("/"):
                    archive.extract(name, tmp_dir)

        restored_db = tmp_dir / "database.sqlite3"
        if not restored_db.exists():
            raise ValueError("Backup archive is missing database.sqlite3.")

        target_db.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(restored_db, target_db)

        restored_uploads = tmp_dir / "uploads"
        if restored_uploads.exists():
            if target_upload_dir.exists():
                shutil.rmtree(target_upload_dir)
            shutil.copytree(restored_uploads, target_upload_dir)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Restore a private local SQLite/upload backup.")
    parser.add_argument("backup_path", type=Path)
    parser.add_argument("--database-url", default=None)
    parser.add_argument("--upload-dir", type=Path, default=None)
    parser.add_argument(
        "--confirm-overwrite",
        action="store_true",
        help="Required. Acknowledge the restore overwrites local database/uploads.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        restore_backup(
            args.backup_path,
            database_url=args.database_url,
            upload_dir=args.upload_dir,
            confirm_overwrite=args.confirm_overwrite,
        )
    except (FileNotFoundError, PermissionError, ValueError, zipfile.BadZipFile) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print("Restore completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
