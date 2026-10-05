import os
from fastapi import APIRouter
from sqlalchemy import text
import urllib.request
import json

from app.database import engine
from app.core.redis import redis_client

router = APIRouter(prefix="/health", tags=["Health"])


def check_url(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=3) as response:
            return 200 <= response.status < 400
    except Exception:
        return False


@router.get("/postgres")
def postgres_health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

            pgvector = connection.execute(
                text(
                    "SELECT EXISTS ("
                    "SELECT 1 FROM pg_extension WHERE extname = 'vector'"
                    ")"
                )
            ).scalar()

        return {
            "status": "healthy",
            "postgres": "connected",
            "pgvector": "enabled" if pgvector else "disabled",
        }
    except Exception:
        return {
            "status": "unhealthy",
            "postgres": "disconnected",
            "pgvector": "unknown",
        }


@router.get("/redis")
def redis_health():
    try:
        redis_client.ping()

        return {
            "status": "healthy",
            "redis": "connected",
        }
    except Exception:
        return {
            "status": "unhealthy",
            "redis": "disconnected",
        }


@router.get("/prometheus")
def prometheus_health():
    healthy = check_url("http://prometheus:9090/-/healthy")

    return {
        "status": "healthy" if healthy else "unhealthy",
        "prometheus": "reachable" if healthy else "unreachable",
    }


@router.get("/grafana")
def grafana_health():
    healthy = check_url("http://grafana:3000/api/health")

    return {
        "status": "healthy" if healthy else "unhealthy",
        "grafana": "reachable" if healthy else "unreachable",
    }


@router.get("/tempo")
def tempo_health():
    healthy = check_url("http://tempo:3200/ready")

    return {
        "status": "healthy" if healthy else "unhealthy",
        "tempo": "reachable" if healthy else "unreachable",
    }


@router.get("/ollama")
def ollama_health():
    try:
        with urllib.request.urlopen(
            "http://host.docker.internal:11434/api/tags",
            timeout=3,
        ) as response:
            data = json.loads(response.read().decode())

        models = [
            model.get("name", "")
            for model in data.get("models", [])
        ]

        llama_ready = any(
            model.startswith("llama3.2:3b")
            for model in models
        )

        return {
            "status": "healthy" if llama_ready else "unhealthy",
            "ollama": "reachable",
            "model": "llama3.2:3b",
            "model_ready": llama_ready,
        }

    except Exception:
        return {
            "status": "unhealthy",
            "ollama": "unreachable",
            "model": "llama3.2:3b",
            "model_ready": False,
        }


@router.get("/platform")
def platform_health():
    llm_provider = os.getenv("LLM_PROVIDER", "ollama").lower()

    if llm_provider == "bedrock":
        services = {
            "postgres": postgres_health(),
            "redis": redis_health(),
        }
    else:
        services = {
            "postgres": postgres_health(),
            "redis": redis_health(),
            "prometheus": prometheus_health(),
            "grafana": grafana_health(),
            "tempo": tempo_health(),
            "ollama": ollama_health(),
        }

    healthy = all(
        service["status"] == "healthy"
        for service in services.values()
    )

    return {
        "status": "healthy" if healthy else "degraded",
        "services": services,
    }
