from fastapi import APIRouter

router = APIRouter()

@router.get("/suppliers")
def get_suppliers():
    return [
        {
            "name": "Supplier Alpha",
            "country": "France",
            "risk_level": "High",
            "blocked_stock_eur": 12500
        },
        {
            "name": "Supplier Beta",
            "country": "Germany",
            "risk_level": "Low",
            "blocked_stock_eur": 2400
        }
    ]

