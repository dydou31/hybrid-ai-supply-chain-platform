from datetime import date
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


class PurchaseOrderStatus(str, Enum):
    OPEN = "open"
    CONFIRMED = "confirmed"
    DELAYED = "delayed"
    RECEIVED = "received"
    CANCELLED = "cancelled"


class PurchaseOrderCreate(BaseModel):
    po_number: str = Field(min_length=1)
    supplier_id: int
    order_date: date
    requested_date: date
    confirmed_date: date | None = None
    quantity: int = Field(gt=0)
    unit_price_eur: Decimal = Field(
        ge=0,
        max_digits=12,
        decimal_places=2
    )
    status: PurchaseOrderStatus


class PurchaseOrderResponse(PurchaseOrderCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)
