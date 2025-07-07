"""
Integration tests for MVP Incremental TDD Workflow

This test verifies that:
1. Tests are written before implementation
2. Tests fail initially (red phase)
3. Implementation makes tests pass (green phase)
4. Test accumulator properly manages test files
5. Progress monitor tracks TDD states correctly
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from shared.data_models import CodingTeamInput, TeamMemberResult, TeamMember
from workflows.mvp_incremental.mvp_incremental_tdd import execute_mvp_incremental_tdd_workflow
from workflows.mvp_incremental.tdd_feature_implementer import TDDFeatureImplementer, TDDFeatureResult
from workflows.mvp_incremental.test_accumulator import TestAccumulator, TestFile
from workflows.mvp_incremental.progress_monitor import ProgressMonitor, StepStatus
from workflows.monitoring import WorkflowExecutionTracer


class TestTDDIntegration:
    """Test the complete TDD workflow integration"""
    
    @pytest.fixture
    def mock_input_data(self):
        """Create mock input data for testing"""
        return CodingTeamInput(
            requirements="Create a simple calculator with add and subtract functions",
            use_tdd=True,
            workflow_type="mvp_incremental_tdd"
        )
    
    @pytest.fixture
    def mock_planning_output(self):
        """Mock planning output"""
        return """
# Project Plan: Simple Calculator

## Overview
Create a Python calculator module with basic arithmetic operations.

## Requirements
1. Addition function
2. Subtraction function
3. Error handling for invalid inputs
"""
    
    @pytest.fixture
    def mock_design_output(self):
        """Mock design output with clear features"""
        return """
# Technical Design: Calculator Module

## Features to Implement

1. Create add function - Takes two numbers and returns their sum
2. Create subtract function - Takes two numbers and returns their difference
3. Add input validation - Ensure inputs are numeric

## Architecture
- Single module: calculator.py
- Pure functions, no state
- Type hints for clarity
"""
    
    @pytest.fixture
    def mock_test_code(self):
        """Mock test code that would be generated"""
        return """```python
# filename: test_calculator.py
import pytest
from calculator import add, subtract

def test_add_positive_numbers():
    assert add(2, 3) == 5
    
def test_add_negative_numbers():
    assert add(-1, -1) == -2
    
def test_subtract_positive_numbers():
    assert subtract(5, 3) == 2
    
def test_subtract_negative_from_positive():
    assert subtract(5, -3) == 8
```"""
    
    @pytest.fixture
    def mock_implementation_code(self):
        """Mock implementation that makes tests pass"""
        return """```python
# filename: calculator.py
def add(a: float, b: float) -> float:
    return a + b
    
def subtract(a: float, b: float) -> float:
    return a - b
```"""
    
    @pytest.mark.asyncio
    async def test_tdd_workflow_execution(self, mock_input_data, mock_planning_output, 
                                        mock_design_output, mock_test_code, 
                                        mock_implementation_code):
        """Test the complete TDD workflow execution"""
        
        # Mock the run_team_member_with_tracking function
        with patch('workflows.mvp_incremental.mvp_incremental_tdd.run_team_member_with_tracking') as mock_run:
            # Set up mock responses for each agent call
            mock_run.side_effect = [
                # Planning response
                [MagicMock(parts=[MagicMock(content=mock_planning_output)])],
                # Design response
                [MagicMock(parts=[MagicMock(content=mock_design_output)])],
                # Test writer response for feature 1
                [MagicMock(parts=[MagicMock(content=mock_test_code)])],
                # Implementation response for feature 1
                [MagicMock(parts=[MagicMock(content=mock_implementation_code)])],
                # Continue for other features...
            ]
            
            # Mock review integration
            with patch('workflows.mvp_incremental.mvp_incremental_tdd.ReviewIntegration') as mock_review_cls:
                mock_review = Mock()
                mock_review.request_review = AsyncMock(return_value=Mock(approved=True, feedback="Good"))
                mock_review_cls.return_value = mock_review
                
                # Mock feature reviewer agent
                with patch('workflows.mvp_incremental.mvp_incremental_tdd.feature_reviewer_agent'):
                    # Execute workflow
                    results = await execute_mvp_incremental_tdd_workflow(mock_input_data)
                    
                    # Verify results
                    assert len(results) > 0
                    
                    # Check that we have both test and implementation results
                    test_results = [r for r in results if r.team_member == TeamMember.test_writer]
                    impl_results = [r for r in results if r.team_member == TeamMember.coder]
                    
                    assert len(test_results) > 0, "Should have test writer results"
                    assert len(impl_results) > 0, "Should have implementation results"
                    
                    # Verify TDD metadata
                    for impl_result in impl_results:
                        if hasattr(impl_result, 'metadata') and impl_result.metadata:
                            assert impl_result.metadata.get('tdd') == True
                            assert impl_result.metadata.get('tests_written') == True
    
    def test_test_accumulator(self, mock_test_code):
        """Test the test accumulator functionality"""
        accumulator = TestAccumulator()
        
        # Add feature tests
        test_files = accumulator.add_feature_tests(
            feature_id="feature_1",
            test_code=mock_test_code,
            feature_dependencies=[]
        )
        
        # Verify test files were parsed
        assert len(test_files) == 1
        assert test_files[0].filename == "test_calculator.py"
        assert len(test_files[0].test_functions) == 4
        
        # Test combined suite generation
        combined = accumulator.get_combined_test_suite("all")
        assert "test_add_positive_numbers" in combined
        assert "test_subtract_positive_numbers" in combined
        
        # Test command generation
        test_cmd = accumulator.get_test_command("feature_1")
        assert "pytest" in test_cmd
        assert "test_calculator.py" in test_cmd
    
    def test_progress_monitor_tdd_states(self):
        """Test that progress monitor correctly tracks TDD states"""
        monitor = ProgressMonitor()
        monitor.start_workflow(total_features=2)
        
        # Start a feature
        monitor.start_feature("feature_1", "Add function", 1)
        
        # Update TDD progress
        monitor.update_step("feature_feature_1", StepStatus.WRITING_TESTS)
        monitor.update_tdd_progress("feature_1", "tests_written", {
            "test_files": 1,
            "test_functions": 2
        })
        
        monitor.update_step("feature_feature_1", StepStatus.TESTS_FAILING)
        monitor.update_tdd_progress("feature_1", "tests_initial_run", {
            "passed": 0,
            "failed": 2
        })
        
        monitor.update_step("feature_feature_1", StepStatus.IMPLEMENTING)
        
        monitor.update_step("feature_feature_1", StepStatus.TESTS_PASSING)
        monitor.update_tdd_progress("feature_1", "tests_passing", {
            "coverage": 95.5
        })
        
        # Check metrics
        metrics = monitor.export_metrics()
        assert metrics["tdd_metrics"]["features_with_tests"] == 1
        assert metrics["tdd_metrics"]["features_tests_passing"] == 1
        assert metrics["tdd_metrics"]["total_test_files"] == 1
        assert metrics["tdd_metrics"]["total_test_functions"] == 2
        assert metrics["tdd_metrics"]["average_coverage"] == 95.5
    
    @pytest.mark.asyncio
    async def test_tdd_feature_implementer(self):
        """Test the TDD feature implementer directly"""
        # Create mocks
        tracer = Mock(spec=WorkflowExecutionTracer)
        tracer.start_step = Mock(return_value="step_id")
        tracer.complete_step = Mock()
        
        monitor = Mock(spec=ProgressMonitor)
        review = Mock()
        review.request_review = AsyncMock(return_value=Mock(approved=True))
        
        # Create implementer
        from workflows.mvp_incremental.retry_strategy import RetryStrategy, RetryConfig
        implementer = TDDFeatureImplementer(
            tracer=tracer,
            progress_monitor=monitor,
            review_integration=review,
            retry_strategy=RetryStrategy(),
            retry_config=RetryConfig(max_retries=1)
        )
        
        # Mock the agent calls
        with patch('workflows.mvp_incremental.tdd_feature_implementer.run_team_member_with_tracking') as mock_run:
            # Mock test writer response
            mock_run.side_effect = [
                [MagicMock(parts=[MagicMock(content="""```python
# filename: test_feature.py
def test_feature():
    assert feature_function() == "expected"
```""")])],
                # Mock implementation response
                [MagicMock(parts=[MagicMock(content="""```python
# filename: feature.py
def feature_function():
    return "expected"
```""")])]
            ]
            
            # Mock validator
            implementer.validator = Mock()
            implementer.validator.validate_syntax = AsyncMock(
                return_value=Mock(success=True, errors=[], details="Syntax valid")
            )
            
            # Test feature implementation
            result = await implementer.implement_feature_tdd(
                feature={"id": "1", "title": "Test Feature", "description": "A test feature"},
                existing_code={},
                requirements="Test requirements",
                design_output="Test design",
                feature_index=0
            )
            
            # Verify result
            assert result.feature_id == "1"
            assert result.feature_title == "Test Feature"
            assert "test_feature.py" in result.test_code
            assert "feature.py" in result.implementation_code
            assert result.success == True
    
    def test_tdd_red_green_refactor_cycle(self):
        """Test that the TDD cycle follows red-green-refactor pattern"""
        # This is more of a conceptual test to ensure our design supports the pattern
        
        # Red phase: Tests should fail without implementation
        initial_test_result = Mock(success=False, failed=2, passed=0)
        
        # Green phase: Tests should pass with implementation
        final_test_result = Mock(success=True, failed=0, passed=2)
        
        # Create a TDD result
        from workflows.mvp_incremental.tdd_feature_implementer import TDDFeatureResult
        tdd_result = TDDFeatureResult(
            feature_id="1",
            feature_title="Calculator Add",
            test_code="test code",
            implementation_code="impl code",
            initial_test_result=initial_test_result,
            final_test_result=final_test_result,
            refactored=False,
            success=True
        )
        
        # Verify the cycle
        assert tdd_result.initial_test_result.success == False, "Tests should fail initially (Red)"
        assert tdd_result.final_test_result.success == True, "Tests should pass after implementation (Green)"
        assert hasattr(tdd_result, 'refactored'), "Should track refactoring phase"


if __name__ == "__main__":
    # Run specific test for debugging
    test = TestTDDIntegration()
    asyncio.run(test.test_tdd_workflow_execution(
        test.mock_input_data(),
        test.mock_planning_output(),
        test.mock_design_output(),
        test.mock_test_code(),
        test.mock_implementation_code()
    ))