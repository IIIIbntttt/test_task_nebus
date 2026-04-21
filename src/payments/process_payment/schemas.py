from uuid import UUID

from pydantic import BaseModel, Field


class PaymentNewMessage(BaseModel):
    payment_id: UUID
    attempt: int = Field(default=0, ge=0)
