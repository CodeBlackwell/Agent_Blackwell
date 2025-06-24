"""
Integration tests for the Test Agent.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.orchestrator.main import Orchestrator


class TestOrchestrator(Orchestrator):
    """Test version of Orchestrator that bypasses Pinecone initialization."""

    __test__ = False  # Prevent pytest from collecting this as a test class

    def __init__(self, *args, **kwargs):
        """Initialize without setting up Pinecone."""
        # Initialize Redis client
        self.redis_client = kwargs.get("redis_client", MagicMock())
        self.task_stream = kwargs.get("task_stream", "agent_tasks")
        self.result_stream = kwargs.get("result_stream", "agent_results")

        # Skip real Pinecone initialization
        self.pinecone_client = MagicMock()
        mock_index = MagicMock()
        self.vector_index = mock_index

        # Initialize agent registry
        self.agents = {}
        self.agent_registry = None
        self.openai_api_key = kwargs.get("openai_api_key")

    async def get_agent(self, task_type):
        """Override to return the agent directly from the agents dict."""
        return self.agents.get(task_type)


class TestTestAgentIntegration:
    """Integration tests for the Test Agent with the Orchestrator."""

    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client."""
        mock = MagicMock()
        mock.xread.return_value = []
        mock.xgroup_create.return_value = True
        mock.xadd.return_value = "task_id"
        mock.xack.return_value = 1
        return mock

    @pytest.fixture
    def mock_file_read(self):
        """Mock file read operations."""
        with patch("builtins.open", MagicMock()) as mock_file:
            mock_read = MagicMock(return_value="Test Agent Prompt: {code_files}")
            mock_file.return_value.__enter__.return_value.read = mock_read
            yield mock_file

    @pytest.mark.asyncio
    @patch("redis.Redis")
    async def test_process_task_with_test_agent(
        self,
        mock_redis,
        mock_file_read,
        mock_redis_client,
    ):
        """Test processing a task with the Test Agent."""
        # Arrange
        mock_redis.return_value = mock_redis_client

        # Create the test orchestrator that bypasses Pinecone initialization
        orchestrator = TestOrchestrator(
            redis_client=mock_redis_client,
            openai_api_key="fake-openai-key",
        )

        # Create a mock for the test agent that directly mocks ainvoke
        test_agent_mock = AsyncMock()
        test_agent_mock.ainvoke = AsyncMock(
            return_value={
                "test_files": [
                    {
                        "path": "test_example.py",
                        "content": "def test_something(): assert True",
                    }
                ],
                "coverage_report": {
                    "overall_coverage": "90%",
                    "notes": "Good coverage",
                },
            }
        )
        orchestrator.agents["test"] = test_agent_mock

        # Create a test task with proper format
        task = {
            "task_id": "task123",
            "task_type": "test",
            "payload": {
                "code_files": [
                    {"path": "example.py", "content": "def hello(): return 'world'"}
                ]
            },
        }

        # Act
        result = await orchestrator.process_task(task)

        # Assert
        assert result is not None
        assert "status" in result
        assert result["status"] == "completed"
        assert "result" in result
        test_agent_mock.ainvoke.assert_called_once_with(task)
        mock_redis_client.xadd.assert_called()

    @pytest.mark.asyncio
    @patch("redis.Redis")
    async def test_test_agent_error_handling(
        self,
        mock_redis,
        mock_file_read,
        mock_redis_client,
    ):
        """Test error handling when Test Agent fails."""
        # Arrange
        mock_redis.return_value = mock_redis_client

        # Create the test orchestrator that bypasses Pinecone initialization
        orchestrator = TestOrchestrator(
            redis_client=mock_redis_client,
            openai_api_key="fake-openai-key",
        )

        # Create a mock for the test agent that raises an exception
        test_agent_mock = AsyncMock()
        test_agent_mock.ainvoke = AsyncMock(side_effect=Exception("Test error"))
        orchestrator.agents["test"] = test_agent_mock

        # Create a task with proper format
        task = {
            "task_id": "task456",
            "task_type": "test",
            "payload": {
                "code_files": [
                    {"path": "example.py", "content": "def hello(): return 'world'"}
                ]
            },
        }

        # Act
        result = await orchestrator.process_task(task)

        # Assert
        assert result is not None
        assert "status" in result
        assert result["status"] == "error"
        assert "error" in result
        assert "Test error" in result["error"]
        test_agent_mock.ainvoke.assert_called_once_with(task)
        mock_redis_client.xadd.assert_called()
