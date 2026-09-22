from sqlalchemy.orm import Session
from app.models.supplier import Supplier

def get_all_suppliers(db: Session):
    return db.query(Supplier).all()
