import argparse
import json
import os
from datetime import date
from decimal import Decimal
import requests

from dotenv import load_dotenv
from sqlalchemy import create_engine, text


load_dotenv()

LOCAL_DATABASE_URL = os.getenv(
    "LOCAL_DATABASE_URL",
    "postgresql+psycopg2://dylan:dylan@localhost:5432/hybrid_ai",
)

CLOUD_SYNC_URL = os.getenv(
    "CLOUD_SYNC_URL",
    "https://dw3e18cneqohd.cloudfront.net/api/admin/sync",
)

def serialize(value):
    if isinstance(value, Decimal):
        return str(value)

    if isinstance(value, date):
        return value.isoformat()

    return value


def fetch_rows(connection, query):
    result = connection.execute(text(query))

    return [
        {
            key: serialize(value)
            for key, value in row._mapping.items()
        }
        for row in result
    ]


def build_payload():
    engine = create_engine(LOCAL_DATABASE_URL)

    with engine.connect() as connection:
        suppliers = fetch_rows(
            connection,
            """
            SELECT
                id,
                name,
                country,
                risk_level,
                blocked_stock_eur
            FROM suppliers
            ORDER BY id
            """,
        )

        purchase_orders = fetch_rows(
            connection,
            """
            SELECT
                id,
                po_number,
                supplier_id,
                order_date,
                requested_date,
                confirmed_date,
                quantity,
                unit_price_eur,
                status
            FROM purchase_orders
            ORDER BY id
            """,
        )

    return {
        "suppliers": suppliers,
        "purchase_orders": purchase_orders,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Synchronize validated local business data to AWS."
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Inspect the local payload without sending anything.",
    )

    args = parser.parse_args()

    payload = build_payload()

    supplier_count = len(payload["suppliers"])
    po_count = len(payload["purchase_orders"])

    print()
    print("Hybrid AI Platform — Local → AWS Sync")
    print("-------------------------------------")
    print(f"Suppliers       : {supplier_count}")
    print(f"Purchase orders : {po_count}")
    print()

    if args.dry_run:
        print("DRY RUN — nothing was sent to AWS.")
        print()

        if payload["suppliers"]:
            print("First supplier:")
            print(
                json.dumps(
                    payload["suppliers"][0],
                    indent=2,
                    ensure_ascii=False,
                )
            )

        if payload["purchase_orders"]:
            print()
            print("First purchase order:")
            print(
                json.dumps(
                    payload["purchase_orders"][0],
                    indent=2,
                    ensure_ascii=False,
                )
            )

        return

    sync_key = os.getenv("SYNC_API_KEY")

    if not sync_key:
        raise RuntimeError("SYNC_API_KEY is not configured.")

    print(f"Sending {supplier_count} suppliers and {po_count} purchase orders...")
    print()

    response = requests.post(
        CLOUD_SYNC_URL,
        headers={
            "X-Sync-Key": sync_key,
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=120,
    )

    response.raise_for_status()

    result = response.json()

    print("Synchronization completed successfully.")
    print()
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
