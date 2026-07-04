from __future__ import annotations

from pathlib import Path

from scripts.audit_static_ui import audit_static_ui


def test_static_ui_accessibility_audit_passes() -> None:
    violations = audit_static_ui(Path(__file__).resolve().parents[1])

    assert violations == []
