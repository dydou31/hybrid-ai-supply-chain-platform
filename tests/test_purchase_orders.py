from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_get_purchase_orders():
    response = client.get("/purchase-orders")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) > 0
