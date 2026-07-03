import sqlite3
import zipfile

import pytest

from scripts.backup_local_data import create_backup
from scripts.restore_local_data import restore_backup


def test_private_backup_requires_explicit_confirmation(tmp_path):
    db_path = tmp_path / "source.db"
    db_path.touch()

    with pytest.raises(PermissionError):
        create_backup(
            tmp_path / "backups",
            database_url=f"sqlite:///{db_path.as_posix()}",
            confirm_private_data=False,
        )


def test_local_backup_and_restore_round_trip_sqlite_and_uploads(tmp_path):
    source_db = tmp_path / "source.db"
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    (upload_dir / "listing-photo.jpg").write_bytes(b"image-bytes")

    with sqlite3.connect(source_db) as connection:
        connection.execute("create table example (id integer primary key, name text)")
        connection.execute("insert into example (name) values ('listing')")
        connection.commit()

    backup_path = create_backup(
        tmp_path / "backups",
        database_url=f"sqlite:///{source_db.as_posix()}",
        upload_dir=upload_dir,
        confirm_private_data=True,
    )

    with zipfile.ZipFile(backup_path) as archive:
        names = set(archive.namelist())
        assert "manifest.json" in names
        assert "database.sqlite3" in names
        assert "uploads/listing-photo.jpg" in names

    target_db = tmp_path / "restored.db"
    target_upload_dir = tmp_path / "restored_uploads"
    restore_backup(
        backup_path,
        database_url=f"sqlite:///{target_db.as_posix()}",
        upload_dir=target_upload_dir,
        confirm_overwrite=True,
    )

    with sqlite3.connect(target_db) as connection:
        assert connection.execute("select name from example").fetchone() == ("listing",)
    assert (target_upload_dir / "listing-photo.jpg").read_bytes() == b"image-bytes"


def test_restore_requires_explicit_overwrite_confirmation(tmp_path):
    db_path = tmp_path / "source.db"
    db_path.touch()
    backup_path = create_backup(
        tmp_path / "backups",
        database_url=f"sqlite:///{db_path.as_posix()}",
        confirm_private_data=True,
    )

    with pytest.raises(PermissionError):
        restore_backup(
            backup_path,
            database_url=f"sqlite:///{(tmp_path / 'target.db').as_posix()}",
            confirm_overwrite=False,
        )
