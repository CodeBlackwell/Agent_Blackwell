"""
Integration tests for the Review Agent.
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


class TestReviewAgentIntegration:
    """Integration tests for the Review Agent with the Orchestrator."""

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
            mock_read = MagicMock(return_value="Review Agent Prompt: {code_files}")
            mock_file.return_value.__enter__.return_value.read = mock_read
            yield mock_file

    @pytest.mark.asyncio
    @patch("src.agents.review_agent.ChatOpenAI")
    @patch("redis.Redis")
    async def test_process_task_with_review_agent(
        self,
        mock_redis,
        mock_chat_openai,
        mock_file_read,
        mock_redis_client,
    ):
        """Test processing a task with the Review Agent."""
        # Arrange
        mock_redis.return_value = mock_redis_client

        # Mock ChatOpenAI
        mock_llm = MagicMock()
        mock_llm_chain = MagicMock()
        mock_llm_chain.arun = AsyncMock(
            return_value=json.dumps(
                {
                    "summary": {
                        "linting_score": 7,
                        "security_score": 8,
                        "quality_score": 7,
                        "overall_score": 7.3,
                        "key_findings": ["Good structure", "Missing input validation"],
                    },
                    "linting_issues": [],
                    "security_issues": [],
                    "quality_issues": [],
                }
            )
        )
        mock_chat_openai.return_value = mock_llm

        # Create the test orchestrator that bypasses Pinecone initialization
        orchestrator = TestOrchestrator(
            redis_client=mock_redis_client,
            openai_api_key="fake-openai-key",
        )

        # Create a proper async mock for the review agent that directly mocks ainvoke
        review_agent_mock = AsyncMock()
        review_agent_mock.ainvoke = AsyncMock(
            return_value={
                "summary": {
                    "linting_score": 7,
                    "security_score": 8,
                    "quality_score": 7,
                    "overall_score": 7.3,
                    "key_findings": ["Good structure", "Missing input validation"],
                },
                "linting_issues": [],
                "security_issues": [],
                "quality_issues": [],
            }
        )
        orchestrator.agents["review"] = review_agent_mock

        # Create a review task with proper format
        task = {
            "task_id": "task123",
            "task_type": "review",
            "payload": {
                "code_files": [
                    {
                        "path": "app.py",
                        "content": "def add(a, b):\n    return a + b",
                    }
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
        assert "summary" in result["result"]
        assert "linting_issues" in result["result"]
        assert "security_issues" in result["result"]
        assert "quality_issues" in result["result"]
        review_agent_mock.ainvoke.assert_called_once_with(task)
        mock_redis_client.xadd.assert_called()

    @pytest.mark.asyncio
    @patch("redis.Redis")
    async def test_review_agent_error_handling(
        self,
        mock_redis,
        mock_file_read,
        mock_redis_client,
    ):
        """Test error handling when Review Agent fails."""
        # Arrange
        mock_redis.return_value = mock_redis_client

        # Create the test orchestrator that bypasses Pinecone initialization
        orchestrator = TestOrchestrator(
            redis_client=mock_redis_client,
            openai_api_key="fake-openai-key",
        )

        # Create a proper async mock for the review agent that raises an exception
        review_agent_mock = AsyncMock()
        review_agent_mock.ainvoke = AsyncMock(side_effect=Exception("Review error"))
        orchestrator.agents["review"] = review_agent_mock

        # Create a task with proper format
        task = {
            "task_id": "task456",
            "task_type": "review",
            "payload": {
                "code_files": [
                    {
                        "path": "app.py",
                        "content": "def add(a, b):\n    return a + b",
                    }
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
        assert "Review error" in result["error"]
        review_agent_mock.ainvoke.assert_called_once_with(task)
        mock_redis_client.xadd.assert_called()
