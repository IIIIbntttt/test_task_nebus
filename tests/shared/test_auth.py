from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from payments.shared.auth import require_api_key
from payments.shared.config import get_settings


def create_test_app() -> FastAPI:
    app = FastAPI()

    @app.get("/secure", dependencies=[Depends(require_api_key)])
    async def secure() -> dict[str, str]:
        return {"status": "ok"}

    return app


def test_auth_accepts_valid_api_key(monkeypatch) -> None:
    monkeypatch.setenv("APP_API_KEY", "test-key")
    get_settings.cache_clear()

    app = create_test_app()
    client = TestClient(app)
    response = client.get("/secure", headers={"X-API-Key": "test-key"})
    assert response.status_code == 200


def test_auth_rejects_invalid_api_key(monkeypatch) -> None:
    monkeypatch.setenv("APP_API_KEY", "test-key")
    get_settings.cache_clear()

    app = create_test_app()
    client = TestClient(app)
    response = client.get("/secure", headers={"X-API-Key": "wrong"})
    assert response.status_code == 401
