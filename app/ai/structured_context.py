from collections import Counter
from decimal import Decimal

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.supplier import Supplier
from app.models.purchase_order import PurchaseOrder


def get_structured_context() -> str:
    db: Session = SessionLocal()

    try:
        suppliers = db.query(Supplier).all()
        purchase_orders = db.query(PurchaseOrder).all()

        total_suppliers = len(suppliers)

        risk_counts = Counter(
            supplier.risk_level
            for supplier in suppliers
        )

        country_counts = Counter(
            supplier.country
            for supplier in suppliers
        )

        total_blocked_stock = sum(
            (
                supplier.blocked_stock_eur
                or Decimal("0")
                for supplier in suppliers
            ),
            Decimal("0"),
        )

        highest_blocked_stock = max(
            suppliers,
            key=lambda supplier:
                supplier.blocked_stock_eur or Decimal("0"),
            default=None,
        )

        delayed_orders = [
            po
            for po in purchase_orders
            if po.confirmed_date
            and po.confirmed_date > po.requested_date
        ]

        lines = [
            "STRUCTURED SUPPLY CHAIN DATA",
            "",
            "GLOBAL KPIS:",
            f"Total suppliers: {total_suppliers}",
            f"Low risk suppliers: {risk_counts.get('low', 0)}",
            f"Medium risk suppliers: {risk_counts.get('medium', 0)}",
            f"High risk suppliers: {risk_counts.get('high', 0)}",
            (
                "Total blocked stock EUR: "
                f"{total_blocked_stock:.2f}"
            ),
            f"Total purchase orders: {len(purchase_orders)}",
            f"Total delayed orders: {len(delayed_orders)}",
        ]

        if highest_blocked_stock:
            lines.extend(
                [
                    (
                        "Supplier with highest blocked stock: "
                        f"{highest_blocked_stock.name}"
                    ),
                    (
                        "Highest blocked stock EUR: "
                        f"{highest_blocked_stock.blocked_stock_eur}"
                    ),
                ]
            )

        lines.extend(
            [
                "",
                "SUPPLIERS BY COUNTRY:",
            ]
        )

        for country, count in sorted(country_counts.items()):
            lines.append(f"{country}: {count}")

        lines.extend(
            [
                "",
                "SUPPLIER DIRECTORY:",
            ]
        )

        for supplier in suppliers:
            lines.append(
                f"{supplier.name} | "
                f"{supplier.country} | "
                f"risk={supplier.risk_level} | "
                f"blocked_stock_eur={supplier.blocked_stock_eur}"
            )

        return "\n".join(lines)

    finally:
        db.close()
