"""
MVP Unit tests for IncrementalExecutor.
Focuses on essential functionality only.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict

from orchestrator.utils.incremental_executor import (
    IncrementalExecutor,
    ValidationResult
)
from shared.utils.feature_parser import Feature, ComplexityLevel
from workflows.monitoring import WorkflowExecutionTracer


class TestIncrementalExecutorMVP:
    """MVP tests for IncrementalExecutor"""
    
    @pytest.fixture
    def mock_tracer(self):
        """Create a mock tracer"""
        tracer = Mock(spec=WorkflowExecutionTracer)
        tracer.start_step = Mock(return_value="validation_123")
        tracer.complete_step = Mock()
        return tracer
    
    @pytest.fixture
    def executor(self, mock_tracer):
        """Create IncrementalExecutor with session ID"""
        return IncrementalExecutor(
            session_id="test_session_123",
            tracer=mock_tracer
        )
    
    @pytest.fixture
    def sample_feature(self):
        """Create a sample feature for testing"""
        return Feature(
            id="feat_calc",
            title="Calculator Operations",
            description="Basic math operations",
            complexity=ComplexityLevel.LOW,
            files=["calculator.py"],
            dependencies=[],
            validation_criteria="Must implement add, subtract, multiply, divide"
        )
    
    @pytest.fixture
    def sample_files(self):
        """Sample implementation files"""
        return {
            "calculator.py": """def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b"""
        }
    
    def test_executor_initialization(self):
        """Test basic initialization of IncrementalExecutor"""
        # Create executor without tracer
        executor = IncrementalExecutor(session_id="test_123")
        
        # Verify initialization
        assert executor.session_id == "test_123"
        assert executor.tracer is None
        assert executor.codebase_state == {}
        assert executor.validated_features == []
        assert executor.error_analyzer is not None
        assert executor.granular_validator is not None
        
        # Create executor with tracer
        mock_tracer = Mock()
        executor_with_tracer = IncrementalExecutor(
            session_id="test_456",
            tracer=mock_tracer
        )
        assert executor_with_tracer.tracer == mock_tracer
    
    @pytest.mark.asyncio
    async def test_validate_feature_success(self, executor, sample_feature, sample_files, mock_tracer):
        """Test successful validation of a feature"""
        # Mock the run_team_member function
        with patch('orchestrator.utils.incremental_executor.run_team_member',
                   new_callable=AsyncMock) as mock_run:
            # Simulate successful validation output
            mock_run.return_value = """
            Validation Results:
            ✅ All validation criteria met
            - add function: Implemented correctly
            - subtract function: Implemented correctly
            - multiply function: Implemented correctly
            - divide function: Implemented with zero check
            
            Tests: 4 passed, 0 failed
            """
            
            # Execute validation
            result = await executor.validate_feature(
                feature=sample_feature,
                new_files=sample_files,
                existing_tests=None
            )
            
            # Verify run_team_member was called
            mock_run.assert_called_once()
            call_args = mock_run.call_args
            assert call_args[0][0] == "executor_agent"
            assert "Calculator Operations" in call_args[0][1]
            assert "calculator.py" in call_args[0][1]
            
            # Verify tracer interactions
            mock_tracer.start_step.assert_called_once_with(
                step_name="validate_feat_calc",
                agent_name="executor_agent",
                input_data={"feature": "feat_calc", "complexity": "low"}
            )
            mock_tracer.complete_step.assert_called_once()
            
            # Verify result
            assert isinstance(result, ValidationResult)
            assert result.success is True
            assert "validation criteria met" in result.feedback
            assert result.files_validated == ["calculator.py"]
            assert result.tests_passed == 4
            assert result.tests_failed == 0
            
            # Verify state updates
            assert executor.codebase_state == sample_files
            assert "feat_calc" in executor.validated_features
    
    @pytest.mark.asyncio
    async def test_validate_feature_failure(self, executor, sample_feature, mock_tracer):
        """Test validation failure handling"""
        # Create incomplete implementation
        incomplete_files = {
            "calculator.py": """def add(a, b):
    return a + b
# Missing other required functions"""
        }
        
        # Mock the run_team_member function
        with patch('orchestrator.utils.incremental_executor.run_team_member',
                   new_callable=AsyncMock) as mock_run:
            # Simulate validation failure output
            mock_run.return_value = """
            Validation Results:
            ❌ Validation failed
            - add function: Implemented correctly
            - subtract function: NOT FOUND
            - multiply function: NOT FOUND
            - divide function: NOT FOUND
            
            Error: Missing required functions
            Tests: 1 passed, 3 failed
            """
            
            # Execute validation
            result = await executor.validate_feature(
                feature=sample_feature,
                new_files=incomplete_files,
                existing_tests=None
            )
            
            # Verify result
            assert isinstance(result, ValidationResult)
            assert result.success is False
            assert "failed" in result.feedback.lower()
            assert result.files_validated == ["calculator.py"]
            assert result.tests_passed == 1
            assert result.tests_failed == 3
            
            # Verify feature not marked as validated
            assert "feat_calc" not in executor.validated_features
            
            # Verify codebase state still updated (for retry purposes)
            assert executor.codebase_state == incomplete_files
            
            # Verify tracer called correctly for failure
            mock_tracer.complete_step.assert_called_once()
            complete_call = mock_tracer.complete_step.call_args
            assert complete_call[1]["output_data"]["success"] is False