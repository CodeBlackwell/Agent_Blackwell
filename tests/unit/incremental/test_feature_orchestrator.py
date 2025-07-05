"""
MVP Unit tests for FeatureOrchestrator.
Focuses on essential functionality only.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from workflows.incremental.feature_orchestrator import (
    FeatureOrchestrator,
    FeatureImplementationResult
)
from shared.utils.feature_parser import Feature, ComplexityLevel
from shared.data_models import TeamMemberResult, TeamMember
from workflows.monitoring import WorkflowExecutionTracer


class TestFeatureOrchestratorMVP:
    """MVP tests for FeatureOrchestrator"""
    
    @pytest.fixture
    def mock_tracer(self):
        """Create a mock tracer"""
        tracer = Mock(spec=WorkflowExecutionTracer)
        tracer.execution_id = "test_exec_123"
        tracer.add_metadata = Mock()
        tracer.start_step = Mock(return_value="step_123")
        tracer.complete_step = Mock()
        return tracer
    
    @pytest.fixture
    def orchestrator(self, mock_tracer):
        """Create FeatureOrchestrator with mock dependencies"""
        return FeatureOrchestrator(tracer=mock_tracer)
    
    @pytest.fixture
    def sample_feature(self):
        """Create a sample feature for testing"""
        return Feature(
            id="feat_1",
            title="Basic Calculator API",
            description="Create a simple calculator API",
            complexity=ComplexityLevel.LOW,
            files=["calculator.py"],
            dependencies=[],
            validation_criteria="Calculator must handle basic operations"
        )
    
    @pytest.fixture
    def designer_output(self):
        """Sample designer output with features"""
        return """
        # Implementation Plan

        ## Features

        ### Feature 1: Basic Calculator API
        **ID**: feat_1
        **Description**: Create a simple calculator API
        **Complexity**: Low
        **Files**: calculator.py
        **Validation**: Calculator must handle basic operations

        ## Architecture
        Simple REST API with basic math operations.
        """
    
    def test_orchestrator_initialization(self, mock_tracer):
        """Test basic initialization of FeatureOrchestrator"""
        # Create orchestrator
        orchestrator = FeatureOrchestrator(tracer=mock_tracer)
        
        # Verify initialization
        assert orchestrator.tracer == mock_tracer
        assert orchestrator.parser is not None
        assert orchestrator.results == []
    
    @pytest.mark.asyncio
    async def test_execute_incremental_development_success(self, orchestrator, designer_output, mock_tracer):
        """Test happy path for incremental development execution"""
        # Mock the parser to return a feature
        mock_feature = Feature(
            id="feat_1",
            title="Basic Calculator API",
            description="Create a simple calculator API",
            complexity=ComplexityLevel.LOW,
            files=["calculator.py"],
            dependencies=[],
            validation_criteria="Calculator must handle basic operations"
        )
        orchestrator.parser.parse = Mock(return_value=[mock_feature])
        
        # Mock execute_features_incrementally
        mock_completed = [{
            "feature": mock_feature,
            "code": "def add(a, b): return a + b",
            "files": {"calculator.py": "def add(a, b): return a + b"},
            "validation_passed": True,
            "retry_count": 0
        }]
        mock_codebase = {"calculator.py": "def add(a, b): return a + b"}
        
        with patch('workflows.incremental.feature_orchestrator.execute_features_incrementally',
                   new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = (mock_completed, mock_codebase)
            
            # Execute
            results, codebase, summary = await orchestrator.execute_incremental_development(
                designer_output=designer_output,
                requirements="Create a calculator API",
                tests=None,
                max_retries=3
            )
            
            # Verify parser was called
            orchestrator.parser.parse.assert_called_once_with(designer_output)
            
            # Verify metadata was added
            assert mock_tracer.add_metadata.call_count >= 2
            mock_tracer.add_metadata.assert_any_call("feature_count", 1)
            
            # Verify execute was called with correct parameters
            mock_execute.assert_called_once()
            call_args = mock_execute.call_args
            assert call_args[1]["features"] == [mock_feature]
            assert call_args[1]["requirements"] == "Create a calculator API"
            assert call_args[1]["design"] == designer_output
            assert call_args[1]["max_retries"] == 3
            
            # Verify results
            assert len(results) == 1
            assert isinstance(results[0], TeamMemberResult)
            assert results[0].team_member == TeamMember.coder
            assert "Basic Calculator API" in results[0].output
            
            # Verify codebase
            assert codebase == mock_codebase
            
            # Verify summary
            assert summary["total_features"] == 1
            assert summary["completed_features"] == 1
            assert summary["failed_features"] == 0
            assert summary["success_rate"] == 100.0
    
    def test_feature_parsing_integration(self, orchestrator, designer_output):
        """Test that feature parsing works correctly"""
        # Test actual parsing (not mocked)
        features = orchestrator.parser.parse(designer_output)
        
        # Verify features were extracted
        assert len(features) >= 1
        assert features[0].id == "feat_1"
        assert features[0].title == "Basic Calculator API"
        assert features[0].complexity == ComplexityLevel.LOW
        assert "calculator.py" in features[0].files
    
    @pytest.mark.asyncio
    async def test_basic_error_handling(self, orchestrator, mock_tracer):
        """Test that orchestrator handles basic errors gracefully"""
        # Test with empty designer output
        orchestrator.parser.parse = Mock(return_value=[])
        
        with pytest.raises(ValueError, match="No features found"):
            await orchestrator.execute_incremental_development(
                designer_output="",
                requirements="Create something",
                tests=None
            )
        
        # Test with parsing error
        orchestrator.parser.parse = Mock(side_effect=Exception("Parse error"))
        
        with pytest.raises(Exception, match="Parse error"):
            await orchestrator.execute_incremental_development(
                designer_output="Invalid content",
                requirements="Create something",
                tests=None
            )