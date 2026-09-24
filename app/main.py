from fastapi import FastAPI
from datetime import datetime

from app.routers.suppliers import router as suppliers_router
from app.routers.purchase_orders import router as purchase_orders_router
from app.routers.kpis import router as kpis_router
from app.ai.router import router as ai_router


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

@app.get("/health/redis")
def redis_health():
    from app.core.redis import redis_client

    redis_client.ping()

    return {
        "status": "healthy",
        "redis": "connected"
    }


# On ajoute les routers
app.include_router(suppliers_router)
app.include_router(purchase_orders_router)
app.include_router(kpis_router)
app.include_router(ai_router)
