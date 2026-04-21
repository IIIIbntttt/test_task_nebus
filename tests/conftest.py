import asyncio
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import create_app
from payments.shared.config import get_settings
from payments.shared.db import Base, get_engine, get_session_factory


def _run(coro):
    return asyncio.run(coro)


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[TestClient]:
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("APP_API_KEY", "test-key")
    monkeypatch.setenv("APP_DATABASE_URL", f"sqlite+aiosqlite:///{db_path}")
    monkeypatch.setenv("APP_RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    get_settings.cache_clear()
    get_engine.cache_clear()
    get_session_factory.cache_clear()

    engine = get_engine()
    _run(_create_tables())
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
    _run(_drop_tables())
    _run(engine.dispose())
    get_settings.cache_clear()
    get_engine.cache_clear()
    get_session_factory.cache_clear()


async def _create_tables() -> None:
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def _drop_tables() -> None:
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
