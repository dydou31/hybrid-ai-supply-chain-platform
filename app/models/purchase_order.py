from sqlalchemy import Column, Integer, String, Date, ForeignKey, Numeric
from app.database import Base


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, index=True)

    po_number = Column(String, nullable=False, unique=True)

    supplier_id = Column(
        Integer,
        ForeignKey("suppliers.id"),
        nullable=False
    )

    order_date = Column(Date, nullable=False)
    requested_date = Column(Date, nullable=False)
    confirmed_date = Column(Date, nullable=True)

    quantity = Column(Integer, nullable=False)

    unit_price_eur = Column(
        Numeric(12, 2),
        nullable=False
    )

    status = Column(String, nullable=False)
