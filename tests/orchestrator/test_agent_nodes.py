"""
Focused tests for LangGraph agent node functions and routing logic.

These tests verify the individual agent nodes work correctly,
handle errors properly, and implement correct routing decisions.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from src.orchestrator.agent_nodes import (
    spec_agent_node,
    design_agent_node,
    coding_agent_node,
    review_agent_node,
    testing_agent_node,  # Test agent node function
    should_continue_to_design,
    should_continue_to_coding,
    should_continue_to_review,
    should_continue_to_test
)
from src.orchestrator.workflow_state import (
    AgentWorkflowState,
    WorkflowStatus,
    AgentType,
    create_initial_state
)


class TestSpecAgentNode:
    """Test the spec_agent_node function."""
    
    @pytest.mark.asyncio
    @patch('src.orchestrator.agent_nodes.SpecAgent')
    async def test_spec_agent_node_success(self, mock_spec_agent):
        """Test successful spec agent execution."""
        # Setup mock
        mock_agent = AsyncMock()
        mock_spec_agent.return_value = mock_agent
        
        # Create mock tasks with model_dump method
        mock_task = MagicMock()
        mock_task.model_dump.return_value = {
            "task_id": "spec-1",
            "title": "API Design",
            "description": "Design REST API endpoints",
            "priority": "high"
        }
        mock_agent.generate_tasks.return_value = [mock_task]
        
        # Create initial state
        state = create_initial_state(
            workflow_id="test-workflow",
            task_id="test-task",
            task_type="feature_development",
            user_request="Create a REST API"
        )
        state["metadata"] = {"openai_api_key": "test-key"}
        
        # Execute node
        result_state = await spec_agent_node(state)
        
        # Verify results
        assert result_state["current_step"] == "design"
        assert len(result_state["spec_tasks"]) == 1
        assert result_state["spec_tasks"][0]["task_id"] == "spec-1"
        assert len(result_state["agent_results"]) == 1
        assert result_state["agent_results"][0]["agent_type"] == AgentType.SPEC.value
        assert result_state["agent_results"][0]["success"] is True
        assert result_state["agent_results"][0]["result"] is not None
        assert result_state["agent_results"][0]["error_message"] is None
    
    @pytest.mark.asyncio
    @patch('src.orchestrator.agent_nodes.SpecAgent')
    async def test_spec_agent_node_error(self, mock_spec_agent):
        """Test spec agent execution with error."""
        # Setup mock to raise exception
        mock_agent = AsyncMock()
        mock_spec_agent.return_value = mock_agent
        mock_agent.generate_tasks.side_effect = Exception("API key not found")
        
        # Create initial state
        state = create_initial_state(
            workflow_id="test-workflow",
            task_id="test-task",
            task_type="feature_development",
            user_request="Create a REST API"
        )
        
        # Execute node
        result_state = await spec_agent_node(state)
        
        # Verify error handling
        assert result_state["status"] == WorkflowStatus.FAILED
        assert len(result_state["agent_results"]) == 1
        assert result_state["agent_results"][0]["agent_type"] == AgentType.SPEC.value
        assert result_state["agent_results"][0]["success"] is False
        assert result_state["agent_results"][0]["error_message"] is not None
        assert "API key not found" in result_state["agent_results"][0]["error_message"]
        assert result_state["agent_results"][0]["result"] is None


class TestDesignAgentNode:
    """Test the design_agent_node function."""
    
    @pytest.mark.asyncio
    @patch('src.orchestrator.agent_nodes.DesignAgent')
    async def test_design_agent_node_success(self, mock_design_agent):
        """Test successful design agent execution."""
        # Setup mock
        mock_agent = AsyncMock()
        mock_design_agent.return_value = mock_agent
        mock_agent.generate_design.return_value = "Design specifications for REST API"
        
        # Create state with spec tasks
        state = create_initial_state(
            workflow_id="test-workflow",
            task_id="test-task",
            task_type="feature_development",
            user_request="Create a REST API"
        )
        state["spec_tasks"] = [
            {"task_id": "spec-1", "description": "Design REST API endpoints"}
        ]
        state["metadata"] = {"openai_api_key": "test-key"}
        
        # Execute node
        result_state = await design_agent_node(state)
        
        # Verify results
        assert result_state["current_step"] == "coding"
        assert result_state["design_specs"] == "Design specifications for REST API"
        assert len(result_state["agent_results"]) == 1
        assert result_state["agent_results"][0]["agent_type"] == AgentType.DESIGN
        assert result_state["agent_results"][0]["success"] is True
        assert result_state["agent_results"][0]["result"] is not None
        assert result_state["agent_results"][0]["error_message"] is None
    
    @pytest.mark.asyncio
    @patch('src.orchestrator.agent_nodes.DesignAgent')
    async def test_design_agent_node_no_spec_tasks(self, mock_design_agent):
        """Test design agent execution without spec tasks."""
        # Create state without spec tasks
        state = create_initial_state(
            workflow_id="test-workflow",
            task_id="test-task",
            task_type="feature_development",
            user_request="Create a REST API"
        )
        
        # Execute node
        result_state = await design_agent_node(state)
        
        # Verify error handling
        assert result_state["status"] == WorkflowStatus.FAILED
        assert len(result_state["agent_results"]) == 1
        assert result_state["agent_results"][0]["agent_type"] == AgentType.DESIGN
        assert result_state["agent_results"][0]["success"] is False
        assert result_state["agent_results"][0]["error_message"] is not None
        assert "No spec tasks available" in result_state["agent_results"][0]["error_message"]
        assert result_state["agent_results"][0]["result"] is None


class TestCodingAgentNode:
    """Test the coding_agent_node function."""
    
    @pytest.mark.asyncio
    @patch('src.orchestrator.agent_nodes.CodingAgent')
    async def test_coding_agent_node_success(self, mock_coding_agent):
        """Test successful coding agent execution."""
        # Setup mock
        mock_agent = AsyncMock()
        mock_coding_agent.return_value = mock_agent
        mock_agent.generate_code.return_value = "Generated Python code"
        
        # Create state with design specs
        state = create_initial_state(
            workflow_id="test-workflow",
            task_id="test-task",
            task_type="feature_development",
            user_request="Create a REST API"
        )
        state["design_specs"] = "Design specifications for REST API"
        state["spec_tasks"] = [
            {"task_id": "spec-1", "description": "Design REST API endpoints"}
        ]
        state["metadata"] = {"openai_api_key": "test-key"}
        
        # Execute node
        result_state = await coding_agent_node(state)
        
        # Verify results
        assert result_state["current_step"] == "review"
        assert result_state["code_result"] == "Generated Python code"
        assert len(result_state["agent_results"]) == 1
        assert result_state["agent_results"][0]["agent_type"] == AgentType.CODING
        assert result_state["agent_results"][0]["success"] is True
        assert result_state["agent_results"][0]["result"] is not None
        assert result_state["agent_results"][0]["error_message"] is None


class TestReviewAgentNode:
    """Test the review_agent_node function."""
    
    @pytest.mark.asyncio
    @patch('src.orchestrator.agent_nodes.ReviewAgent')
    async def test_review_agent_node_success(self, mock_review_agent):
        """Test successful review agent execution."""
        # Setup mock
        mock_agent = AsyncMock()
        mock_review_agent.return_value = mock_agent
        mock_agent.review_code.return_value = "Code review feedback"
        
        # Create state with code result
        state = create_initial_state(
            workflow_id="test-workflow",
            task_id="test-task",
            task_type="feature_development",
            user_request="Create a REST API"
        )
        state["code_result"] = "Generated Python code"
        state["spec_tasks"] = [
            {"task_id": "spec-1", "description": "Design REST API endpoints"}
        ]
        state["metadata"] = {"openai_api_key": "test-key"}
        
        # Execute node
        result_state = await review_agent_node(state)
        
        # Verify results
        assert result_state["current_step"] == "test"
        assert result_state["review_feedback"] == "Code review feedback"
        assert len(result_state["agent_results"]) == 1
        assert result_state["agent_results"][0]["agent_type"] == AgentType.REVIEW
        assert result_state["agent_results"][0]["success"] is True
        assert result_state["agent_results"][0]["result"] is not None
        assert result_state["agent_results"][0]["error_message"] is None


class TestTestAgentNode:
    """Test the test_agent_node function."""
    
    @pytest.mark.asyncio
    @patch('src.orchestrator.agent_nodes.TestGeneratorAgent')
    async def test_test_agent_node_success(self, mock_test_agent):
        """Test successful test agent execution."""
        # Setup mock
        mock_agent = AsyncMock()
        mock_test_agent.return_value = mock_agent
        mock_agent.generate_tests.return_value = "Generated test code"
        
        # Create state with code result
        state = create_initial_state(
            workflow_id="test-workflow",
            task_id="test-task",
            task_type="feature_development",
            user_request="Create a REST API"
        )
        state["code_result"] = "Generated Python code"
        state["spec_tasks"] = [
            {"task_id": "spec-1", "description": "Design REST API endpoints"}
        ]
        state["metadata"] = {"openai_api_key": "test-key"}
        
        # Execute node
        result_state = await testing_agent_node(state)
        
        # Verify results
        assert result_state["current_step"] == "completed"
        assert result_state["status"] == WorkflowStatus.COMPLETED
        assert result_state["test_results"] == "Generated test code"
        assert len(result_state["agent_results"]) == 1
        assert result_state["agent_results"][0]["agent_type"] == AgentType.TEST
        assert result_state["agent_results"][0]["success"] is True
        assert result_state["agent_results"][0]["result"] is not None
        assert result_state["agent_results"][0]["error_message"] is None
    
    @pytest.mark.asyncio
    @patch('src.orchestrator.agent_nodes.TestGeneratorAgent')
    async def test_test_agent_node_no_code(self, mock_test_agent):
        """Test test agent execution without code result."""
        # Create state without code result
        state = create_initial_state(
            workflow_id="test-workflow",
            task_id="test-task",
            task_type="feature_development",
            user_request="Create a REST API"
        )
        
        # Execute node
        result_state = await testing_agent_node(state)
        
        # Verify error handling
        assert result_state["status"] == WorkflowStatus.FAILED
        assert len(result_state["agent_results"]) == 1
        assert result_state["agent_results"][0]["agent_type"] == AgentType.TEST
        assert result_state["agent_results"][0]["success"] is False
        assert result_state["agent_results"][0]["error_message"] is not None
        assert "No code available" in result_state["agent_results"][0]["error_message"]
        assert result_state["agent_results"][0]["result"] is None


class TestStatePersistence:
    """Test state persistence across agent nodes."""
    
    @pytest.mark.asyncio
    @patch('src.orchestrator.agent_nodes.SpecAgent')
    @patch('src.orchestrator.agent_nodes.DesignAgent')
    async def test_state_persistence_across_nodes(self, mock_design_agent, mock_spec_agent):
        """Test that state is properly preserved across multiple agent executions."""
        # Setup mocks
        mock_spec = AsyncMock()
        mock_spec_agent.return_value = mock_spec
        mock_task = MagicMock()
        mock_task.model_dump.return_value = {"task_id": "spec-1", "description": "API spec"}
        mock_spec.generate_tasks.return_value = [mock_task]
        
        mock_design = AsyncMock()
        mock_design_agent.return_value = mock_design
        mock_design.generate_design.return_value = "Design specs"
        
        # Create initial state
        initial_state = create_initial_state(
            workflow_id="persistence-test",
            task_id="persistence-task",
            task_type="feature_development",
            user_request="Create a REST API"
        )
        initial_state["metadata"] = {"openai_api_key": "test-key"}
        
        # Execute spec agent
        after_spec = await spec_agent_node(initial_state)
        
        # Verify spec agent results are preserved
        assert len(after_spec["spec_tasks"]) == 1
        assert len(after_spec["agent_results"]) == 1
        assert after_spec["agent_results"][0]["agent_type"] == AgentType.SPEC.value
        
        # Execute design agent
        after_design = await design_agent_node(after_spec)
        
        # Verify both spec and design results are preserved
        assert len(after_design["spec_tasks"]) == 1  # Spec results preserved
        assert after_design["design_specs"] == "Design specs"  # Design results added
        assert len(after_design["agent_results"]) == 2  # Both agent results preserved
        assert after_design["agent_results"][0]["agent_type"] == AgentType.SPEC.value
        assert after_design["agent_results"][1]["agent_type"] == AgentType.DESIGN.value
