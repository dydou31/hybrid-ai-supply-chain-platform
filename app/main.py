from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from app.observability.tracing import setup_tracing
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware

from app.routers.suppliers import router as suppliers_router
from app.routers.health import router as health_router
from app.routers.purchase_orders import router as purchase_orders_router
from app.routers.kpis import router as kpis_router
from app.ai.router import router as ai_router


setup_tracing()

app = FastAPI(
    title="Hybrid AI Supply Chain Platform",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

Instrumentator().instrument(app).expose(app, endpoint="/metrics")
FastAPIInstrumentor.instrument_app(app)

# On ajoute les routers
app.include_router(health_router)
app.include_router(suppliers_router)
app.include_router(purchase_orders_router)
app.include_router(kpis_router)
app.include_router(ai_router)
