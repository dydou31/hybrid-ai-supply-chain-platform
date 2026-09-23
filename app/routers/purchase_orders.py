from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.supplier import Supplier

from app.database import get_db
from app.models.purchase_order import PurchaseOrder
from app.schemas.purchase_order import (
    PurchaseOrderCreate,
    PurchaseOrderResponse,
)

router = APIRouter()


@router.get(
    "/purchase-orders",
    response_model=list[PurchaseOrderResponse]
)
def get_purchase_orders(db: Session = Depends(get_db)):
    return db.query(PurchaseOrder).all()


@router.get(
    "/purchase-orders/{purchase_order_id}",
    response_model=PurchaseOrderResponse
)
def get_purchase_order(
    purchase_order_id: int,
    db: Session = Depends(get_db)
):
    purchase_order = db.query(PurchaseOrder).filter(
        PurchaseOrder.id == purchase_order_id
    ).first()

    if not purchase_order:
        raise HTTPException(
            status_code=404,
            detail="Purchase order not found"
        )

    return purchase_order


@router.post(
    "/purchase-orders",
    response_model=PurchaseOrderResponse
)
def create_purchase_order(
    payload: PurchaseOrderCreate,
    db: Session = Depends(get_db)
):
    supplier = db.query(Supplier).filter(
        Supplier.id == payload.supplier_id
    ).first()

    if not supplier:
        raise HTTPException(
            status_code=404,
            detail="Supplier not found"
        )

    purchase_order = PurchaseOrder(**payload.model_dump())

    db.add(purchase_order)
    db.commit()
    db.refresh(purchase_order)

    return purchase_order
