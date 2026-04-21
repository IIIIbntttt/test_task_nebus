from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from payments.shared.enums import Currency, PaymentStatus


class GetPaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    payment_id: UUID
    amount: Decimal
    currency: Currency
    description: str
    metadata: dict[str, Any]
    status: PaymentStatus
    webhook_url: str
    created_at: datetime
    processed_at: datetime | None
