"""
Test script for validating the BaseAgent implementation.

This script creates a simple test agent that extends BaseAgent
and validates that it correctly handles ACP protocol messages.
"""

import asyncio
import os
import sys
from unittest.mock import patch, MagicMock

import pytest

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base_agent import BaseAgent
from acp_sdk.models import Message, MessagePart
from config.config import PROMPT_TEMPLATES


class TestAgent(BaseAgent):
    """
    Simple test agent that extends BaseAgent for testing purposes.
    """
    
    def __init__(self, name="test", port=9000):
        super().__init__(name, port)
        
    async def process_request(self, inputs, context):
        """
        Simple implementation that echoes back the input with a prefix.
        """
        input_content = inputs[0].parts[0].content if inputs and inputs[0].parts else "No input"
        response = f"Test Agent Response: {input_content}"
        
        # Use the stream_response method from BaseAgent
        async for part in self.stream_response(response):
            yield part


@pytest.fixture
def test_agent():
    """Fixture to create a test agent for each test."""
    return TestAgent()


def test_agent_initialization(test_agent):
    """Test that the agent initializes correctly."""
    assert test_agent.name == "test"
    assert test_agent.port == 9000
    assert test_agent.server is not None


def test_agent_run():
    """Test that the agent run method calls server.run with the correct port."""
    with patch('acp_sdk.server.Server.run') as mock_run:
        agent = TestAgent()
        agent.run()
        mock_run.assert_called_once_with(port=9000)


def test_system_prompt_loading():
    """Test that the agent loads the correct system prompt."""
    # Check if 'test' is in PROMPT_TEMPLATES
    if 'test' in PROMPT_TEMPLATES:
        # If it is, we need to adjust our test expectations
        test_agent = TestAgent()
        assert test_agent.system_prompt == PROMPT_TEMPLATES['test'].get('system', '')
    else:
        # If 'test' is not in PROMPT_TEMPLATES, system_prompt should be empty
        test_agent = TestAgent()
        assert test_agent.system_prompt == ''
    
    # Create a new agent with a name that exists in PROMPT_TEMPLATES
    planner_agent = TestAgent(name="planner", port=8001)
    assert planner_agent.system_prompt != ''
    assert "Planning Agent" in planner_agent.system_prompt


@pytest.mark.asyncio
async def test_process_request_async(test_agent):
    """Test the async process_request method."""
    # Create a mock input message
    test_message = Message(parts=[MessagePart(content="Hello")])
    mock_context = MagicMock()
    
    # Collect all yielded results
    results = []
    async for part in test_agent.process_request([test_message], mock_context):
        results.append(part.content)
    
    # Join all parts and verify the response
    full_response = "".join(results)
    assert full_response == "Test Agent Response: Hello"


@pytest.mark.asyncio
async def test_stream_response(test_agent):
    """Test the stream_response method."""
    test_content = "This is a test message for streaming."
    
    # Collect all yielded parts
    parts = []
    async for part in test_agent.stream_response(test_content):
        parts.append(part.content)
    
    # Join all parts and verify they match the original content
    streamed_content = "".join(parts)
    assert streamed_content == test_content
