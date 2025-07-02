import pytest
from app import app

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

def test_get_posts(client):
    response = client.get('/posts')
    assert response.status_code == 200

# Add more test cases based on the test scenarios provided