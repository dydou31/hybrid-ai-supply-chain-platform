from decimal import Decimal
from app.core.redis import redis_client
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.supplier import Supplier
from app.models.purchase_order import PurchaseOrder


router = APIRouter(
    prefix="/kpis",
    tags=["KPIs"]
)


@router.get("/suppliers")
def get_supplier_kpis(
    db: Session = Depends(get_db)
):
    cache_key = "kpis:suppliers"

    cached = redis_client.get(cache_key)

    if cached:
        import json
        return json.loads(cached)

    suppliers = db.query(Supplier).all()
    purchase_orders = db.query(PurchaseOrder).all()

    orders_by_supplier = {}

    for po in purchase_orders:
        orders_by_supplier.setdefault(po.supplier_id, []).append(po)

    results = []

    for supplier in suppliers:
        orders = orders_by_supplier.get(supplier.id, [])

        total_orders = len(orders)

        delayed_orders = sum(
            1
            for po in orders
            if po.confirmed_date
            and po.confirmed_date > po.requested_date
        )

        total_value = sum(
            (
                Decimal(po.quantity) * po.unit_price_eur
                for po in orders
            ),
            Decimal("0")
        )

        delay_days = [
            (po.confirmed_date - po.requested_date).days
            for po in orders
            if po.confirmed_date
            and po.confirmed_date > po.requested_date
        ]

        average_delay_days = (
            round(sum(delay_days) / len(delay_days), 2)
            if delay_days
            else 0
        )

        delay_rate = (
            round((delayed_orders / total_orders) * 100, 2)
            if total_orders
            else 0
        )

        results.append({
            "supplier_id": supplier.id,
            "supplier": supplier.name,
            "country": supplier.country,
            "risk_level": supplier.risk_level,
            "blocked_stock_eur": supplier.blocked_stock_eur,
            "purchase_orders": total_orders,
            "total_value_eur": total_value,
            "delayed_orders": delayed_orders,
            "delay_rate": delay_rate,
            "average_delay_days": average_delay_days,
        })
    import json

    redis_client.setex(
        "kpis:suppliers",
        300,
        json.dumps(results, default=str)
    )

    return results
