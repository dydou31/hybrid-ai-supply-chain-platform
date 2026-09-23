from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SupplierCreate(BaseModel):
    name: str = Field(min_length=1)
    country: str = Field(min_length=1)
    risk_level: RiskLevel
    blocked_stock_eur: Decimal = Field(
        ge=0,
        max_digits=12,
        decimal_places=2
    )


class SupplierResponse(BaseModel):
    id: int
    name: str
    country: str
    risk_level: RiskLevel
    blocked_stock_eur: Decimal

    model_config = ConfigDict(from_attributes=True)
