from datetime import date, timedelta
from decimal import Decimal
import random

from app.database import SessionLocal
from app.models.supplier import Supplier
from app.models.purchase_order import PurchaseOrder


random.seed(42)

ORDERS_PER_SUPPLIER = 5

DELAY_PROBABILITY = {
    "low": 0.10,
    "medium": 0.30,
    "high": 0.60,
}


def main():
    db = SessionLocal()

    try:
        suppliers = (
            db.query(Supplier)
            .filter(Supplier.name.notin_([
                "Bosch",
                "Valeo",
                "Continental",
                "ZF",
            ]))
            .order_by(Supplier.id)
            .all()
        )

        existing_po_numbers = {
            number
            for (number,) in db.query(
                PurchaseOrder.po_number
            ).all()
        }

        created = 0
        delayed = 0

        for supplier in suppliers:
            delay_probability = DELAY_PROBABILITY.get(
                supplier.risk_level,
                0.25,
            )

            for index in range(1, ORDERS_PER_SUPPLIER + 1):
                po_number = (
                    f"DEMO-{supplier.id:04d}-{index:02d}"
                )

                if po_number in existing_po_numbers:
                    continue

                order_date = date(2026, 1, 1) + timedelta(
                    days=random.randint(0, 240)
                )

                lead_time = random.randint(7, 35)

                requested_date = (
                    order_date + timedelta(days=lead_time)
                )

                is_delayed = (
                    random.random() < delay_probability
                )

                if is_delayed:
                    confirmed_date = (
                        requested_date
                        + timedelta(days=random.randint(1, 15))
                    )
                    delayed += 1
                else:
                    confirmed_date = (
                        requested_date
                        - timedelta(days=random.randint(0, 3))
                    )

                quantity = random.randint(50, 5000)

                unit_price = Decimal(
                    f"{random.uniform(1.50, 250.00):.2f}"
                )

                po = PurchaseOrder(
                    po_number=po_number,
                    supplier_id=supplier.id,
                    order_date=order_date,
                    requested_date=requested_date,
                    confirmed_date=confirmed_date,
                    quantity=quantity,
                    unit_price_eur=unit_price,
                    status="confirmed",
                )

                db.add(po)
                created += 1

        db.commit()

        total = db.query(PurchaseOrder).count()

        print(f"Suppliers processed: {len(suppliers)}")
        print(f"Created purchase orders: {created}")
        print(f"Delayed purchase orders created: {delayed}")
        print(f"Total purchase orders in database: {total}")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()
