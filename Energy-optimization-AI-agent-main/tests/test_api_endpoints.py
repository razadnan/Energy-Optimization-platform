from fastapi.testclient import TestClient
from backend.api import app

client = TestClient(app)

def test_api_home():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["project"] == "Energy Optimization Agent"
    assert data["status"] == "Running"

def test_api_usage():
    response = client.get("/usage")
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "consumption" in data

def test_api_forecast():
    response = client.get("/forecast")
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "evaluation" in data
    assert "forecast" in data

def test_api_anomaly():
    response = client.get("/anomaly")
    assert response.status_code == 200
    data = response.json()
    assert "statistics" in data
    assert "high_risk_records" in data

def test_api_recommendations():
    response = client.get("/recommendations")
    assert response.status_code == 200
    data = response.json()
    assert "recommendations" in data
    assert "savings" in data
    assert "co2" in data

def test_api_reports():
    response = client.get("/reports")
    assert response.status_code == 200
    data = response.json()
    assert "summary_markdown" in data
    assert data["status"] == "Report generated successfully"
