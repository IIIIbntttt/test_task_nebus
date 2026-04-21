from fastapi.testclient import TestClient


def test_create_and_get_payment_flow(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/payments",
        headers={"X-API-Key": "test-key", "Idempotency-Key": "e2e-idem-1"},
        json={
            "amount": "44.00",
            "currency": "RUB",
            "description": "E2E payment flow",
            "metadata": {"source": "e2e"},
            "webhook_url": "https://example.com/webhook",
        },
    )
    assert create_response.status_code == 202
    payload = create_response.json()

    get_response = client.get(
        f"/api/v1/payments/{payload['payment_id']}",
        headers={"X-API-Key": "test-key"},
    )
    assert get_response.status_code == 200
    assert get_response.json()["payment_id"] == payload["payment_id"]
