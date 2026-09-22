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
