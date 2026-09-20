from fastapi import FastAPI
from app.routers.suppliers import router as suppliers_router
from datetime import datetime

app = FastAPI(
    title="Hybrid AI Supply Chain Platform",
    version="0.1.0"
)

@app.get("/")
def root():
    return {
        "application": "Hybrid AI Supply Chain Platform",
        "version": "0.1.0"
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

# On ajoute le router suppliers
app.include_router(suppliers_router)
