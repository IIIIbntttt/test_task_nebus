from fastapi.testclient import TestClient


def test_create_payment_returns_202(client: TestClient) -> None:
    response = client.post(
        "/api/v1/payments",
        headers={"X-API-Key": "test-key", "Idempotency-Key": "idem-1"},
        json={
            "amount": "100.00",
            "currency": "USD",
            "description": "Test payment",
            "metadata": {"source": "test"},
            "webhook_url": "https://example.com/webhook",
        },
    )

    assert response.status_code == 202
    payload = response.json()
    assert payload["status"] == "pending"
    assert payload["payment_id"]
    assert payload["created_at"]


def test_create_payment_requires_idempotency_header(client: TestClient) -> None:
    response = client.post(
        "/api/v1/payments",
        headers={"X-API-Key": "test-key"},
        json={
            "amount": "100.00",
            "currency": "USD",
            "description": "Test payment",
            "metadata": {"source": "test"},
            "webhook_url": "https://example.com/webhook",
        },
    )

    assert response.status_code == 422


def test_create_payment_requires_valid_api_key(client: TestClient) -> None:
    response = client.post(
        "/api/v1/payments",
        headers={"X-API-Key": "bad-key", "Idempotency-Key": "idem-2"},
        json={
            "amount": "100.00",
            "currency": "USD",
            "description": "Test payment",
            "metadata": {"source": "test"},
            "webhook_url": "https://example.com/webhook",
        },
    )

    assert response.status_code == 401


def test_create_payment_idempotency_returns_same_payment(client: TestClient) -> None:
    headers = {"X-API-Key": "test-key", "Idempotency-Key": "idem-3"}
    body = {
        "amount": "100.00",
        "currency": "USD",
        "description": "Test payment",
        "metadata": {"source": "test"},
        "webhook_url": "https://example.com/webhook",
    }

    first = client.post("/api/v1/payments", headers=headers, json=body)
    second = client.post("/api/v1/payments", headers=headers, json=body)

    assert first.status_code == 202
    assert second.status_code == 202
    assert first.json()["payment_id"] == second.json()["payment_id"]
