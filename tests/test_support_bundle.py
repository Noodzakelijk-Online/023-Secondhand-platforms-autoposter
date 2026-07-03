import json
import zipfile

from scripts.support_bundle import create_support_bundle


def test_support_bundle_excludes_runtime_and_secret_files(tmp_path):
    bundle_path = create_support_bundle(tmp_path)

    assert bundle_path.exists()
    with zipfile.ZipFile(bundle_path) as archive:
        names = set(archive.namelist())
        assert "manifest.json" in names
        assert "Readme.md" in names
        assert "docs/SECURITY.md" in names
        assert not any(name.startswith("data/") for name in names)
        assert not any(".env" in name for name in names)

        manifest = json.loads(archive.read("manifest.json"))
        assert manifest["purpose"] == "Secondhand Autoposter support/debug bundle"
        assert "doctor" in manifest
        assert "git" in manifest
        assert ".env files" in manifest["exclusions"]
        secret_settings = [
            item for item in manifest["environment"]["settings"] if "SECRET" in item["name"]
        ]
        assert secret_settings
        assert all(item["value"] == "<redacted>" for item in secret_settings)
