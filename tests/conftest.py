import pytest
from datetime import date
from decimal import Decimal

from app.core.redis import redis_client
from app.database import SessionLocal
from app.models.supplier import Supplier
from app.models.purchase_order import PurchaseOrder


@pytest.fixture(autouse=True)
def seed_test_data():
    db = SessionLocal()

    redis_client.delete("kpis:suppliers")

    supplier = Supplier(
        name="Test Supplier",
        country="France",
        risk_level="low",
        blocked_stock_eur=Decimal("5000.00"),
    )

    db.add(supplier)
    db.flush()

    purchase_order = PurchaseOrder(
        po_number="TEST-PO-001",
        supplier_id=supplier.id,
        order_date=date(2026, 9, 23),
        requested_date=date(2026, 9, 30),
        confirmed_date=date(2026, 10, 2),
        quantity=100,
        unit_price_eur=Decimal("10.00"),
        status="confirmed",
    )

    db.add(purchase_order)
    db.commit()

    try:
        yield
    finally:
        redis_client.delete("kpis:suppliers")

        db.delete(purchase_order)
        db.delete(supplier)
        db.commit()
        db.close()
