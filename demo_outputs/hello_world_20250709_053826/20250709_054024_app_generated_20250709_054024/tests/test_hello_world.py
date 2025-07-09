import pytest
from fastapi.testclient import TestClient
from main import app  # This import will fail initially

client = TestClient(app)

def test_hello_world_endpoint():
    response = client.get("/hello")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, World!"}

def test_invalid_endpoint():
    response = client.get("/invalid")
    assert response.status_code == 404
    assert response.json() == {"error": "Not Found"}

def test_error_handling():
    response = client.get("/nonexistent")
    assert response.status_code == 404  # Assuming this endpoint does not exist
    assert "error" in response.json()  # Check for error key in response