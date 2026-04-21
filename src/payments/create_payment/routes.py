from typing import Annotated

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.ext.asyncio import AsyncSession

from payments.create_payment.schemas import CreatePaymentRequest, CreatePaymentResponse
from payments.create_payment.services import CreatePaymentService
from payments.shared.auth import require_api_key

router = APIRouter(prefix="/api/v1/payments", tags=["payments"])


@router.post(
    "",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=CreatePaymentResponse,
    dependencies=[Depends(require_api_key)],
)
@inject
async def create_payment(
    payload: CreatePaymentRequest,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
    session: FromDishka[AsyncSession],
    service: FromDishka[CreatePaymentService],
) -> CreatePaymentResponse:
    payment = await service.execute(session, payload, idempotency_key)
    return CreatePaymentResponse(
        payment_id=payment.id,
        status=payment.status,
        created_at=payment.created_at,
    )
