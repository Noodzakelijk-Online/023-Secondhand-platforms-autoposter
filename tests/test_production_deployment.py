from pathlib import Path


def test_production_compose_requires_migrations_before_services_start():
    content = Path("docker-compose.production.yml").read_text(encoding="utf-8")

    assert 'command: ["alembic", "upgrade", "head"]' in content
    assert "condition: service_completed_successfully" in content
    assert "worker:" in content
    assert "UPLOAD_VOLUME" in content
    assert "postgres:" not in content


def test_production_environment_template_uses_safe_required_values():
    content = Path(".env.production.example").read_text(encoding="utf-8")

    required = [
        "APP_ENV=production",
        "AUTH_TRANSPORT=bearer",
        "AUTO_CREATE_TABLES=false",
        "JOB_PROCESS_INLINE=false",
        "DATABASE_URL=postgresql+psycopg://",
        "WORKER_HEARTBEAT_TIMEOUT_SECONDS=30",
    ]
    for value in required:
        assert value in content
