"""
Smoke test for the orchestrator.

This test verifies that the basic functionality of the orchestrator works:
- Enqueuing a task
- Processing the task
- Getting the expected result
"""

import json

import pytest
import redis

from src.orchestrator.main import Orchestrator


@pytest.fixture
def redis_client():
    """Create a Redis client for testing."""
    client = redis.Redis(host="localhost", port=6379, db=0)
    # Clear test streams
    client.delete("test_tasks")
    client.delete("test_results")
    yield client
    # Clean up
    client.delete("test_tasks")
    client.delete("test_results")


@pytest.mark.asyncio
async def test_orchestrator_ping_pong(redis_client):
    """Test that the orchestrator correctly processes a ping task and returns pong."""
    # Initialize orchestrator with test streams
    orchestrator = Orchestrator(
        redis_url="redis://localhost:6379",
        task_stream="test_tasks",
        result_stream="test_results",
    )

    # Register the dummy agent
    orchestrator.register_agent("dummy", None)

    # Enqueue a ping task
    task_id = await orchestrator.enqueue_task("dummy", {"input": "ping"})

    # Process the task manually (without starting the full loop)
    # Get the task from Redis
    response = redis_client.xread({"test_tasks": "0"}, count=1)
    stream_name, messages = response[0]
    message_id, message = messages[0]
    task_data = json.loads(message[b"task"].decode("utf-8"))

    # Process the task
    result = await orchestrator.process_task(task_data)

    # Verify the result
    assert result["status"] == "completed"
    assert result["result"] == "pong"
    assert result["task_id"] == task_id

    # Verify the result was stored in Redis
    response = redis_client.xread({"test_results": "0"}, count=1)
    stream_name, messages = response[0]
    message_id, message = messages[0]
    result_data = json.loads(message[b"result"].decode("utf-8"))

    assert result_data["status"] == "completed"
    assert result_data["result"] == "pong"
    assert result_data["task_id"] == task_id


@pytest.mark.asyncio
async def test_orchestrator_task_status(redis_client):
    """Test that the orchestrator correctly reports task status."""
    # Initialize orchestrator with test streams
    orchestrator = Orchestrator(
        redis_url="redis://localhost:6379",
        task_stream="test_tasks",
        result_stream="test_results",
    )

    # Register the dummy agent
    orchestrator.register_agent("dummy", None)

    # Enqueue a task
    task_id = await orchestrator.enqueue_task("dummy", {"input": "hello"})

    # Check status before processing
    status = await orchestrator.get_task_status(task_id)
    assert status["status"] == "pending"

    # Process the task
    response = redis_client.xread({"test_tasks": "0"}, count=1)
    stream_name, messages = response[0]
    message_id, message = messages[0]
    task_data = json.loads(message[b"task"].decode("utf-8"))
    await orchestrator.process_task(task_data)

    # Check status after processing
    status = await orchestrator.get_task_status(task_id)
    assert status["status"] == "completed"
    assert status["result"] == "echo: hello"


@pytest.mark.asyncio
async def test_orchestrator_nonexistent_agent(redis_client):
    """Test that the orchestrator handles tasks for nonexistent agents."""
    # Initialize orchestrator with test streams
    orchestrator = Orchestrator(
        redis_url="redis://localhost:6379",
        task_stream="test_tasks",
        result_stream="test_results",
    )

    # Enqueue a task for a nonexistent agent
    task_id = await orchestrator.enqueue_task("nonexistent", {"input": "test"})

    # Process the task
    response = redis_client.xread({"test_tasks": "0"}, count=1)
    stream_name, messages = response[0]
    message_id, message = messages[0]
    task_data = json.loads(message[b"task"].decode("utf-8"))
    result = await orchestrator.process_task(task_data)

    # Verify the result
    assert result["status"] == "error"
    assert "No agent registered" in result["error"]
    assert result["task_id"] == task_id
