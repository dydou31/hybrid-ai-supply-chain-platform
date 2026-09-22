from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.supplier import Supplier
from app.schemas.supplier import SupplierCreate

router = APIRouter()


@router.get("/suppliers")
def get_suppliers(db: Session = Depends(get_db)):
    return db.query(Supplier).all()


@router.post("/suppliers")
def create_supplier(payload: SupplierCreate, db: Session = Depends(get_db)):
    supplier = Supplier(
        name=payload.name,
        country=payload.country,
        risk_level=payload.risk_level,
        blocked_stock_eur=payload.blocked_stock_eur
    )

    db.add(supplier)
    db.commit()
    db.refresh(supplier)

    return supplier


@router.put("/suppliers/{supplier_id}")
def update_supplier(
    supplier_id: int,
    payload: SupplierCreate,
    db: Session = Depends(get_db)
):
    supplier = db.query(Supplier).filter(
        Supplier.id == supplier_id
    ).first()

    if not supplier:
        return {"error": "Supplier not found"}

    supplier.name = payload.name
    supplier.country = payload.country
    supplier.risk_level = payload.risk_level
    supplier.blocked_stock_eur = payload.blocked_stock_eur

    db.commit()
    db.refresh(supplier)

    return supplier


@router.delete("/suppliers/{supplier_id}")
def delete_supplier(
    supplier_id: int,
    db: Session = Depends(get_db)
):
    supplier = db.query(Supplier).filter(
        Supplier.id == supplier_id
    ).first()

    if not supplier:
        return {"error": "Supplier not found"}

    db.delete(supplier)
    db.commit()

    return {"message": "Supplier deleted"}
