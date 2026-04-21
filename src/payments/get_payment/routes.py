from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from payments.get_payment.schemas import GetPaymentResponse
from payments.get_payment.services import GetPaymentService
from payments.shared.auth import require_api_key
from payments.shared.exceptions import PaymentNotFoundError

router = APIRouter(prefix="/api/v1/payments", tags=["payments"])


@router.get(
    "/{payment_id}",
    response_model=GetPaymentResponse,
    dependencies=[Depends(require_api_key)],
)
@inject
async def get_payment(
    payment_id: UUID,
    session: FromDishka[AsyncSession],
    service: FromDishka[GetPaymentService],
) -> GetPaymentResponse:
    try:
        payment = await service.execute(session, payment_id)
    except PaymentNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    return GetPaymentResponse(
        payment_id=payment.id,
        amount=payment.amount,
        currency=payment.currency,
        description=payment.description,
        metadata=payment.metadata_,
        status=payment.status,
        webhook_url=payment.webhook_url,
        created_at=payment.created_at,
        processed_at=payment.processed_at,
    )
