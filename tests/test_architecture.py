from pathlib import Path


def test_api_routes_are_split_by_responsibility():
    root = Path(__file__).resolve().parents[1]

    main_source = (root / "app" / "main.py").read_text()
    api_source = (root / "app" / "api.py").read_text()

    assert (root / "app" / "dependencies.py").exists()
    assert (root / "app" / "routes" / "auth.py").exists()
    assert (root / "app" / "routes" / "system.py").exists()
    assert "auth_router" in main_source
    assert "system_router" in main_source
    assert "@router.post(\"/auth/login\"" not in api_source
    assert "@router.get(\"/health\"" not in api_source
    assert "def get_current_session(" not in api_source
