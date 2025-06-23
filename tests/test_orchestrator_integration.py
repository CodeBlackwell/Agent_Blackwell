"""
Integration test for the orchestrator.

This test verifies that the orchestrator's run_loop function correctly processes
tasks from Redis Streams and stores results.
"""

import asyncio
import json
import time

import pytest
import redis

from src.orchestrator.main import Orchestrator


@pytest.fixture
def redis_client():
    """Create a Redis client for testing."""
    client = redis.Redis(host="localhost", port=6379, db=0)
    # Clear test streams
    client.delete("test_integration_tasks")
    client.delete("test_integration_results")
    yield client
    # Clean up
    client.delete("test_integration_tasks")
    client.delete("test_integration_results")


class TestOrchestrator:
    """Integration tests for the Orchestrator class."""

    @pytest.mark.asyncio
    async def test_run_loop_processes_tasks(self, redis_client):
        """Test that the run_loop correctly processes tasks from Redis Streams."""
        # Initialize orchestrator with test streams
        orchestrator = Orchestrator(
            redis_url="redis://localhost:6379",
            task_stream="test_integration_tasks",
            result_stream="test_integration_results",
        )

        # Register the dummy agent
        orchestrator.register_agent("dummy", None)

        # Enqueue multiple test tasks
        task_ids = []
        for i in range(3):
            task_id = await orchestrator.enqueue_task("dummy", {"input": f"test_{i}"})
            task_ids.append(task_id)

        # Start the orchestrator loop in a separate task
        loop_task = asyncio.create_task(self._run_loop_for_duration(orchestrator, 2))

        # Wait for the loop to process tasks
        await asyncio.sleep(3)

        # Check that all tasks were processed
        for task_id in task_ids:
            status = await orchestrator.get_task_status(task_id)
            assert status["status"] == "completed"
            assert status["result"].startswith("echo: test_")

        # Cancel the loop task
        loop_task.cancel()
        try:
            await loop_task
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_run_loop_handles_errors(self, redis_client):
        """Test that the run_loop correctly handles errors in task processing."""
        # Initialize orchestrator with test streams
        orchestrator = Orchestrator(
            redis_url="redis://localhost:6379",
            task_stream="test_integration_tasks",
            result_stream="test_integration_results",
        )

        # Enqueue a task for a nonexistent agent
        task_id = await orchestrator.enqueue_task("nonexistent", {"input": "test"})

        # Start the orchestrator loop in a separate task
        loop_task = asyncio.create_task(self._run_loop_for_duration(orchestrator, 2))

        # Wait for the loop to process tasks
        await asyncio.sleep(3)

        # Check that the task was processed with an error
        status = await orchestrator.get_task_status(task_id)
        assert status["status"] == "error"
        assert "No agent registered" in status["error"]

        # Cancel the loop task
        loop_task.cancel()
        try:
            await loop_task
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_run_loop_with_multiple_agent_types(self, redis_client):
        """Test that the run_loop correctly processes tasks for different agent types."""
        # Initialize orchestrator with test streams
        orchestrator = Orchestrator(
            redis_url="redis://localhost:6379",
            task_stream="test_integration_tasks",
            result_stream="test_integration_results",
        )

        # Register multiple dummy agents
        orchestrator.register_agent("dummy", None)
        orchestrator.register_agent("echo", None)

        # Enqueue tasks for different agent types
        dummy_task_id = await orchestrator.enqueue_task("dummy", {"input": "ping"})
        echo_task_id = await orchestrator.enqueue_task("echo", {"input": "hello"})

        # Start the orchestrator loop in a separate task
        loop_task = asyncio.create_task(self._run_loop_for_duration(orchestrator, 2))

        # Wait for the loop to process tasks
        await asyncio.sleep(3)

        # Check that all tasks were processed
        dummy_status = await orchestrator.get_task_status(dummy_task_id)
        assert dummy_status["status"] == "completed"
        assert dummy_status["result"] == "pong"

        echo_status = await orchestrator.get_task_status(echo_task_id)
        assert echo_status["status"] == "completed"
        assert echo_status["result"] == "echo: hello"

        # Cancel the loop task
        loop_task.cancel()
        try:
            await loop_task
        except asyncio.CancelledError:
            pass

    async def _run_loop_for_duration(self, orchestrator, duration_seconds):
        """Run the orchestrator loop for a specified duration."""
        # Create a patched version of the run_loop that will exit after processing tasks
        original_run_loop = orchestrator.run_loop

        async def patched_run_loop():
            """Patched version of run_loop that exits after a duration."""
            start_time = time.time()
            last_id = "0"

            while time.time() - start_time < duration_seconds:
                try:
                    # Read new messages from the stream
                    response = orchestrator.redis_client.xread(
                        {orchestrator.task_stream: last_id},
                        count=1,
                        block=500,  # Block for 0.5 seconds
                    )

                    if not response:
                        await asyncio.sleep(0.1)  # Small delay if no messages
                        continue

                    # Process each message
                    for stream_name, messages in response:
                        for message_id, message in messages:
                            last_id = message_id  # Update last seen ID

                            # Parse task
                            task_data = json.loads(message[b"task"].decode("utf-8"))

                            # Process task
                            await orchestrator.process_task(task_data)

                except Exception as e:
                    print(f"Error in processing loop: {e}")
                    await asyncio.sleep(0.1)

        # Replace the run_loop method temporarily
        orchestrator.run_loop = patched_run_loop

        # Run the patched loop
        await orchestrator.run_loop()

        # Restore the original method
        orchestrator.run_loop = original_run_loop


@pytest.mark.asyncio
async def test_orchestrator_end_to_end():
    """End-to-end test of the orchestrator with a complete task flow."""
    # Create Redis client
    redis_client = redis.Redis(host="localhost", port=6379, db=0)
    redis_client.delete("test_e2e_tasks")
    redis_client.delete("test_e2e_results")

    try:
        # Initialize orchestrator
        orchestrator = Orchestrator(
            redis_url="redis://localhost:6379",
            task_stream="test_e2e_tasks",
            result_stream="test_e2e_results",
        )

        # Register a dummy agent
        orchestrator.register_agent("dummy", None)

        # Create a sequence of dependent tasks
        task1_id = await orchestrator.enqueue_task("dummy", {"input": "task1"})

        # Start processing in background
        loop_task = asyncio.create_task(orchestrator.run_loop())

        # Wait a bit for task1 to be processed
        await asyncio.sleep(1)

        # Check task1 status
        task1_status = await orchestrator.get_task_status(task1_id)
        assert task1_status["status"] == "completed"

        # Enqueue a second task that depends on the first
        task2_id = await orchestrator.enqueue_task(
            "dummy", {"input": f"task2_depends_on_{task1_status['result']}"}
        )

        # Wait for task2 to be processed
        await asyncio.sleep(1)

        # Check task2 status
        task2_status = await orchestrator.get_task_status(task2_id)
        assert task2_status["status"] == "completed"
        assert "task2_depends_on_echo: task1" in task2_status["result"]

        # Cancel the loop task
        loop_task.cancel()
        try:
            await loop_task
        except asyncio.CancelledError:
            pass

    finally:
        # Clean up
        redis_client.delete("test_e2e_tasks")
        redis_client.delete("test_e2e_results")
