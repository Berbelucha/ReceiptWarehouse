"""
Test file for document processing functionality.
"""

from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "ReceiptWarehouse API" in data["message"]

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "receipt-warehouse"

def test_document_processing_endpoints_exist():
    # Test that the endpoints exist and return 422 (validation error) for missing parameters
    response = client.post("/documents/scan")
    assert response.status_code == 422  # Validation error

    response = client.post("/documents/fix-ocr")
    assert response.status_code == 422  # Validation error

    response = client.post("/documents/generate-metadata")
    assert response.status_code == 422  # Validation error