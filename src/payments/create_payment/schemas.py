from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from payments.shared.enums import Currency, PaymentStatus


class CreatePaymentRequest(BaseModel):
    amount: Decimal = Field(gt=0)
    currency: Currency
    description: str = Field(min_length=1, max_length=2048)
    metadata: dict[str, Any] = Field(default_factory=dict)
    webhook_url: HttpUrl


class CreatePaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    payment_id: UUID
    status: PaymentStatus
    created_at: datetime
