import pytest
from app import app

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

def test_add_task(client):
    response = client.post('/tasks', json={'content': 'Task 1'})
    assert response.status_code == 200

def test_delete_task(client):
    response = client.delete('/tasks/1')
    assert response.status_code == 200

def test_mark_complete(client):
    response = client.put('/tasks/1')
    assert response.status_code == 200