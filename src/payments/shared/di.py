from collections.abc import AsyncIterator

from dishka import Provider, Scope, make_async_container, provide
from dishka.async_container import AsyncContainer
from dishka.integrations.fastapi import FastapiProvider
from sqlalchemy.ext.asyncio import AsyncSession

from payments.create_payment.repository import CreatePaymentRepository
from payments.create_payment.services import CreatePaymentService
from payments.get_payment.repository import GetPaymentRepository
from payments.get_payment.services import GetPaymentService
from payments.shared.db import get_session_factory


class AppProvider(Provider):
    @provide(scope=Scope.REQUEST)
    async def db_session(self) -> AsyncIterator[AsyncSession]:
        session_factory = get_session_factory()
        async with session_factory() as session:
            yield session

    @provide(scope=Scope.REQUEST)
    def create_payment_repository(self) -> CreatePaymentRepository:
        return CreatePaymentRepository()

    @provide(scope=Scope.REQUEST)
    def create_payment_service(
        self,
        repository: CreatePaymentRepository,
    ) -> CreatePaymentService:
        return CreatePaymentService(repository=repository)

    @provide(scope=Scope.REQUEST)
    def get_payment_repository(self) -> GetPaymentRepository:
        return GetPaymentRepository()

    @provide(scope=Scope.REQUEST)
    def get_payment_service(
        self,
        repository: GetPaymentRepository,
    ) -> GetPaymentService:
        return GetPaymentService(repository=repository)


def create_fastapi_container() -> AsyncContainer:
    return make_async_container(AppProvider(), FastapiProvider())
