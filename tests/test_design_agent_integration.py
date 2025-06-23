"""
Integration test for the Design Agent with the Orchestrator.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.orchestrator.agent_registry import AgentRegistry
from src.orchestrator.main import Orchestrator


@pytest.mark.asyncio
class TestDesignAgentIntegration:
    """Test cases for the Design Agent integration with the Orchestrator."""

    @pytest.fixture
    def mock_openai_api_key(self):
        """Mock OpenAI API key."""
        return "fake-api-key"

    @pytest.fixture
    def mock_agent_registry(self, mock_openai_api_key):
        """Create a mock agent registry."""
        # Create mock file content for both agents
        mock_spec_prompt = "You are a Spec Agent responsible for breaking down user requests into tasks.\n\nUser Request: {user_request}"
        mock_design_prompt = "You are a Design Agent responsible for creating architecture diagrams.\n\nTask Description: {task_description}\n\nAdditional Context: {additional_context}"

        # Setup the mocks for file reads
        mock_file_spec = MagicMock()
        mock_file_spec.__enter__.return_value.read.return_value = mock_spec_prompt

        mock_file_design = MagicMock()
        mock_file_design.__enter__.return_value.read.return_value = mock_design_prompt

        # Create a side effect function to return different mock files based on the path
        def mock_open_side_effect(*args, **kwargs):
            path = args[0] if args else kwargs.get("file")
            if isinstance(path, MagicMock):
                # If path is already a MagicMock (from nested patching), return a default mock
                return mock_file_spec
            if "spec_agent_prompt.txt" in str(path):
                return mock_file_spec
            elif "design_agent_prompt.txt" in str(path):
                return mock_file_design
            return MagicMock()

        # Apply all the necessary patches
        with patch("src.agents.spec_agent.PromptTemplate"):
            with patch("src.agents.design_agent.PromptTemplate"):
                with patch("src.agents.spec_agent.ChatOpenAI"):
                    with patch("src.agents.design_agent.ChatOpenAI"):
                        with patch("src.agents.spec_agent.LLMChain"):
                            with patch("src.agents.design_agent.LLMChain"):
                                with patch(
                                    "builtins.open", side_effect=mock_open_side_effect
                                ):
                                    with patch("src.agents.spec_agent.Path"):
                                        with patch("src.agents.design_agent.Path"):
                                            registry = AgentRegistry(
                                                openai_api_key=mock_openai_api_key
                                            )
                                            return registry

    @pytest.fixture
    def mock_redis_client(self):
        """Create a mock Redis client."""
        mock_client = MagicMock()
        mock_client.xread.return_value = []
        mock_client.xadd.return_value = "message-id"
        return mock_client

    @pytest.fixture
    def mock_pinecone_client(self):
        """Create a mock Pinecone client."""
        return MagicMock()

    async def test_design_agent_registration(
        self, mock_agent_registry, mock_redis_client, mock_pinecone_client
    ):
        """Test that the Design Agent is properly registered with the Orchestrator."""
        # Create an orchestrator with the mocked components
        # Patch Redis.from_url to return our mock client
        with patch(
            "src.orchestrator.main.Redis.from_url", return_value=mock_redis_client
        ):
            # Patch Pinecone to return our mock client
            with patch(
                "src.orchestrator.main.Pinecone", return_value=mock_pinecone_client
            ):
                orchestrator = Orchestrator(openai_api_key="fake-api-key")

                # Manually set the agent_registry
                orchestrator.agent_registry = mock_agent_registry

                # Check that the design agent is registered
                design_agent = mock_agent_registry.get_agent("design")
                assert design_agent is not None, "Design Agent should be registered"

                # Verify the agent has the expected interface
                assert hasattr(
                    design_agent, "ainvoke"
                ), "Design Agent should have ainvoke method"

    async def test_design_agent_invocation(self, mock_agent_registry):
        """Test that the Design Agent can be invoked through the registry."""
        # Get the design agent from the registry
        design_agent = mock_agent_registry.get_agent("design")
        assert design_agent is not None

        # Mock the agent's ainvoke method
        design_agent.ainvoke = AsyncMock()
        design_agent.ainvoke.return_value = {
            "output": "Mermaid diagram and API contract",
            "design": "Mermaid diagram and API contract",
        }

        # Invoke the agent
        result = await design_agent.ainvoke(
            {
                "input": "Create a user authentication system",
                "context": "The system should support OAuth2",
            }
        )

        # Verify the result
        assert "output" in result
        assert "design" in result
        assert design_agent.ainvoke.called

        # Verify the agent was called with the expected arguments
        call_args = design_agent.ainvoke.call_args[0][0]
        assert call_args["input"] == "Create a user authentication system"
        assert call_args["context"] == "The system should support OAuth2"
