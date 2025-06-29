"""
Integration tests for the Planning and Orchestrator agents working together.

Tests the complete flow from user request through planning to orchestration.
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.planning.planning_agent import PlanningAgent
from agents.orchestrator.orchestrator_agent import OrchestratorAgent
from acp_sdk.models import Message, MessagePart
from acp_sdk.server import Context
from config.config import AGENT_PORTS


class TestPlanningOrchestratorIntegration:
    """Integration tests for Planning and Orchestrator agents."""
    
    @pytest.fixture
    def planning_agent(self):
        """Create a Planning Agent instance."""
        return PlanningAgent("planner", AGENT_PORTS["planner"])
    
    @pytest.fixture
    def orchestrator_agent(self):
        """Create an Orchestrator Agent instance."""
        return OrchestratorAgent("orchestrator", AGENT_PORTS["orchestrator"])
    
    @pytest.fixture
    def mock_context(self):
        """Create a mock ACP context."""
        context = Mock(spec=Context)
        context.session = Mock()
        context.session.load_history = AsyncMock(return_value=[])
        return context
    
    @pytest.mark.asyncio
    async def test_planning_to_orchestration_flow(self, planning_agent, orchestrator_agent, mock_context):
        """Test complete flow from planning to orchestration."""
        # Step 1: Create user request
        user_request = "Build a task management web application with user authentication, REST API endpoints, and database storage for tasks and users"
        
        # Create planning request message
        planning_message_part = MessagePart(content=user_request)
        planning_message = Message(parts=[planning_message_part])
        
        # Step 2: Get job plan from Planning Agent
        planning_responses = []
        async for response in planning_agent.process_request([planning_message], mock_context):
            planning_responses.append(response)
        
        # Verify planning agent created a job plan
        assert len(planning_responses) >= 2
        job_plan_response = planning_responses[-1].content
        assert "Job plan created successfully" in job_plan_response
        assert "```json" in job_plan_response
        
        # Step 3: Extract job plan and pass to Orchestrator
        orchestrator_message_part = MessagePart(content=job_plan_response)
        orchestrator_message = Message(parts=[orchestrator_message_part])
        
        # Mock state manager for orchestrator
        with patch.object(orchestrator_agent.state_manager, 'create_pipeline') as mock_create:
            with patch.object(orchestrator_agent.state_manager, 'update_stage_status') as mock_update:
                # Mock pipeline state creation
                from state.state_manager import PipelineState
                mock_pipeline_state = Mock(spec=PipelineState)
                mock_create.return_value = mock_pipeline_state
                
                # Step 4: Process job plan with Orchestrator
                orchestration_responses = []
                async for response in orchestrator_agent.orchestrate_pipeline([orchestrator_message], mock_context):
                    orchestration_responses.append(response)
                
                # Verify orchestrator processed the job plan
                assert len(orchestration_responses) >= 3
                
                response_contents = [r.content for r in orchestration_responses]
                
                # Should show initialization
                assert any("Initializing pipeline orchestration" in content for content in response_contents)
                
                # Should show pipeline creation
                assert any("Created" in content and "feature pipeline" in content for content in response_contents)
                
                # Should show completion
                assert any("All pipelines completed successfully" in content for content in response_contents)
                
                # Verify state manager was called appropriately
                assert mock_create.call_count > 0  # Should create pipelines for features
                assert mock_update.call_count > 0  # Should update stage statuses
    
    @pytest.mark.asyncio
    async def test_complex_user_request_end_to_end(self, planning_agent, orchestrator_agent, mock_context):
        """Test complex user request through complete pipeline."""
        # Complex user request with multiple features
        user_request = """
        Create a comprehensive e-commerce platform with the following requirements:
        1. User authentication and authorization system
        2. Product catalog with search and filtering
        3. Shopping cart and checkout process
        4. Payment integration with external APIs
        5. Order management and tracking
        6. Admin dashboard for inventory management
        7. REST API for mobile app integration
        8. Database for users, products, orders, and analytics
        """
        
        # Step 1: Planning phase
        planning_message = Message(parts=[MessagePart(content=user_request)])
        
        planning_responses = []
        async for response in planning_agent.process_request([planning_message], mock_context):
            planning_responses.append(response)
        
        # Extract and parse job plan
        job_plan_response = planning_responses[-1].content
        json_start = job_plan_response.find("```json") + 7
        json_end = job_plan_response.find("```", json_start)
        job_plan_json = job_plan_response[json_start:json_end].strip()
        job_plan = json.loads(job_plan_json)
        
        # Verify comprehensive planning
        assert len(job_plan["feature_sets"]) >= 3  # Should detect multiple features
        assert job_plan["estimated_complexity"]["overall"] in ["medium", "high"]  # Should be complex
        
        # Check for expected features
        feature_names = [f["name"] for f in job_plan["feature_sets"]]
        assert "API Development" in feature_names
        assert "User Interface" in feature_names
        assert "Data Layer" in feature_names
        assert "Authentication" in feature_names
        
        # Step 2: Orchestration phase
        orchestrator_message = Message(parts=[MessagePart(content=job_plan_response)])
        
        with patch.object(orchestrator_agent.state_manager, 'create_pipeline') as mock_create:
            with patch.object(orchestrator_agent.state_manager, 'update_stage_status') as mock_update:
                from state.state_manager import PipelineState
                mock_pipeline_state = Mock(spec=PipelineState)
                mock_create.return_value = mock_pipeline_state
                
                orchestration_responses = []
                async for response in orchestrator_agent.orchestrate_pipeline([orchestrator_message], mock_context):
                    orchestration_responses.append(response)
                
                # Verify orchestration handled multiple features
                response_text = " ".join([r.content for r in orchestration_responses])
                
                # Should create multiple pipelines
                assert "Created" in response_text and "feature pipeline" in response_text
                
                # Should execute multiple pipelines
                for feature_name in feature_names:
                    assert feature_name in response_text
                
                # Should complete successfully
                assert "All pipelines completed successfully" in response_text
                
                # Verify state management calls
                assert mock_create.call_count == len(job_plan["feature_sets"])
                
                # Each pipeline has 5 stages, 2 status updates per stage
                expected_updates = len(job_plan["feature_sets"]) * 5 * 2
                assert mock_update.call_count == expected_updates
    
    @pytest.mark.asyncio
    async def test_error_propagation_between_agents(self, planning_agent, orchestrator_agent, mock_context):
        """Test error handling when planning output is malformed."""
        # Step 1: Create a scenario where planning might produce malformed output
        user_request = ""  # Empty request
        
        planning_message = Message(parts=[MessagePart(content=user_request)])
        
        planning_responses = []
        async for response in planning_agent.process_request([planning_message], mock_context):
            planning_responses.append(response)
        
        # Planning should handle empty request gracefully
        assert len(planning_responses) >= 1
        
        # Even with empty request, planning should create a default job plan
        job_plan_response = planning_responses[-1].content
        
        # Step 2: Pass potentially problematic output to orchestrator
        orchestrator_message = Message(parts=[MessagePart(content=job_plan_response)])
        
        with patch.object(orchestrator_agent.state_manager, 'create_pipeline') as mock_create:
            mock_create.return_value = Mock()
            
            orchestration_responses = []
            async for response in orchestrator_agent.orchestrate_pipeline([orchestrator_message], mock_context):
                orchestration_responses.append(response)
            
            # Orchestrator should handle the output appropriately
            assert len(orchestration_responses) >= 1
            
            # Should not crash - either process successfully or show error
            response_text = " ".join([r.content for r in orchestration_responses])
            assert response_text  # Should have some response
    
    @pytest.mark.asyncio
    async def test_dependency_handling_integration(self, planning_agent, orchestrator_agent, mock_context):
        """Test that dependencies identified in planning are respected in orchestration."""
        # Request that should create clear dependencies
        user_request = "Build a web application with a database backend, REST API layer, and React frontend"
        
        # Step 1: Planning
        planning_message = Message(parts=[MessagePart(content=user_request)])
        
        planning_responses = []
        async for response in planning_agent.process_request([planning_message], mock_context):
            planning_responses.append(response)
        
        # Extract job plan
        job_plan_response = planning_responses[-1].content
        json_start = job_plan_response.find("```json") + 7
        json_end = job_plan_response.find("```", json_start)
        job_plan_json = job_plan_response[json_start:json_end].strip()
        job_plan = json.loads(job_plan_json)
        
        # Verify dependencies were identified
        dependencies = job_plan["dependencies"]
        
        # UI should depend on API, API should depend on Data Layer
        if "User Interface" in dependencies and "API Development" in dependencies:
            # Check logical dependencies
            ui_deps = dependencies.get("User Interface", [])
            api_deps = dependencies.get("API Development", [])
            
            # Data Layer should have no dependencies
            data_deps = dependencies.get("Data Layer", [])
            assert data_deps == []
        
        # Step 2: Orchestration should respect these dependencies
        orchestrator_message = Message(parts=[MessagePart(content=job_plan_response)])
        
        with patch.object(orchestrator_agent.state_manager, 'create_pipeline') as mock_create:
            with patch.object(orchestrator_agent.state_manager, 'update_stage_status') as mock_update:
                mock_create.return_value = Mock()
                
                orchestration_responses = []
                async for response in orchestrator_agent.orchestrate_pipeline([orchestrator_message], mock_context):
                    orchestration_responses.append(response)
                
                # Verify orchestration created pipelines with dependency information
                pipelines_created = await orchestrator_agent.create_feature_pipelines(job_plan)
                
                # Find pipelines and verify dependencies are preserved
                for pipeline in pipelines_created:
                    feature_name = pipeline["feature_name"]
                    pipeline_deps = pipeline["dependencies"]
                    expected_deps = dependencies.get(feature_name, [])
                    assert pipeline_deps == expected_deps


class TestAgentCommunicationProtocol:
    """Test ACP protocol compliance between agents."""
    
    @pytest.mark.asyncio
    async def test_message_format_compatibility(self):
        """Test that Planning Agent output is compatible with Orchestrator input."""
        planning_agent = PlanningAgent("planner", AGENT_PORTS["planner"])
        orchestrator_agent = OrchestratorAgent("orchestrator", AGENT_PORTS["orchestrator"])
        
        mock_context = Mock(spec=Context)
        mock_context.session = Mock()
        mock_context.session.load_history = AsyncMock(return_value=[])
        
        # Test various user request formats
        test_requests = [
            "Simple web app",
            "Complex system with multiple microservices, databases, and user interfaces",
            "Mobile app with offline capabilities and cloud sync",
            "API-first platform with third-party integrations"
        ]
        
        for request in test_requests:
            # Get planning output
            planning_message = Message(parts=[MessagePart(content=request)])
            
            planning_responses = []
            async for response in planning_agent.process_request([planning_message], mock_context):
                planning_responses.append(response)
            
            job_plan_response = planning_responses[-1].content
            
            # Verify JSON format
            assert "```json" in job_plan_response
            json_start = job_plan_response.find("```json") + 7
            json_end = job_plan_response.find("```", json_start)
            job_plan_json = job_plan_response[json_start:json_end].strip()
            
            # Should be valid JSON
            job_plan = json.loads(job_plan_json)
            
            # Test orchestrator can process it
            orchestrator_message = Message(parts=[MessagePart(content=job_plan_response)])
            
            with patch.object(orchestrator_agent.state_manager, 'create_pipeline') as mock_create:
                mock_create.return_value = Mock()
                
                orchestration_responses = []
                async for response in orchestrator_agent.orchestrate_pipeline([orchestrator_message], mock_context):
                    orchestration_responses.append(response)
                
                # Should process without errors
                assert len(orchestration_responses) >= 1
                
                # Should not contain error messages
                response_text = " ".join([r.content for r in orchestration_responses])
                assert "Error parsing job plan JSON" not in response_text
    
    @pytest.mark.asyncio
    async def test_streaming_response_compatibility(self):
        """Test that both agents properly implement streaming responses."""
        planning_agent = PlanningAgent("planner", AGENT_PORTS["planner"])
        orchestrator_agent = OrchestratorAgent("orchestrator", AGENT_PORTS["orchestrator"])
        
        mock_context = Mock(spec=Context)
        mock_context.session = Mock()
        mock_context.session.load_history = AsyncMock(return_value=[])
        
        user_request = "Build a web application with authentication"
        
        # Test Planning Agent streaming
        planning_message = Message(parts=[MessagePart(content=user_request)])
        
        planning_responses = []
        async for response in planning_agent.process_request([planning_message], mock_context):
            planning_responses.append(response)
            # Verify each response is a proper MessagePart
            assert hasattr(response, 'content')
            assert isinstance(response.content, str)
        
        # Should have multiple responses (streaming)
        assert len(planning_responses) >= 2
        
        # Test Orchestrator Agent streaming
        job_plan_response = planning_responses[-1].content
        orchestrator_message = Message(parts=[MessagePart(content=job_plan_response)])
        
        with patch.object(orchestrator_agent.state_manager, 'create_pipeline') as mock_create:
            mock_create.return_value = Mock()
            
            orchestration_responses = []
            async for response in orchestrator_agent.orchestrate_pipeline([orchestrator_message], mock_context):
                orchestration_responses.append(response)
                # Verify each response is a proper MessagePart
                assert hasattr(response, 'content')
                assert isinstance(response.content, str)
            
            # Should have multiple responses (streaming)
            assert len(orchestration_responses) >= 3
