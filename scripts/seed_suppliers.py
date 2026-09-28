from decimal import Decimal
import random

from app.database import SessionLocal
from app.models.supplier import Supplier


random.seed(42)

PREFIXES = [
    "Alpine", "Nordic", "Atlas", "Orion", "Nova",
    "Vector", "Helios", "Apex", "Delta", "Euro",
    "Titan", "Nexus", "Vertex", "Prime", "Stellar",
    "Falcon", "Quantum", "Dynamic", "Global", "Advanced",
]

ACTIVITIES = [
    "Electronics",
    "Components",
    "Automotive",
    "Plastics",
    "Systems",
]

COUNTRIES = [
    "France",
    "Germany",
    "Spain",
    "Italy",
    "Poland",
    "Portugal",
    "Czech Republic",
    "Romania",
    "Belgium",
    "Netherlands",
]

RISK_LEVELS = (
    ["low"] * 50
    + ["medium"] * 35
    + ["high"] * 15
)


def main():
    db = SessionLocal()

    try:
        existing_names = {
            name
            for (name,) in db.query(Supplier.name).all()
        }

        suppliers_to_create = []

        # 20 prefixes × 5 activities = exactly 100 unique suppliers
        names = [
            f"{prefix} {activity}"
            for prefix in PREFIXES
            for activity in ACTIVITIES
        ]

        for index, name in enumerate(names):
            if name in existing_names:
                continue

            risk_level = RISK_LEVELS[index]

            if risk_level == "low":
                blocked_stock = random.uniform(0, 15000)
            elif risk_level == "medium":
                blocked_stock = random.uniform(10000, 40000)
            else:
                blocked_stock = random.uniform(30000, 90000)

            suppliers_to_create.append(
                Supplier(
                    name=name,
                    country=random.choice(COUNTRIES),
                    risk_level=risk_level,
                    blocked_stock_eur=Decimal(
                        f"{blocked_stock:.2f}"
                    ),
                )
            )

        db.add_all(suppliers_to_create)
        db.commit()

        total = db.query(Supplier).count()

        print(
            f"Created: {len(suppliers_to_create)} suppliers"
        )
        print(f"Total suppliers: {total}")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()
