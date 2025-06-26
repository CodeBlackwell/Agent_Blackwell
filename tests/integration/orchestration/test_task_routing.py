"""
Phase 5 Integration Tests: Task Routing and Orchestration

This module contains integration tests for task routing, agent coordination,
and orchestration workflow management in the Agent Blackwell system.
"""

import asyncio
import json
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.orchestrator.agent_registry import AgentRegistry
from src.orchestrator.main import Orchestrator


@pytest.fixture
async def orchestrator_client():
    """Create an orchestrator client for testing."""
    # Create orchestrator with test configuration
    orchestrator = Orchestrator(
        redis_url="redis://localhost:6379",
        task_stream="test_agent_tasks",
        result_stream="test_agent_results",
        skip_pinecone_init=True,  # Skip Pinecone for testing
    )

    # Mock the Redis client for testing
    orchestrator.redis_client = MagicMock()

    # Register mock agents
    mock_spec_agent = AsyncMock()
    mock_design_agent = AsyncMock()
    mock_coding_agent = AsyncMock()

    orchestrator.register_agent("spec", mock_spec_agent)
    orchestrator.register_agent("design", mock_design_agent)
    orchestrator.register_agent("coding", mock_coding_agent)

    return orchestrator


@pytest.mark.asyncio
class TestTaskRouting:
    """Test task routing and dispatch functionality."""

    async def test_task_enqueue_and_route(self, orchestrator_client):
        """Test task enqueuing and routing to appropriate agents."""
        # Mock Redis xadd to return a task ID
        orchestrator_client.redis_client.xadd.return_value = b"12345-0"

        # Test enqueuing different task types
        task_types = ["spec", "design", "coding"]

        for task_type in task_types:
            task_data = {
                "description": f"Test {task_type} task",
                "priority": "high",
                "user_id": "test_user",
            }

            task_id = await orchestrator_client.enqueue_task(task_type, task_data)

            # Verify task was enqueued
            assert task_id is not None
            orchestrator_client.redis_client.xadd.assert_called()

            # Check that the task data includes proper routing info
            last_call = orchestrator_client.redis_client.xadd.call_args
            stream_name, task_payload = last_call[0]

            assert stream_name == "test_agent_tasks"

            # Handle both dictionary and byte string payloads
            if isinstance(task_payload, dict) and "task" in task_payload:
                # Dictionary payload format
                task_str = task_payload["task"]
                task_json = (
                    json.loads(task_str) if isinstance(task_str, str) else task_str
                )
            elif isinstance(task_payload, dict) and isinstance(
                next(iter(task_payload.values()), None), str
            ):
                # Direct JSON string in dict value
                task_str = next(iter(task_payload.values()))
                task_json = json.loads(task_str)
            else:
                # Byte string format
                assert b"task" in task_payload
                task_json = json.loads(task_payload[b"task"].decode())

            assert task_json["task_type"] == task_type
            assert "description" in task_json

    async def test_task_lifecycle_management(self, orchestrator_client):
        """Test complete task lifecycle from creation to completion."""
        # Mock successful agent execution
        mock_agent = orchestrator_client.agents["spec"]
        mock_agent.ainvoke.return_value = {
            "status": "completed",
            "result": "Test specification generated successfully",
            "artifacts": ["spec.md", "requirements.txt"],
        }

        # Create and process a task
        task_data = {
            "task_id": "test-lifecycle-123",
            "task_type": "spec",
            "task_data": {
                "description": "Create API specification",
                "requirements": ["REST API", "Authentication"],
            },
            "created_at": "2025-06-26T12:00:00Z",
            "status": "pending",
        }

        # Process the task
        result = await orchestrator_client.process_task(task_data)

        # Verify task was processed correctly
        assert result["status"] == "completed"
        assert "result" in result
        assert result["task_id"] == "test-lifecycle-123"

        # Verify agent was called with correct parameters
        mock_agent.ainvoke.assert_called_once()
        call_args = mock_agent.ainvoke.call_args[0][0]
        # Agent receives task_data structure with description rather than input field
        assert call_args.get("description") == "Create API specification"

    async def test_agent_coordination_workflow(self, orchestrator_client):
        """Test multi-agent workflow coordination."""
        # Mock agents with different response types
        spec_result = {
            "status": "completed",
            "result": "API specification created",
            "next_agent": "design",
        }
        design_result = {
            "status": "completed",
            "result": "System design completed",
            "next_agent": "coding",
        }
        coding_result = {
            "status": "completed",
            "result": "Code implementation finished",
        }

        orchestrator_client.agents["spec"].ainvoke.return_value = spec_result
        orchestrator_client.agents["design"].ainvoke.return_value = design_result
        orchestrator_client.agents["coding"].ainvoke.return_value = coding_result

        # Simulate workflow chain
        tasks = [
            {
                "task_id": "workflow-spec-1",
                "task_type": "spec",
                "task_data": {"description": "Create specification"},
            },
            {
                "task_id": "workflow-design-1",
                "task_type": "design",
                "task_data": {
                    "description": "Design system",
                    "spec_result": spec_result,
                },
            },
            {
                "task_id": "workflow-coding-1",
                "task_type": "coding",
                "task_data": {
                    "description": "Implement code",
                    "design_result": design_result,
                },
            },
        ]

        results = []
        for task in tasks:
            result = await orchestrator_client.process_task(task)
            results.append(result)

        # Verify workflow progression
        assert all(r["status"] == "completed" for r in results)
        assert len(results) == 3

        # Verify each agent was called
        orchestrator_client.agents["spec"].ainvoke.assert_called_once()
        orchestrator_client.agents["design"].ainvoke.assert_called_once()
        orchestrator_client.agents["coding"].ainvoke.assert_called_once()


@pytest.mark.asyncio
class TestErrorHandling:
    """Test error handling and recovery mechanisms."""

    async def test_agent_failure_handling(self, orchestrator_client):
        """Test handling of agent execution failures."""
        # Mock agent failure
        mock_agent = orchestrator_client.agents["spec"]
        mock_agent.ainvoke.side_effect = Exception("Agent execution failed")

        task_data = {
            "task_id": "error-test-123",
            "task_type": "spec",
            "task_data": {"description": "This will fail"},
        }

        # Process task with error
        result = await orchestrator_client.process_task(task_data)

        # Verify error handling
        assert result["status"] == "error"
        assert "error" in result
        assert "Agent execution failed" in result["error"]
        assert result["task_id"] == "error-test-123"

    async def test_invalid_agent_type_handling(self, orchestrator_client):
        """Test handling of requests for non-existent agents."""
        task_data = {
            "task_id": "invalid-agent-test",
            "task_type": "nonexistent_agent",
            "task_data": {"description": "Test invalid agent"},
        }

        result = await orchestrator_client.process_task(task_data)

        # Verify proper error response
        assert result["status"] == "error"
        assert "No agent registered for task type: nonexistent_agent" in result["error"]

    async def test_task_retry_mechanism(self, orchestrator_client):
        """Test task retry functionality."""
        # Mock agent that fails first time, succeeds second time
        mock_agent = orchestrator_client.agents["spec"]
        mock_agent.ainvoke.side_effect = [
            Exception("Temporary failure"),
            {"status": "completed", "result": "Success on retry"},
        ]

        task_data = {
            "task_id": "retry-test-123",
            "task_type": "spec",
            "task_data": {"description": "Test retry mechanism"},
            "retry_count": 0,
            "max_retries": 2,
        }

        # First attempt should fail
        result1 = await orchestrator_client.process_task(task_data)
        assert result1["status"] == "error"

        # Update retry count and try again
        task_data["retry_count"] = 1
        result2 = await orchestrator_client.process_task(task_data)
        assert result2["status"] == "completed"


@pytest.mark.asyncio
class TestPerformanceAndConcurrency:
    """Test performance and concurrent task processing."""

    async def test_concurrent_task_processing(self, orchestrator_client):
        """Test handling of multiple concurrent tasks."""

        # Mock agents to simulate processing time
        async def mock_agent_work(input_data):
            await asyncio.sleep(0.1)  # Simulate work
            # Access task_data which includes the description field
            input_value = input_data.get("description", "") if input_data else ""
            return {"status": "completed", "result": f"Processed: {input_value}"}

        for agent_name in ["spec", "design", "coding"]:
            orchestrator_client.agents[agent_name].ainvoke.side_effect = mock_agent_work

        # Create multiple concurrent tasks
        tasks = []
        for i in range(10):
            task_data = {
                "task_id": f"concurrent-task-{i}",
                "task_type": "spec",
                "task_data": {"description": f"Concurrent task {i}"},
            }
            tasks.append(orchestrator_client.process_task(task_data))

        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks)

        # Verify all tasks completed successfully
        assert len(results) == 10
        assert all(r["status"] == "completed" for r in results)

        # Verify unique task IDs
        task_ids = [r["task_id"] for r in results]
        assert len(set(task_ids)) == 10

    async def test_task_queue_management(self, orchestrator_client):
        """Test task queue overflow and management."""
        # Mock Redis xlen to simulate queue length
        orchestrator_client.redis_client.xlen.return_value = 1000

        # Test queue status check
        queue_length = orchestrator_client.redis_client.xlen("test_agent_tasks")
        assert queue_length == 1000

        # Mock xadd for enqueuing
        orchestrator_client.redis_client.xadd.return_value = b"queue-test-0"

        # Test enqueuing with high queue length
        task_id = await orchestrator_client.enqueue_task(
            "spec", {"description": "Test queue management", "priority": "normal"}
        )

        assert task_id is not None
        orchestrator_client.redis_client.xadd.assert_called()
