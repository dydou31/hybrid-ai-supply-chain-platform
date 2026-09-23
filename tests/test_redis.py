from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_redis_health():
    response = client.get("/health/redis")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "healthy"
    assert data["redis"] == "connected"
