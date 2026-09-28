from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.supplier import Supplier
from app.models.purchase_order import PurchaseOrder


def get_structured_context() -> str:
    db: Session = SessionLocal()

    try:
        suppliers = db.query(Supplier).all()
        purchase_orders = db.query(PurchaseOrder).all()

        orders_by_supplier = {}

        for po in purchase_orders:
            orders_by_supplier.setdefault(
                po.supplier_id,
                [],
            ).append(po)

        lines = [
            "STRUCTURED SUPPLY CHAIN DATA",
            f"Total suppliers: {len(suppliers)}",
            "",
        ]

        for supplier in suppliers:
            orders = orders_by_supplier.get(supplier.id, [])

            delayed_orders = [
                po
                for po in orders
                if po.confirmed_date
                and po.confirmed_date > po.requested_date
            ]

            delay_days = [
                (po.confirmed_date - po.requested_date).days
                for po in delayed_orders
            ]

            average_delay = (
                round(sum(delay_days) / len(delay_days), 2)
                if delay_days
                else 0
            )

            delay_rate = (
                round(
                    (len(delayed_orders) / len(orders)) * 100,
                    2,
                )
                if orders
                else 0
            )

            lines.extend(
                [
                    f"Supplier: {supplier.name}",
                    f"Country: {supplier.country}",
                    f"Risk level: {supplier.risk_level}",
                    (
                        "Blocked stock EUR: "
                        f"{supplier.blocked_stock_eur}"
                    ),
                    f"Purchase orders: {len(orders)}",
                    f"Delayed orders: {len(delayed_orders)}",
                    f"Delay rate: {delay_rate}%",
                    f"Average delay days: {average_delay}",
                    "",
                ]
            )

        return "\n".join(lines)

    finally:
        db.close()
