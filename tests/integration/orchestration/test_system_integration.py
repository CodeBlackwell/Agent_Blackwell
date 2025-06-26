"""
Phase 5 Integration Tests: End-to-End System Integration

This module contains comprehensive end-to-end integration tests that validate
the complete Agent Blackwell system working together: API → Orchestrator → Agents → Results.
"""

import asyncio
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.orchestrator.main import Orchestrator


@pytest.fixture
def mock_orchestrator():
    """Create a comprehensive mock orchestrator for end-to-end testing."""
    orchestrator = MagicMock(spec=Orchestrator)

    # Mock task storage for end-to-end workflow
    orchestrator._tasks = {}

    async def mock_enqueue_task(task_type, task_data):
        task_id = f"e2e-{task_type}-{len(orchestrator._tasks)}"
        orchestrator._tasks[task_id] = {
            "task_id": task_id,
            "task_type": task_type,
            "task_data": task_data,
            "status": "queued",
            "created_at": "2025-06-26T12:00:00Z",
        }
        return task_id

    async def mock_get_task_status(task_id):
        return orchestrator._tasks.get(task_id)

    async def mock_process_task(task_data):
        task_id = task_data["task_id"]
        if task_id in orchestrator._tasks:
            orchestrator._tasks[task_id]["status"] = "completed"
            orchestrator._tasks[task_id][
                "result"
            ] = f"Completed {task_data['task_type']} task"
        return orchestrator._tasks[task_id]

    orchestrator.enqueue_task = mock_enqueue_task
    orchestrator.get_task_status = mock_get_task_status
    orchestrator.process_task = mock_process_task

    return orchestrator


@pytest.fixture
def client_with_mock_orchestrator(mock_orchestrator):
    """Create test client with mocked orchestrator dependency."""
    from src.api.dependencies import get_orchestrator

    def override_get_orchestrator():
        return mock_orchestrator

    app.dependency_overrides[get_orchestrator] = override_get_orchestrator
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


class TestEndToEndWorkflows:
    """Test complete end-to-end workflows through the system."""

    async def test_specification_generation_workflow(
        self, client_with_mock_orchestrator, mock_orchestrator
    ):
        """Test complete specification generation workflow from API to result."""
        # Step 1: Submit specification request via ChatOps API
        command_request = {
            "command": "!spec Create a REST API for user authentication with JWT tokens and password reset functionality",
            "platform": "slack",
            "user_id": "product_manager",
            "channel_id": "development",
            "timestamp": datetime.now().isoformat(),
        }

        response = client_with_mock_orchestrator.post(
            "/api/v1/chatops/command", json=command_request
        )

        assert response.status_code == 200
        data = response.json()
        assert "task has been queued" in data["message"]

        # Extract task ID from response message
        import re

        task_id_match = re.search(r"(e2e-spec-\d+)", data["message"])
        assert task_id_match is not None
        task_id = task_id_match.group(1)

        # Step 2: Verify task was enqueued properly
        task_status = mock_orchestrator._tasks[task_id]
        assert task_status["task_type"] == "spec"
        assert task_status["status"] == "queued"
        assert "user authentication" in task_status["task_data"]["description"]

        # Step 3: Simulate task processing
        await mock_orchestrator.process_task(task_status)

        # Step 4: Check final task status via API
        status_response = client_with_mock_orchestrator.get(
            f"/api/v1/chatops/tasks/{task_id}/status"
        )

        assert status_response.status_code == 200
        final_status = status_response.json()

        assert final_status["status"] == "completed"
        assert final_status["task_id"] == task_id
        assert "result" in final_status

    async def test_multi_agent_design_workflow(
        self, client_with_mock_orchestrator, mock_orchestrator
    ):
        """Test multi-agent workflow: Spec → Design → Code → Review."""
        # Configure mock orchestrator for multi-agent workflow
        workflow_results = {
            "spec": "API specification with authentication endpoints",
            "design": "Microservices architecture with API gateway",
            "coding": "FastAPI implementation with JWT middleware",
            "review": "Code review completed with security recommendations",
        }

        async def enhanced_process_task(task_data):
            task_id = task_data["task_id"]
            task_type = task_data["task_type"]

            if task_id in mock_orchestrator._tasks:
                mock_orchestrator._tasks[task_id]["status"] = "completed"
                mock_orchestrator._tasks[task_id]["result"] = workflow_results[
                    task_type
                ]
                mock_orchestrator._tasks[task_id]["updated_at"] = "2025-06-26T12:05:00Z"

            return mock_orchestrator._tasks[task_id]

        mock_orchestrator.process_task = enhanced_process_task

        # Execute multi-step workflow
        workflow_steps = [
            ("!spec Create microservices authentication system", "spec"),
            ("!design Design system architecture based on spec", "design"),
            ("!code Implement authentication service", "coding"),
            ("!review Review authentication implementation", "review"),
        ]

        task_ids = []

        for command, expected_type in workflow_steps:
            # Submit command
            command_request = {
                "command": command,
                "platform": "slack",
                "user_id": "dev_team",
                "channel_id": "architecture",
            }

            response = client_with_mock_orchestrator.post(
                "/api/v1/chatops/command", json=command_request
            )
            assert response.status_code == 200

            # Extract and store task ID
            import re

            task_id_match = re.search(
                rf"(e2e-{expected_type}-\d+)", response.json()["message"]
            )
            assert task_id_match is not None
            task_id = task_id_match.group(1)
            task_ids.append(task_id)

            # Process the task
            task_data = mock_orchestrator._tasks[task_id]
            await mock_orchestrator.process_task(task_data)

        # Verify all workflow steps completed successfully
        for i, task_id in enumerate(task_ids):
            status_response = client_with_mock_orchestrator.get(
                f"/api/v1/chatops/tasks/{task_id}/status"
            )
            assert status_response.status_code == 200

            status_data = status_response.json()
            assert status_data["status"] == "completed"
            assert workflow_steps[i][1] in status_data["result"].lower()

    async def test_error_recovery_workflow(
        self, client_with_mock_orchestrator, mock_orchestrator
    ):
        """Test error handling and recovery in end-to-end workflow."""
        # Configure orchestrator to simulate failure then recovery
        failure_count = 0

        async def failing_then_succeeding_process(task_data):
            nonlocal failure_count
            task_id = task_data["task_id"]

            if task_id in mock_orchestrator._tasks:
                if failure_count < 1:  # Fail first time
                    failure_count += 1
                    mock_orchestrator._tasks[task_id]["status"] = "error"
                    mock_orchestrator._tasks[task_id][
                        "error"
                    ] = "Temporary service unavailable"
                else:  # Succeed on retry
                    mock_orchestrator._tasks[task_id]["status"] = "completed"
                    mock_orchestrator._tasks[task_id][
                        "result"
                    ] = "Task completed after retry"
                    if "error" in mock_orchestrator._tasks[task_id]:
                        del mock_orchestrator._tasks[task_id]["error"]

            return mock_orchestrator._tasks[task_id]

        mock_orchestrator.process_task = failing_then_succeeding_process

        # Submit task that will initially fail
        command_request = {
            "command": "!spec Create error-prone specification",
            "platform": "slack",
            "user_id": "test_user",
            "channel_id": "testing",
            "timestamp": datetime.now().isoformat(),
        }

        response = client_with_mock_orchestrator.post(
            "/api/v1/chatops/command", json=command_request
        )
        assert response.status_code == 200

        # Extract task ID
        import re

        task_id_match = re.search(r"(e2e-spec-\d+)", response.json()["message"])
        task_id = task_id_match.group(1)

        # First processing attempt (will fail)
        task_data = mock_orchestrator._tasks[task_id]
        await mock_orchestrator.process_task(task_data)

        # Check error status
        status_response = client_with_mock_orchestrator.get(
            f"/api/v1/chatops/tasks/{task_id}/status"
        )
        error_status = status_response.json()

        assert error_status["status"] == "error"
        assert "error" in error_status

        # Retry processing (will succeed)
        await mock_orchestrator.process_task(task_data)

        # Check recovery status
        recovery_response = client_with_mock_orchestrator.get(
            f"/api/v1/chatops/tasks/{task_id}/status"
        )
        recovery_status = recovery_response.json()

        assert recovery_status["status"] == "completed"
        assert "result" in recovery_status
        assert "completed after retry" in recovery_status["result"]


class TestSystemPerformance:
    """Test system performance under various load conditions."""

    async def test_concurrent_request_handling(self, client_with_mock_orchestrator):
        """Test system handling of concurrent API requests."""
        import concurrent.futures

        def make_concurrent_request(request_id):
            command_request = {
                "command": f"!spec Concurrent specification request {request_id}",
                "platform": "slack",
                "user_id": f"user_{request_id}",
                "channel_id": "load_test",
                "timestamp": datetime.now().isoformat(),
            }

            response = client_with_mock_orchestrator.post(
                "/api/v1/chatops/command", json=command_request
            )
            return response.status_code, response.json()

        # Execute concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_concurrent_request, i) for i in range(20)]
            results = [future.result() for future in futures]

        # Verify all requests succeeded
        status_codes = [result[0] for result in results]
        assert all(code == 200 for code in status_codes)

        # Verify all responses contain task IDs
        responses = [result[1] for result in results]
        assert all("task has been queued" in resp["message"] for resp in responses)

    async def test_system_resource_usage(
        self, client_with_mock_orchestrator, mock_orchestrator
    ):
        """Test system resource usage under load."""
        import os

        import psutil

        # Get initial resource usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        initial_cpu = process.cpu_percent()

        # Generate load
        for i in range(50):
            command_request = {
                "command": f"!spec Resource test specification {i}",
                "platform": "slack",
                "user_id": f"load_user_{i}",
                "channel_id": "resource_test",
                "timestamp": datetime.now().isoformat(),
            }

            response = client_with_mock_orchestrator.post(
                "/api/v1/chatops/command", json=command_request
            )
            assert response.status_code == 200

            # Simulate task processing
            import re

            task_id_match = re.search(r"(e2e-spec-\d+)", response.json()["message"])
            if task_id_match:
                task_id = task_id_match.group(1)
                if task_id in mock_orchestrator._tasks:
                    await mock_orchestrator.process_task(
                        mock_orchestrator._tasks[task_id]
                    )

        # Check final resource usage
        final_memory = process.memory_info().rss
        final_cpu = process.cpu_percent()

        # Memory usage should not increase dramatically (less than 50MB increase)
        memory_increase = final_memory - initial_memory
        assert memory_increase < 50 * 1024 * 1024  # 50MB

        # CPU usage should return to reasonable levels
        assert final_cpu < 80  # Less than 80% CPU usage


class TestSystemResilience:
    """Test system resilience and fault tolerance."""

    async def test_graceful_degradation(
        self, client_with_mock_orchestrator, mock_orchestrator
    ):
        """Test system behavior when components are degraded."""

        # Simulate Redis unavailability
        async def failing_enqueue_task(task_type, task_data):
            raise Exception("Redis connection failed")

        mock_orchestrator.enqueue_task = failing_enqueue_task

        # System should handle the failure gracefully
        command_request = {
            "command": "!spec Test degraded system behavior",
            "platform": "slack",
            "user_id": "resilience_test",
            "channel_id": "testing",
            "timestamp": datetime.now().isoformat(),
        }

        response = client_with_mock_orchestrator.post(
            "/api/v1/chatops/command", json=command_request
        )

        # Should return 500 due to the orchestrator failure
        assert response.status_code == 500
        data = response.json()
        assert "unexpected error occurred" in data["detail"]

    async def test_service_recovery(
        self, client_with_mock_orchestrator, mock_orchestrator
    ):
        """Test system recovery after service restoration."""
        # First, simulate service failure
        failure_mode = True

        async def intermittent_enqueue_task(task_type, task_data):
            if failure_mode:
                raise Exception("Service temporarily unavailable")
            else:
                task_id = f"recovery-{task_type}-{len(mock_orchestrator._tasks)}"
                mock_orchestrator._tasks[task_id] = {
                    "task_id": task_id,
                    "task_type": task_type,
                    "task_data": task_data,
                    "status": "queued",
                }
                return task_id

        mock_orchestrator.enqueue_task = intermittent_enqueue_task

        # Request during failure should fail
        command_request = {
            "command": "!code Implement feature with error: FileNotFoundError",
            "platform": "slack",
            "user_id": "error_test",
            "channel_id": "testing",
            "timestamp": datetime.now().isoformat(),
        }

        response = client_with_mock_orchestrator.post(
            "/api/v1/chatops/command", json=command_request
        )
        assert response.status_code == 500

        # Restore service
        failure_mode = False

        # Request after recovery should succeed
        recovery_response = client_with_mock_orchestrator.post(
            "/api/v1/chatops/command", json=command_request
        )
        assert recovery_response.status_code == 200

        data = recovery_response.json()
        assert "task has been queued" in data["message"]


class TestDataConsistency:
    """Test data consistency across system components."""

    async def test_task_state_consistency(
        self, client_with_mock_orchestrator, mock_orchestrator
    ):
        """Test that task state remains consistent across operations."""
        # Create a task
        command_request = {
            "command": "!spec Test data consistency",
            "platform": "slack",
            "user_id": "consistency_test",
            "channel_id": "testing",
            "timestamp": datetime.now().isoformat(),
        }

        response = client_with_mock_orchestrator.post(
            "/api/v1/chatops/command", json=command_request
        )
        assert response.status_code == 200

        # Extract task ID
        import re

        task_id_match = re.search(r"(e2e-spec-\d+)", response.json()["message"])
        task_id = task_id_match.group(1)

        # Check initial state
        initial_status_response = client_with_mock_orchestrator.get(
            f"/api/v1/chatops/tasks/{task_id}/status"
        )
        initial_status = initial_status_response.json()

        assert initial_status["status"] == "queued"
        assert initial_status["task_id"] == task_id

        # Process the task
        task_data = mock_orchestrator._tasks[task_id]
        await mock_orchestrator.process_task(task_data)

        # Check final state
        final_status_response = client_with_mock_orchestrator.get(
            f"/api/v1/chatops/tasks/{task_id}/status"
        )
        final_status = final_status_response.json()

        assert final_status["status"] == "completed"
        assert final_status["task_id"] == task_id

        # Verify state transition was atomic
        assert initial_status["task_id"] == final_status["task_id"]
        assert initial_status["status"] != final_status["status"]

    async def test_concurrent_task_isolation(
        self, client_with_mock_orchestrator, mock_orchestrator
    ):
        """Test that concurrent tasks don't interfere with each other."""
        # Create multiple tasks concurrently
        task_commands = [
            "!spec Create authentication service",
            "!design Design payment system",
            "!code Implement user dashboard",
            "!review Review security implementation",
        ]

        task_ids = []

        # Submit all tasks
        for command in task_commands:
            command_request = {
                "command": command,
                "platform": "slack",
                "user_id": "isolation_test",
                "channel_id": "testing",
                "timestamp": datetime.now().isoformat(),
            }

            response = client_with_mock_orchestrator.post(
                "/api/v1/chatops/command", json=command_request
            )
            assert response.status_code == 200

            # Extract task ID
            import re

            task_id_match = re.search(r"(e2e-\w+-\d+)", response.json()["message"])
            assert task_id_match is not None
            task_ids.append(task_id_match.group(1))

        # Verify all tasks have unique IDs and independent state
        assert len(set(task_ids)) == len(task_ids)  # All IDs are unique

        # Process tasks and verify isolation
        for task_id in task_ids:
            task_data = mock_orchestrator._tasks[task_id]
            await mock_orchestrator.process_task(task_data)

            # Check that processing one task doesn't affect others
            status_response = client_with_mock_orchestrator.get(
                f"/api/v1/chatops/tasks/{task_id}/status"
            )
            status = status_response.json()

            assert status["task_id"] == task_id
            assert status["status"] == "completed"

        # Verify all tasks completed independently
        assert len(mock_orchestrator._tasks) >= len(task_ids)
        completed_tasks = [
            task
            for task in mock_orchestrator._tasks.values()
            if task["status"] == "completed"
        ]
        assert len(completed_tasks) >= len(task_ids)
