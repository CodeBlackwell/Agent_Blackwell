"""
Unit tests for the Design Agent.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agents.design_agent import DesignAgent, DesignAgentWrapper


class TestDesignAgent:
    """Test cases for the Design Agent."""

    @pytest.fixture
    def mock_llm_chain(self):
        """Create a mock LLM chain."""
        mock_chain = AsyncMock()
        mock_chain.ainvoke.return_value = {
            "text": """
Here's an architecture diagram for the described system:

```mermaid
classDiagram
    class Orchestrator {
        +process_task()
        +enqueue_task()
        +run_loop()
    }
    class AgentRegistry {
        +register_agent()
        +get_agent()
    }
    class SpecAgent {
        +generate_tasks()
    }
    class DesignAgent {
        +generate_design()
    }

    Orchestrator --> AgentRegistry : uses
    AgentRegistry --> SpecAgent : manages
    AgentRegistry --> DesignAgent : manages
```

API Contract:

```json
{
  "openapi": "3.0.0",
  "info": {
    "title": "Agent Orchestration API",
    "version": "1.0.0",
    "description": "API for interacting with the agent orchestration system"
  },
  "paths": {
    "/tasks": {
      "post": {
        "summary": "Create a new task",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "properties": {
                  "description": {
                    "type": "string"
                  },
                  "type": {
                    "type": "string"
                  }
                }
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Task created successfully",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "task_id": {
                      "type": "string"
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```
"""
        }
        return mock_chain

    @pytest.fixture
    def design_agent(self, mock_llm_chain):
        """Create a Design Agent with mocked components."""
        # Create a mock file content
        mock_prompt_content = "You are a Design Agent responsible for creating architecture diagrams and API contracts based on task descriptions.\n\nTask Description: {task_description}\n\nAdditional Context: {additional_context}"

        # Setup the mocks
        mock_file = MagicMock()
        mock_file.__enter__.return_value.read.return_value = mock_prompt_content

        with patch("src.agents.design_agent.LLMChain", return_value=mock_llm_chain):
            with patch("src.agents.design_agent.ChatOpenAI"):
                with patch("src.agents.design_agent.Path"):
                    with patch("builtins.open", return_value=mock_file):
                        agent = DesignAgent(openai_api_key="fake-key")
                        return agent

    @pytest.mark.asyncio
    async def test_generate_design(self, design_agent, mock_llm_chain):
        """Test that the agent can generate a design."""
        # Call the generate_design method
        result = await design_agent.generate_design(
            "Create a task orchestration system", "Use Redis for queueing"
        )

        # Verify the LLM chain was called with the correct arguments
        mock_llm_chain.ainvoke.assert_called_once_with(
            {
                "task_description": "Create a task orchestration system",
                "additional_context": "Use Redis for queueing",
            }
        )

        # Verify the result contains the expected content
        assert "mermaid" in result.lower()
        assert "API Contract" in result

    @pytest.mark.asyncio
    async def test_design_agent_wrapper(self, design_agent):
        """Test the DesignAgentWrapper."""
        # Create a wrapper with the mocked agent
        wrapper = DesignAgentWrapper(design_agent)

        # Mock the generate_design method
        design_agent.generate_design = AsyncMock(return_value="Mocked design output")

        # Call the process_task method
        task_data = {
            "task_id": "test-task-id",
            "description": "Create an API",
            "metadata": {"context": "RESTful design"},
        }
        result = await wrapper.process_task(task_data)

        # Verify the agent was called with the correct arguments
        design_agent.generate_design.assert_called_once_with(
            "Create an API", "RESTful design"
        )

        # Verify the result has the expected structure
        assert result["task_id"] == "test-task-id"
        assert result["status"] == "completed"
        assert result["result"] == "Mocked design output"
        assert result["agent_type"] == "design"

    @pytest.mark.asyncio
    async def test_design_agent_error_handling(self, design_agent):
        """Test error handling in the Design Agent."""
        # Mock the chain to raise an exception
        design_agent.chain.ainvoke = AsyncMock(side_effect=Exception("Test error"))

        # Call the generate_design method
        result = await design_agent.generate_design("This will cause an error")

        # Verify the result is an error message
        assert "Error generating design" in result
        assert "Test error" in result
