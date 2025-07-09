import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_hello_world_endpoint():
    response = client.get("/hello")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, World!"}

def test_invalid_endpoint():
    response = client.get("/invalid")
    assert response.status_code == 404
    assert response.json() == {"error": "Not Found"}

def test_nonexistent_endpoint():
    response = client.get("/nonexistent")
    assert response.status_code == 404
    assert response.json() == {"error": "Not Found"}