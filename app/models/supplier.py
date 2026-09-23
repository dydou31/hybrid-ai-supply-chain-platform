from sqlalchemy import Column, Integer, String, Numeric
from app.database import Base


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    country = Column(String, nullable=False)
    risk_level = Column(String, nullable=False)
    blocked_stock_eur = Column(Numeric(12, 2), nullable=False)
