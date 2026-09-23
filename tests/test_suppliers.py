from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_get_suppliers():
    response = client.get("/suppliers")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) > 0
