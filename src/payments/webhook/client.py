from typing import Protocol

import httpx

from payments.shared.config import get_settings


class WebhookClient(Protocol):
    async def post(self, url: str, payload: dict[str, object]) -> None:
        ...


class HttpxWebhookClient:
    async def post(self, url: str, payload: dict[str, object]) -> None:
        settings = get_settings()
        timeout = settings.webhook_timeout_seconds
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
