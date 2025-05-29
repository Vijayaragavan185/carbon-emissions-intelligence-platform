from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_create_emission():
    response = client.post("/api/v1/emissions/", json={"source": "power", "value": 100.0, "unit": "kg"})
    assert response.status_code == 200
    assert response.json()["source"] == "power"

