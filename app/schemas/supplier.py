from pydantic import BaseModel

class SupplierCreate(BaseModel):
    name: str
    country: str
    risk_level: str
    blocked_stock_eur: int
