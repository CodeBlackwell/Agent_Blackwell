"""
Integration tests for the SpecAgent.
"""
import pytest
import asyncio
import json
from typing import Dict, Any, List
from unittest.mock import AsyncMock, patch, MagicMock

import redis.asyncio as redis
from src.config.settings import get_settings
from tests.integration.agents.base import BaseAgentIntegrationTest


class TestSpecAgentIntegration(BaseAgentIntegrationTest):
    """Test SpecAgent integration."""
    
    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.post")
    async def test_spec_agent_with_mock_llm(self, mock_post, redis_client, agent_fixtures, user_request_fixtures):
        """Test SpecAgent with mock LLM."""
        # Setup mock LLM response using the fixture data
        spec_output = agent_fixtures["spec"]["sample_outputs"][0]
        mock_response = await self.setup_mock_llm_response(spec_output)
        mock_post.return_value.__aenter__.return_value = mock_response
        
        # Get sample user request
        user_request = user_request_fixtures["spec"][0]
        
        # Prepare input message for the SpecAgent
        input_message = {
            "request_id": "test-request-123",
            "user_id": "test-user-456",
            "content": user_request["content"],
            "timestamp": "2025-06-26T00:30:00Z",
            "request_type": "specification",
            "priority": "high"
        }
        
        # Test that the agent produces the expected output
        expected_output_keys = ["request_id", "spec_details", "user_stories", "acceptance_criteria"]
        
        # Publish to agent input stream and assert correct output
        output_data = await self.assert_agent_produces_output(
            redis_client,
            "spec",
            input_message,
            expected_output_keys,
            timeout=10.0  # Allow more time for agent processing
        )
        
        # Assert specific content in the output
        assert "spec_details" in output_data, "spec_details missing from output"
        assert len(output_data["spec_details"]) > 0, "spec_details is empty"
        
        # Verify user stories exist and have expected format
        assert "user_stories" in output_data, "user_stories missing from output"
        user_stories = output_data["user_stories"]
        assert isinstance(user_stories, list), "user_stories should be a list"
        if user_stories:  # If any user stories exist
            assert isinstance(user_stories[0], dict), "user story should be a dictionary"
            assert "role" in user_stories[0], "user story missing 'role' field"
            assert "action" in user_stories[0], "user story missing 'action' field"
            assert "benefit" in user_stories[0], "user story missing 'benefit' field"
        
        # Verify acceptance criteria exist
        assert "acceptance_criteria" in output_data, "acceptance_criteria missing from output"
        criteria = output_data["acceptance_criteria"]
        assert isinstance(criteria, list), "acceptance_criteria should be a list"
        assert len(criteria) > 0, "acceptance_criteria is empty"
    
    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.post")
    async def test_spec_agent_handles_complex_request(self, mock_post, redis_client, agent_fixtures, user_request_fixtures):
        """Test SpecAgent with complex request."""
        # Setup mock LLM response for complex request
        complex_spec_output = agent_fixtures["spec"]["sample_outputs"][1]  # Using second sample output
        mock_response = await self.setup_mock_llm_response(complex_spec_output)
        mock_post.return_value.__aenter__.return_value = mock_response
        
        # Get complex user request
        complex_request = user_request_fixtures["complex"][0]
        
        # Prepare input message
        input_message = {
            "request_id": "complex-req-789",
            "user_id": "test-user-456",
            "content": complex_request["content"],
            "timestamp": "2025-06-26T00:35:00Z",
            "request_type": "specification",
            "priority": "critical",
            "complexity": "high"
        }
        
        # Expected output keys
        expected_output_keys = [
            "request_id", 
            "spec_details", 
            "user_stories", 
            "acceptance_criteria",
            "technical_requirements",
            "constraints"
        ]
        
        # Test agent output
        output_data = await self.assert_agent_produces_output(
            redis_client,
            "spec",
            input_message,
            expected_output_keys,
            timeout=15.0  # Allow more time for complex request
        )
        
        # Verify technical requirements exist for complex request
        assert "technical_requirements" in output_data, "technical_requirements missing for complex request"
        tech_reqs = output_data["technical_requirements"]
        assert isinstance(tech_reqs, list), "technical_requirements should be a list"
        assert len(tech_reqs) > 0, "technical_requirements is empty"
        
        # Verify constraints exist
        assert "constraints" in output_data, "constraints missing for complex request"
        
    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.post")
    async def test_spec_agent_handles_llm_error(self, mock_post, redis_client, user_request_fixtures):
        """Test SpecAgent handles LLM errors gracefully."""
        # Setup mock LLM error response
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.text = AsyncMock(return_value=json.dumps({"error": "Internal Server Error"}))
        mock_post.return_value.__aenter__.return_value = mock_response
        
        # Get sample user request
        user_request = user_request_fixtures["spec"][0]
        
        # Prepare input message
        input_message = {
            "request_id": "error-test-123",
            "user_id": "test-user-456",
            "content": user_request["content"],
            "timestamp": "2025-06-26T00:40:00Z",
            "request_type": "specification",
            "priority": "normal"
        }
        
        # Publish to agent input stream
        await self.publish_to_agent_stream(redis_client, "spec", input_message)
        
        # Wait for output - expecting error handling message
        message_id, message_data = await self.wait_for_agent_output(redis_client, "spec", timeout=10.0)
        
        # Should get an error response, not a timeout
        assert message_id is not None, "No error response received"
        assert message_data is not None, "Error message data is None"
        
        # Check for error indicators in response
        assert "error" in message_data or "error_code" in message_data, "Error indicators missing from response"
        assert "request_id" in message_data, "request_id missing in error response"
        assert message_data["request_id"] == input_message["request_id"], "request_id mismatch in error response"
        
    @pytest.mark.asyncio
    async def test_spec_agent_persistence(self, redis_client, agent_fixtures, user_request_fixtures):
        """Test that SpecAgent output is persisted correctly."""
        # Get sample spec output
        spec_output = agent_fixtures["spec"]["sample_outputs"][0]
        
        # Create a sample output message
        output_message = {
            "request_id": "persist-test-123",
            "user_id": "test-user-456",
            "spec_details": spec_output,
            "user_stories": [
                {"role": "user", "action": "submit a request", "benefit": "track progress"},
                {"role": "admin", "action": "review requests", "benefit": "ensure quality"}
            ],
            "acceptance_criteria": [
                "System must respond within 2 seconds",
                "All inputs must be validated"
            ],
            "timestamp": "2025-06-26T00:45:00Z"
        }
        
        # Manually publish to output stream to simulate agent output
        output_stream = "agent:spec:output"
        message_id = await redis_client.xadd(output_stream, output_message)
        
        # Verify message was added to stream
        messages = await redis_client.xrange(output_stream, min=message_id, max=message_id)
        assert len(messages) == 1, "Output message not found in stream"
        
        # Check if message content is correct
        _, stored_message = messages[0]
        assert stored_message["request_id"] == output_message["request_id"], "request_id not persisted correctly"
        assert stored_message["spec_details"] == output_message["spec_details"], "spec_details not persisted correctly"
        
        # Cleanup
        await redis_client.xdel(output_stream, message_id)
