"""
MVP Integration tests for incremental workflow.
Tests basic end-to-end functionality and fallback behavior.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import List
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from workflows.incremental.incremental_workflow import execute_incremental_workflow
from shared.data_models import (
    CodingTeamInput,
    TeamMemberResult,
    TeamMember
)
from workflows.monitoring import WorkflowExecutionTracer
from shared.utils.feature_parser import Feature, ComplexityLevel


class TestIncrementalWorkflowBasic:
    """Basic integration tests for incremental workflow"""
    
    @pytest.fixture
    def sample_input(self):
        """Create sample coding team input"""
        return CodingTeamInput(
            requirements="Create a simple calculator API with add and subtract operations"
        )
    
    @pytest.fixture
    def mock_planner_output(self):
        """Mock planner agent output"""
        return """
        # Project Plan: Calculator API
        
        ## Objective
        Create a RESTful API that provides basic calculator operations.
        
        ## Features
        1. Addition endpoint
        2. Subtraction endpoint
        
        ## Technical Requirements
        - Use FastAPI framework
        - Implement input validation
        - Return JSON responses
        """
    
    @pytest.fixture
    def mock_designer_output(self):
        """Mock designer agent output with features"""
        return """
        # Technical Design: Calculator API
        
        ## Architecture
        Simple REST API using FastAPI framework.
        
        ## Features
        
        ### Feature 1: Addition Endpoint
        **ID**: feat_add
        **Description**: Implement /add endpoint that takes two numbers and returns sum
        **Complexity**: Low
        **Files**: api/calculator.py, api/__init__.py
        **Validation**: Endpoint responds with correct sum for two numbers
        
        ### Feature 2: Subtraction Endpoint
        **ID**: feat_subtract
        **Description**: Implement /subtract endpoint that takes two numbers and returns difference
        **Complexity**: Low
        **Files**: api/calculator.py
        **Dependencies**: feat_add
        **Validation**: Endpoint responds with correct difference for two numbers
        
        ## API Endpoints
        - POST /add - Add two numbers
        - POST /subtract - Subtract two numbers
        """
    
    @pytest.fixture
    def mock_codebase(self):
        """Mock generated codebase"""
        return {
            "api/__init__.py": "",
            "api/calculator.py": """from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class CalculationRequest(BaseModel):
    a: float
    b: float

class CalculationResponse(BaseModel):
    result: float

@app.post("/add", response_model=CalculationResponse)
def add(request: CalculationRequest):
    return CalculationResponse(result=request.a + request.b)

@app.post("/subtract", response_model=CalculationResponse)
def subtract(request: CalculationRequest):
    return CalculationResponse(result=request.a - request.b)
"""
        }
    
    @pytest.mark.asyncio
    async def test_simple_incremental_workflow_end_to_end(self, sample_input, mock_planner_output, 
                                                         mock_designer_output, mock_codebase):
        """Test simple end-to-end incremental workflow execution"""
        # Mock the agent calls
        with patch('orchestrator.orchestrator_agent.run_team_member_with_tracking',
                   new_callable=AsyncMock) as mock_run_agent:
            
            # Setup agent responses in order
            mock_run_agent.side_effect = [
                mock_planner_output,      # Planner
                mock_designer_output,      # Designer
                "Code review passed"       # Reviewer
            ]
            
            # Mock the feature orchestrator
            with patch('workflows.incremental.incremental_workflow.FeatureOrchestrator') as mock_orchestrator_class:
                mock_orchestrator = Mock()
                mock_orchestrator_class.return_value = mock_orchestrator
                
                # Mock successful incremental execution
                mock_team_results = [
                    TeamMemberResult(
                        team_member=TeamMember.coder,
                        output="Generated calculator API code",
                        name="coder"
                    )
                ]
                mock_execution_summary = {
                    "total_features": 2,
                    "features_implemented": 2,
                    "success_rate": 100.0
                }
                
                mock_orchestrator.execute_incremental_development = AsyncMock(
                    return_value=(mock_team_results, mock_codebase, mock_execution_summary)
                )
                
                # Execute workflow
                results = await execute_incremental_workflow(sample_input)
                
                # Verify agent calls
                assert mock_run_agent.call_count == 3  # planner, designer, reviewer
                
                # Verify planner called correctly
                planner_call = mock_run_agent.call_args_list[0]
                assert planner_call[0][0] == "planner_agent"
                assert sample_input.requirements in planner_call[0][1]
                
                # Verify designer called correctly
                designer_call = mock_run_agent.call_args_list[1]
                assert designer_call[0][0] == "designer_agent"
                assert "plan" in designer_call[0][1].lower()
                
                # Verify orchestrator called correctly
                mock_orchestrator.execute_incremental_development.assert_called_once()
                orchestrator_call = mock_orchestrator.execute_incremental_development.call_args
                assert orchestrator_call[1]["designer_output"] == mock_designer_output
                assert orchestrator_call[1]["requirements"] == sample_input.requirements
                assert orchestrator_call[1]["max_retries"] == 3
                
                # Verify reviewer called
                reviewer_call = mock_run_agent.call_args_list[2]
                assert reviewer_call[0][0] == "reviewer_agent"
                
                # Verify results structure
                assert len(results) >= 4  # planner, designer, coder (from orchestrator), incremental_coder, reviewer
                
                # Check team members in results
                team_members = [r.team_member for r in results]
                assert TeamMember.planner in team_members
                assert TeamMember.designer in team_members
                assert TeamMember.reviewer in team_members
                
                # Verify at least one coder result
                coder_results = [r for r in results if r.team_member == TeamMember.coder]
                assert len(coder_results) >= 1
    
    @pytest.mark.asyncio
    async def test_incremental_workflow_fallback_to_standard(self, sample_input):
        """Test that workflow handles failures gracefully and can fall back"""
        # Mock the agent calls
        with patch('orchestrator.orchestrator_agent.run_team_member_with_tracking',
                   new_callable=AsyncMock) as mock_run_agent:
            
            # Setup agent responses
            mock_run_agent.side_effect = [
                "Planning output",
                "Design output without features",  # Designer output that won't parse features
                "Review output"
            ]
            
            # Mock the feature orchestrator to raise an error
            with patch('workflows.incremental.incremental_workflow.FeatureOrchestrator') as mock_orchestrator_class:
                mock_orchestrator = Mock()
                mock_orchestrator_class.return_value = mock_orchestrator
                
                # Simulate parsing failure - no features found
                mock_orchestrator.execute_incremental_development = AsyncMock(
                    side_effect=ValueError("No features found in designer output")
                )
                
                # Execute workflow - should raise the error
                with pytest.raises(ValueError, match="No features found"):
                    await execute_incremental_workflow(sample_input)
                
                # In a real implementation, this would fall back to standard workflow
                # For MVP, we just verify the error is properly propagated
                mock_orchestrator.execute_incremental_development.assert_called_once()