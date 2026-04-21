from pathlib import Path

import yaml


def test_compose_has_migrate_init_service() -> None:
    content = Path("docker-compose.yml").read_text(encoding="utf-8")
    compose = yaml.safe_load(content)
    services = compose["services"]

    assert "migrate" in services
    assert services["migrate"]["command"] == "uv run alembic upgrade head"

    for service_name in ("api", "consumer", "outbox-worker"):
        depends_on = services[service_name]["depends_on"]
        assert depends_on["migrate"]["condition"] == "service_completed_successfully"


def test_api_does_not_run_alembic_in_command() -> None:
    content = Path("docker-compose.yml").read_text(encoding="utf-8")
    compose = yaml.safe_load(content)
    api_command = compose["services"]["api"]["command"]

    assert "alembic upgrade head" not in api_command
