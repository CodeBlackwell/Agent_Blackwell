"""
Integration tests for the Coding Agent.
"""

from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import pytest
from redis import Redis

from src.agents.coding_agent import CodingAgent
from src.orchestrator.agent_registry import AgentRegistry


class TestCodingAgentIntegration:
    """Test suite for the Coding Agent integration with the orchestrator."""

    @pytest.fixture
    def mock_agent_registry(self):
        """Create a mock AgentRegistry."""
        mock = MagicMock(spec=AgentRegistry)
        mock.get_agent = MagicMock()
        return mock

    @pytest.fixture
    def mock_redis_client(self):
        """Create a mock Redis client."""
        mock = MagicMock(spec=Redis)
        mock.xadd = MagicMock()
        mock.xread = MagicMock(return_value=[])
        return mock

    @pytest.fixture
    def mock_coding_agent(self):
        """Create a mock Coding Agent."""
        mock = MagicMock(spec=CodingAgent)
        mock.generate_code = AsyncMock(
            return_value={
                "files": [
                    {
                        "path": "test_file.py",
                        "content": "def hello_world():\n    return 'Hello, World!'",
                        "description": "A simple test file",
                    }
                ],
                "explanation": "This is a simple hello world function.",
            }
        )
        return mock

    @pytest.fixture
    def mock_file_read(self):
        """Mock file read operations."""
        with patch("builtins.open", mock_open()) as mock_file:
            # Create a mock file object with a read method
            mock_file_handle = mock_file.return_value.__enter__.return_value

            # Define the read method behavior based on file path
            def side_effect(*args, **kwargs):
                # Get the file path from the mock_calls
                for call in mock_file.mock_calls:
                    if call[0] == "()":
                        file_path = call[1][0]
                        if "coding_agent_prompt.txt" in file_path:
                            return "You are a Coding Agent. Generate code based on: {task_description}, {design_specs}, {architecture_diagram}"
                        elif "spec_agent_prompt.txt" in file_path:
                            return "You are a Spec Agent. Extract tasks from: {user_request}"
                        elif "design_agent_prompt.txt" in file_path:
                            return "You are a Design Agent. Create diagrams for: {task_description}"
                return "Default mock content"

            mock_file_handle.read.side_effect = side_effect
            yield mock_file

    @pytest.mark.asyncio
    @patch("src.orchestrator.agent_registry.CodingAgent")
    async def test_coding_agent_registration(
        self,
        mock_coding_agent_class,
        mock_agent_registry,
        mock_redis_client,
        mock_file_read,
    ):
        """Test that the Coding Agent is properly registered with the Orchestrator."""
        # Arrange
        mock_coding_agent_class.return_value = MagicMock()

        # Patch Redis.from_url to return our mock client
        with patch(
            "src.orchestrator.main.Redis.from_url", return_value=mock_redis_client
        ):
            # Create a real AgentRegistry with mocked agents
            with patch(
                "src.orchestrator.agent_registry.CodingAgent"
            ) as mock_coding_agent_class:
                mock_coding_agent_class.return_value = MagicMock()

                registry = AgentRegistry(openai_api_key="fake-api-key")
                registry.register_coding_agent()

                # Check that the coding agent is registered
                coding_agent = registry.get_agent("coding")
                assert coding_agent is not None, "Coding Agent should be registered"

                # Verify the agent has the expected interface
                assert hasattr(
                    coding_agent, "ainvoke"
                ), "Coding Agent should have ainvoke method"

    @pytest.mark.asyncio
    async def test_coding_agent_invocation(self, mock_coding_agent, mock_file_read):
        """Test that the Coding Agent can be invoked through the registry."""
        # Arrange
        with patch(
            "src.orchestrator.agent_registry.CodingAgent",
            return_value=mock_coding_agent,
        ):
            registry = AgentRegistry(openai_api_key="fake-api-key")
            registry.register_coding_agent()

            # Get the registered agent
            coding_agent = registry.get_agent("coding")

            # Act
            task = {
                "task_id": "test-task-123",
                "description": "Create a hello world function",
                "design_specs": "Function should return 'Hello, World!'",
                "architecture_diagram": "No diagram needed",
            }

            result = await coding_agent.ainvoke(task)

            # Assert
            assert result["task_id"] == "test-task-123"
            assert result["status"] == "completed"
            assert "result" in result
            assert "files" in result["result"]
            assert len(result["result"]["files"]) > 0
            assert "explanation" in result["result"]
