from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_get_supplier_kpis():
    response = client.get("/kpis/suppliers")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) > 0

    supplier = next(
        item for item in data
        if item["supplier"] == "Test Supplier"
    )

    assert supplier["purchase_orders"] == 1
    assert float(supplier["total_value_eur"]) == 1000.0
    assert supplier["delayed_orders"] == 1
    assert supplier["delay_rate"] == 100.0
    assert supplier["average_delay_days"] == 2
