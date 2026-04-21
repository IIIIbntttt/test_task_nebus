from uuid import uuid4

from fastapi.testclient import TestClient


def test_get_payment_returns_details(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/payments",
        headers={"X-API-Key": "test-key", "Idempotency-Key": "idem-get-1"},
        json={
            "amount": "55.00",
            "currency": "EUR",
            "description": "Payment for GET",
            "metadata": {"kind": "test"},
            "webhook_url": "https://example.com/webhook",
        },
    )
    payment_id = create_response.json()["payment_id"]

    response = client.get(
        f"/api/v1/payments/{payment_id}",
        headers={"X-API-Key": "test-key"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["payment_id"] == payment_id
    assert payload["status"] == "pending"
    assert payload["amount"] == "55.00"


def test_get_payment_returns_404_for_unknown_payment(client: TestClient) -> None:
    response = client.get(
        f"/api/v1/payments/{uuid4()}",
        headers={"X-API-Key": "test-key"},
    )

    assert response.status_code == 404


def test_get_payment_requires_valid_api_key(client: TestClient) -> None:
    response = client.get(
        f"/api/v1/payments/{uuid4()}",
        headers={"X-API-Key": "bad-key"},
    )

    assert response.status_code == 401
