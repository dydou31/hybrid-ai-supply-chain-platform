import os
from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.supplier import Supplier
from app.models.purchase_order import PurchaseOrder


router = APIRouter(
    prefix="/admin",
    tags=["admin"],
)


class SupplierSync(BaseModel):
    id: int
    name: str
    country: str
    risk_level: str
    blocked_stock_eur: Decimal


class PurchaseOrderSync(BaseModel):
    id: int
    po_number: str
    supplier_id: int
    order_date: date
    requested_date: date
    confirmed_date: Optional[date] = None
    quantity: int
    unit_price_eur: Decimal
    status: str


class SyncPayload(BaseModel):
    suppliers: list[SupplierSync]
    purchase_orders: list[PurchaseOrderSync]


@router.post("/sync")
def sync_local_to_cloud(
    payload: SyncPayload,
    db: Session = Depends(get_db),
    x_sync_key: Optional[str] = Header(default=None),
):
    expected_key = os.getenv("SYNC_API_KEY")

    if not expected_key:
        raise HTTPException(
            status_code=503,
            detail="Cloud synchronization is not configured.",
        )

    if x_sync_key != expected_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid synchronization key.",
        )

    supplier_created = 0
    supplier_updated = 0
    po_created = 0
    po_updated = 0

    try:
        # Suppliers first because purchase_orders references suppliers.id.
        for item in payload.suppliers:
            supplier = db.get(Supplier, item.id)

            if supplier is None:
                supplier = Supplier(
                    id=item.id,
                    name=item.name,
                    country=item.country,
                    risk_level=item.risk_level,
                    blocked_stock_eur=item.blocked_stock_eur,
                )
                db.add(supplier)
                supplier_created += 1
            else:
                supplier.name = item.name
                supplier.country = item.country
                supplier.risk_level = item.risk_level
                supplier.blocked_stock_eur = item.blocked_stock_eur
                supplier_updated += 1

        # Flush suppliers before inserting purchase orders so FK references exist.
        db.flush()

        for item in payload.purchase_orders:
            purchase_order = (
                db.query(PurchaseOrder)
                .filter(PurchaseOrder.po_number == item.po_number)
                .first()
            )

            if purchase_order is None:
                purchase_order = PurchaseOrder(
                    id=item.id,
                    po_number=item.po_number,
                    supplier_id=item.supplier_id,
                    order_date=item.order_date,
                    requested_date=item.requested_date,
                    confirmed_date=item.confirmed_date,
                    quantity=item.quantity,
                    unit_price_eur=item.unit_price_eur,
                    status=item.status,
                )
                db.add(purchase_order)
                po_created += 1
            else:
                purchase_order.supplier_id = item.supplier_id
                purchase_order.order_date = item.order_date
                purchase_order.requested_date = item.requested_date
                purchase_order.confirmed_date = item.confirmed_date
                purchase_order.quantity = item.quantity
                purchase_order.unit_price_eur = item.unit_price_eur
                purchase_order.status = item.status
                po_updated += 1

        # Make sure all explicit IDs have been inserted before adjusting sequences.
        db.flush()

        # Local IDs are preserved during synchronization. PostgreSQL sequences
        # must therefore be moved to the current maximum ID so future cloud
        # inserts cannot reuse an existing primary key.
        db.execute(
            text(
                """
                SELECT setval(
                    pg_get_serial_sequence('suppliers', 'id'),
                    COALESCE((SELECT MAX(id) FROM suppliers), 1),
                    true
                )
                """
            )
        )

        db.execute(
            text(
                """
                SELECT setval(
                    pg_get_serial_sequence('purchase_orders', 'id'),
                    COALESCE((SELECT MAX(id) FROM purchase_orders), 1),
                    true
                )
                """
            )
        )

        db.commit()

        return {
            "status": "success",
            "suppliers": {
                "created": supplier_created,
                "updated": supplier_updated,
            },
            "purchase_orders": {
                "created": po_created,
                "updated": po_updated,
            },
            "deleted": 0,
        }

    except Exception:
        db.rollback()
        raise