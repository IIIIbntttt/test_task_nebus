from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from payments.create_payment.schemas import CreatePaymentRequest
from payments.shared.enums import OutboxStatus, PaymentStatus
from payments.shared.models import OutboxModel, PaymentModel


class CreatePaymentRepository:
    async def get_by_idempotency_key(
        self,
        session: AsyncSession,
        idempotency_key: str,
    ) -> PaymentModel | None:
        stmt = select(PaymentModel).where(PaymentModel.idempotency_key == idempotency_key)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_with_outbox(
        self,
        session: AsyncSession,
        payload: CreatePaymentRequest,
        idempotency_key: str,
    ) -> PaymentModel:
        payment = PaymentModel(
            amount=payload.amount,
            currency=payload.currency,
            description=payload.description,
            metadata_=payload.metadata,
            status=PaymentStatus.PENDING,
            idempotency_key=idempotency_key,
            webhook_url=str(payload.webhook_url),
        )
        try:
            session.add(payment)
            await session.flush()

            outbox = OutboxModel(
                event_type="payments.new",
                payload={"payment_id": str(payment.id)},
                status=OutboxStatus.PENDING,
                attempts=0,
            )
            session.add(outbox)
            await session.commit()
        except IntegrityError:
            await session.rollback()
            existing = await self.get_by_idempotency_key(session, idempotency_key)
            if existing is None:
                raise
            return existing
        await session.refresh(payment)
        return payment
