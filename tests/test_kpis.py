from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_get_supplier_kpis():
    response = client.get("/kpis/suppliers")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
