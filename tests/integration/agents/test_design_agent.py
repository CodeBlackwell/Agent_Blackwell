"""
Integration tests for the DesignAgent.
"""
import pytest
import asyncio
import json
from typing import Dict, Any, List
from unittest.mock import AsyncMock, patch, MagicMock

import redis.asyncio as redis
from src.config.settings import get_settings
from tests.integration.agents.base import BaseAgentIntegrationTest


class TestDesignAgentIntegration(BaseAgentIntegrationTest):
    """Test DesignAgent integration."""
    
    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.post")
    async def test_design_agent_with_mock_llm(self, mock_post, redis_client, agent_fixtures, user_request_fixtures):
        """Test DesignAgent with mock LLM."""
        # Setup mock LLM response using the fixture data
        design_output = agent_fixtures["design"]["sample_outputs"][0]
        mock_response = await self.setup_mock_llm_response(design_output)
        mock_post.return_value.__aenter__.return_value = mock_response
        
        # Get sample design request (spec output as input)
        spec_output = agent_fixtures["spec"]["sample_outputs"][0]
        
        # Prepare input message for the DesignAgent
        input_message = {
            "request_id": "design-test-123",
            "user_id": "test-user-456",
            "spec_details": spec_output,
            "user_stories": [
                {"role": "user", "action": "submit request", "benefit": "track progress"},
                {"role": "admin", "action": "review requests", "benefit": "ensure quality"}
            ],
            "acceptance_criteria": [
                "System must respond within 2 seconds",
                "All inputs must be validated"
            ],
            "timestamp": "2025-06-26T01:00:00Z",
            "request_type": "design",
            "priority": "high"
        }
        
        # Test that the agent produces the expected output
        expected_output_keys = ["request_id", "architecture", "data_models", "api_design", "ui_wireframes"]
        
        # Publish to agent input stream and assert correct output
        output_data = await self.assert_agent_produces_output(
            redis_client,
            "design",
            input_message,
            expected_output_keys,
            timeout=10.0
        )
        
        # Assert specific content in the output
        assert "architecture" in output_data, "architecture missing from output"
        architecture = output_data["architecture"]
        assert isinstance(architecture, dict), "architecture should be a dictionary"
        assert "components" in architecture, "architecture missing components"
        
        # Verify data models exist and have expected format
        assert "data_models" in output_data, "data_models missing from output"
        data_models = output_data["data_models"]
        assert isinstance(data_models, list), "data_models should be a list"
        if data_models:
            assert isinstance(data_models[0], dict), "data model should be a dictionary"
            assert "name" in data_models[0], "data model missing 'name' field"
            assert "fields" in data_models[0], "data model missing 'fields' field"
        
        # Verify API design exists
        assert "api_design" in output_data, "api_design missing from output"
        api_design = output_data["api_design"]
        assert isinstance(api_design, dict), "api_design should be a dictionary"
        assert "endpoints" in api_design, "api_design missing endpoints"
    
    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.post")
    async def test_design_agent_handles_complex_architecture(self, mock_post, redis_client, agent_fixtures, user_request_fixtures):
        """Test DesignAgent with complex architectural requirements."""
        # Setup mock LLM response for complex design
        complex_design_output = agent_fixtures["design"]["sample_outputs"][1]
        mock_response = await self.setup_mock_llm_response(complex_design_output)
        mock_post.return_value.__aenter__.return_value = mock_response
        
        # Get complex spec input
        complex_spec = agent_fixtures["spec"]["sample_outputs"][1]
        
        # Prepare input message with microservices requirements
        input_message = {
            "request_id": "complex-design-789",
            "user_id": "test-user-456",
            "spec_details": complex_spec,
            "user_stories": [
                {"role": "customer", "action": "place order", "benefit": "buy products"},
                {"role": "admin", "action": "manage inventory", "benefit": "track stock"}
            ],
            "acceptance_criteria": [
                "System must scale to 1M users",
                "99.9% uptime required",
                "Support multiple payment methods"
            ],
            "timestamp": "2025-06-26T01:05:00Z",
            "request_type": "design",
            "priority": "critical",
            "complexity": "high",
            "scale_requirements": "enterprise"
        }
        
        # Expected output keys for complex design
        expected_output_keys = [
            "request_id", "architecture", "data_models", "api_design", 
            "ui_wireframes", "scalability_plan", "security_design"
        ]
        
        # Test agent output
        output_data = await self.assert_agent_produces_output(
            redis_client,
            "design",
            input_message,
            expected_output_keys,
            timeout=15.0  # More time for complex processing
        )
        
        # Verify scalability considerations
        assert "scalability_plan" in output_data, "scalability_plan missing for complex design"
        scalability = output_data["scalability_plan"]
        assert isinstance(scalability, dict), "scalability_plan should be a dictionary"
        assert "load_balancing" in scalability, "load_balancing missing from scalability plan"
        
        # Verify security design
        assert "security_design" in output_data, "security_design missing for complex design"
        security = output_data["security_design"]
        assert isinstance(security, dict), "security_design should be a dictionary"
        assert "authentication" in security, "authentication missing from security design"
    
    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.post")
    async def test_design_agent_handles_llm_error(self, mock_post, redis_client, agent_fixtures):
        """Test DesignAgent handles LLM errors gracefully."""
        # Setup mock LLM error response
        mock_response = AsyncMock()
        mock_response.status = 503
        mock_response.text = AsyncMock(return_value=json.dumps({"error": "Service Unavailable"}))
        mock_post.return_value.__aenter__.return_value = mock_response
        
        # Get sample spec output as input
        spec_output = agent_fixtures["spec"]["sample_outputs"][0]
        
        # Prepare input message
        input_message = {
            "request_id": "error-design-123",
            "user_id": "test-user-456",
            "spec_details": spec_output,
            "timestamp": "2025-06-26T01:10:00Z",
            "request_type": "design",
            "priority": "normal"
        }
        
        # Publish to agent input stream
        await self.publish_to_agent_stream(redis_client, "design", input_message)
        
        # Wait for output - expecting error handling message
        message_id, message_data = await self.wait_for_agent_output(redis_client, "design", timeout=10.0)
        
        # Should get an error response, not a timeout
        assert message_id is not None, "No error response received"
        assert message_data is not None, "Error message data is None"
        
        # Check for error indicators in response
        assert "error" in message_data or "error_code" in message_data, "Error indicators missing from response"
        assert "request_id" in message_data, "request_id missing in error response"
        assert message_data["request_id"] == input_message["request_id"], "request_id mismatch in error response"
    
    @pytest.mark.asyncio
    async def test_design_agent_persistence(self, redis_client, agent_fixtures):
        """Test that DesignAgent output is persisted correctly."""
        # Get sample design output
        design_output = agent_fixtures["design"]["sample_outputs"][0]
        
        # Create a sample output message
        output_message = {
            "request_id": "persist-design-123",
            "user_id": "test-user-456",
            "architecture": {
                "components": ["api-gateway", "user-service", "notification-service"],
                "patterns": ["microservices", "event-driven"],
                "technologies": ["FastAPI", "Redis", "PostgreSQL"]
            },
            "data_models": [
                {
                    "name": "User",
                    "fields": ["id", "email", "created_at"],
                    "relationships": ["has_many_requests"]
                }
            ],
            "api_design": {
                "endpoints": ["/users", "/requests", "/notifications"],
                "authentication": "JWT",
                "versioning": "v1"
            },
            "ui_wireframes": {
                "pages": ["dashboard", "profile", "settings"],
                "components": ["header", "sidebar", "main-content"]
            },
            "timestamp": "2025-06-26T01:15:00Z"
        }
        
        # Manually publish to output stream to simulate agent output
        output_stream = "agent:design:output"
        message_id = await redis_client.xadd(output_stream, output_message)
        
        # Verify message was added to stream
        messages = await redis_client.xrange(output_stream, min=message_id, max=message_id)
        assert len(messages) == 1, "Output message not found in stream"
        
        # Check if message content is correct
        _, stored_message = messages[0]
        assert stored_message["request_id"] == output_message["request_id"], "request_id not persisted correctly"
        assert "architecture" in stored_message, "architecture not persisted correctly"
        assert "data_models" in stored_message, "data_models not persisted correctly"
        
        # Cleanup
        await redis_client.xdel(output_stream, message_id)
    
    @pytest.mark.asyncio
    async def test_design_agent_spec_to_design_transition(self, redis_client, agent_fixtures):
        """Test the transition from SpecAgent output to DesignAgent input."""
        # Simulate the complete workflow: spec output → design input
        spec_output_message = {
            "request_id": "transition-test-456",
            "user_id": "test-user-789",
            "spec_details": agent_fixtures["spec"]["sample_outputs"][0],
            "user_stories": [
                {"role": "user", "action": "create account", "benefit": "access services"}
            ],
            "acceptance_criteria": ["Email validation required", "Password strength minimum 8 chars"],
            "timestamp": "2025-06-26T01:20:00Z"
        }
        
        # Publish spec output to spec output stream
        spec_output_stream = "agent:spec:output"
        spec_message_id = await redis_client.xadd(spec_output_stream, spec_output_message)
        
        # Create design input based on spec output
        design_input_message = {
            **spec_output_message,  # Inherit from spec output
            "request_type": "design",
            "previous_agent": "spec",
            "previous_message_id": spec_message_id
        }
        
        # Publish to design input stream
        design_input_stream = "agent:design:input"
        design_message_id = await redis_client.xadd(design_input_stream, design_input_message)
        
        # Verify both messages exist
        spec_messages = await redis_client.xrange(spec_output_stream, min=spec_message_id, max=spec_message_id)
        design_messages = await redis_client.xrange(design_input_stream, min=design_message_id, max=design_message_id)
        
        assert len(spec_messages) == 1, "Spec output not persisted"
        assert len(design_messages) == 1, "Design input not persisted"
        
        # Verify content consistency
        _, spec_stored = spec_messages[0]
        _, design_stored = design_messages[0]
        
        assert spec_stored["request_id"] == design_stored["request_id"], "request_id not consistent across transition"
        assert design_stored["previous_agent"] == "spec", "previous_agent not set correctly"
        
        # Cleanup
        await redis_client.xdel(spec_output_stream, spec_message_id)
        await redis_client.xdel(design_input_stream, design_message_id)
