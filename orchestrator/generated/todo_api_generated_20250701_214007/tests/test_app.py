import pytest
from app import app

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

def test_get_tasks(client):
    response = client.get('/tasks')
    assert response.status_code == 200

def test_add_task(client):
    response = client.post('/tasks', json={'content': 'Test Task'})
    assert response.status_code == 200

def test_delete_task(client):
    response = client.delete('/tasks/1')
    assert response.status_code == 200

def test_complete_task(client):
    response = client.put('/tasks/1/complete')
    assert response.status_code == 200