"""
Tests for the messages API endpoint.

These tests verify the functionality of the messages endpoint,
which allows users to retrieve agent messages from Redis streams.
"""

import json
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from src.api.main import app


@patch("src.api.v1.messages.get_redis")
def test_get_all_messages(mock_get_redis):
    """Test retrieving all messages from the Redis stream."""
    mock_redis = AsyncMock()
    # Simulate two messages in the legacy stream
    mock_redis.xrange.side_effect = [
        # First call: legacy stream
        [
            ("1-0", {"field1": "value1"}),
            ("2-0", {"field2": "value2"}),
        ],
        # Second call: workflow metrics stream (empty for this test)
        []
    ]
    mock_get_redis.return_value = mock_redis

    client = TestClient(app)
    response = client.get("/api/v1/messages")
    assert response.status_code == 200
    data = response.json()
    assert "messages" in data
    assert len(data["messages"]) == 2
    assert data["messages"][0]["id"] == "1-0"
    assert data["messages"][0]["source"] == "legacy"
    assert data["messages"][1]["id"] == "2-0"
    assert data["messages"][1]["source"] == "legacy"


@patch("src.api.v1.messages.get_redis")
def test_get_limited_messages(mock_get_redis):
    """Test retrieving a limited number of messages from the Redis stream."""
    mock_redis = AsyncMock()
    # Simulate limited messages with xrevrange for legacy stream
    mock_redis.xrevrange.return_value = [
        ("3-0", {"field3": "value3"}),
        ("2-0", {"field2": "value2"}),
    ]
    # Empty workflow metrics stream
    mock_redis.xrange.return_value = []
    mock_get_redis.return_value = mock_redis

    client = TestClient(app)
    response = client.get("/api/v1/messages?number_of_messages=2")
    assert response.status_code == 200
    data = response.json()
    assert "messages" in data
    assert len(data["messages"]) == 2
    assert data["messages"][0]["id"] == "2-0"  # Reversed order becomes chronological
    assert data["messages"][1]["id"] == "3-0"


@patch("src.api.v1.messages.get_redis")
def test_get_messages_with_task_filter(mock_get_redis):
    """Test retrieving messages filtered by task ID."""
    mock_redis = AsyncMock()
    # Simulate messages with some containing task IDs
    mock_redis.xrange.side_effect = [
        # Legacy stream
        [
            ("1-0", {"task": '{"task_id": "task-123", "data": "some data"}'}),
            ("2-0", {"field2": "value2"}),  # No task ID
            ("3-0", {"result": '{"task_id": "task-456", "output": "result"}'}),
        ],
        # Workflow metrics stream (empty)
        []
    ]
    mock_get_redis.return_value = mock_redis

    client = TestClient(app)
    response = client.get("/api/v1/messages?task_id=task-123")
    assert response.status_code == 200
    data = response.json()
    assert "messages" in data
    assert len(data["messages"]) == 1
    assert data["messages"][0]["id"] == "1-0"


@patch("src.api.v1.messages.get_redis")
def test_get_messages_with_workflow_filter(mock_get_redis):
    """Test retrieving messages filtered by workflow ID."""
    mock_redis = AsyncMock()
    # Simulate workflow messages
    mock_redis.xrange.side_effect = [
        # Legacy stream (empty)
        [],
        # Workflow metrics stream
        [
            ("1-0", {"workflow_id": "workflow-123", "event_type": "started"}),
            ("2-0", {"workflow_id": "workflow-456", "event_type": "completed"}),
        ]
    ]
    mock_get_redis.return_value = mock_redis

    client = TestClient(app)
    response = client.get("/api/v1/messages?workflow_id=workflow-123")
    assert response.status_code == 200
    data = response.json()
    assert "messages" in data
    assert len(data["messages"]) == 1
    assert data["messages"][0]["id"] == "1-0"
    assert data["messages"][0]["source"] == "workflow"
    assert data["messages"][0]["workflow_id"] == "workflow-123"


@patch("src.api.v1.messages.get_redis")
def test_redis_error(mock_get_redis):
    """Test error handling when Redis operations fail."""
    mock_redis = AsyncMock()
    mock_redis.xrange.side_effect = Exception("Redis error")
    mock_get_redis.return_value = mock_redis

    client = TestClient(app)
    response = client.get("/api/v1/messages")
    assert response.status_code == 500
    data = response.json()
    assert "Error fetching messages" in data["detail"]


@patch("src.api.v1.messages.get_redis")
def test_filter_messages_by_task_id(mock_get_redis):
    """Test filtering messages by task ID."""
    mock_redis = AsyncMock()
    # Simulate three messages in the stream, two for the same task
    target_task_id = "abc123"
    mock_redis.xrange.side_effect = [
        # Legacy stream
        [
            ("1-0", {"task": json.dumps({"task_id": target_task_id, "task_type": "spec"})}),
            ("2-0", {"task": json.dumps({"task_id": "xyz789", "task_type": "design"})}),
            (
                "3-0",
                {"result": json.dumps({"task_id": target_task_id, "status": "complete"})},
            ),
        ],
        # Workflow metrics stream (empty)
        []
    ]
    mock_get_redis.return_value = mock_redis

    client = TestClient(app)
    response = client.get(f"/api/v1/messages?task_id={target_task_id}")

    assert response.status_code == 200
    data = response.json()

    # Should only return the two messages with matching task_id
    assert len(data["messages"]) == 2
    assert data["messages"][0]["id"] == "1-0"
    assert data["messages"][1]["id"] == "3-0"

    # Verify messages contain the correct task data
    task_data = json.loads(data["messages"][0]["task"])
    assert task_data["task_id"] == target_task_id

    result_data = json.loads(data["messages"][1]["result"])
    assert result_data["task_id"] == target_task_id
