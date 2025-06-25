"""Tests for the messages endpoint that retrieves agent messages from Redis streams."""
import json
import os
import sys
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from api.main import app


@patch("src.api.v1.messages.get_redis")
def test_get_all_messages(mock_get_redis):
    """Test retrieving all messages from the Redis stream."""
    # Mock Redis
    mock_redis = AsyncMock()
    # Simulate two messages in the stream
    mock_redis.xrange.return_value = [
        ("1-0", {"field1": "value1"}),
        ("2-0", {"field2": "value2"}),
    ]
    mock_get_redis.return_value = mock_redis

    client = TestClient(app)
    response = client.get("/api/v1/messages")
    assert response.status_code == 200
    data = response.json()
    assert "messages" in data
    assert len(data["messages"]) == 2
    assert data["messages"][0]["id"] == "1-0"
    assert data["messages"][1]["id"] == "2-0"


@patch("src.api.v1.messages.get_redis")
def test_get_limited_messages(mock_get_redis):
    """Test retrieving a limited number of messages from the Redis stream."""
    mock_redis = AsyncMock()
    # Simulate one message returned by xrevrange
    mock_redis.xrevrange.return_value = [("2-0", {"field2": "value2"})]
    mock_get_redis.return_value = mock_redis

    client = TestClient(app)
    response = client.get("/api/v1/messages?number_of_messages=1")
    assert response.status_code == 200
    data = response.json()
    assert len(data["messages"]) == 1
    assert data["messages"][0]["id"] == "2-0"


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
    mock_redis.xrange.return_value = [
        ("1-0", {"task": json.dumps({"task_id": target_task_id, "task_type": "spec"})}),
        ("2-0", {"task": json.dumps({"task_id": "xyz789", "task_type": "design"})}),
        (
            "3-0",
            {"result": json.dumps({"task_id": target_task_id, "status": "complete"})},
        ),
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
