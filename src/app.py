from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI

from payments.create_payment.routes import router as create_payment_router
from payments.get_payment.routes import router as get_payment_router
from payments.shared.di import create_fastapi_container


def create_app() -> FastAPI:
    container = create_fastapi_container()

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        try:
            yield
        finally:
            await container.close()

    app = FastAPI(title="Async Payments Service", lifespan=lifespan)
    app.include_router(create_payment_router)
    app.include_router(get_payment_router)
    setup_dishka(container, app)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
