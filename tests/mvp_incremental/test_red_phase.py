"""
Test suite for RED Phase Orchestrator

Tests the RED phase enforcement including:
- Test failure validation
- Failure context extraction
- Implementation context preparation
- Phase transition blocking
- Error handling
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any
import asyncio

from workflows.mvp_incremental.red_phase import (
    RedPhaseOrchestrator,
    TestFailureContext,
    RedPhaseError
)
from workflows.mvp_incremental.tdd_phase_tracker import TDDPhase, TDDPhaseTracker
from workflows.mvp_incremental.test_execution import TestExecutor
from workflows.mvp_incremental.testable_feature_parser import TestableFeature


class TestRedPhaseOrchestrator:
    """Test suite for RedPhaseOrchestrator"""
    
    @pytest.fixture
    def mock_test_executor(self):
        """Create mock test executor"""
        executor = Mock(spec=TestExecutor)
        executor.run_tests = AsyncMock()
        return executor
    
    @pytest.fixture
    def mock_phase_tracker(self):
        """Create mock phase tracker"""
        tracker = Mock()
        tracker.get_current_phase = Mock(return_value=TDDPhase.RED)
        # Add a simple timestamp method
        tracker._get_timestamp = Mock(return_value="2024-01-01T12:00:00")
        return tracker
    
    @pytest.fixture
    def sample_feature(self):
        """Create sample testable feature"""
        from workflows.mvp_incremental.testable_feature_parser import TestCriteria
        
        return TestableFeature(
            id="calculator_addition",
            title="Calculator Addition",
            description="Add two numbers",
            test_criteria=TestCriteria(
                description="Test calculator addition functionality",
                input_examples=[{"a": 2, "b": 3}],
                expected_outputs=[5],
                edge_cases=["negative numbers", "zero"],
                error_conditions=["non-numeric input"]
            ),
            dependencies=[],
            test_files=["test_add_positive_numbers.py", "test_add_negative_numbers.py"],
            tdd_phase=TDDPhase.RED
        )
    
    @pytest.fixture
    def orchestrator(self, mock_test_executor, mock_phase_tracker):
        """Create RED phase orchestrator instance"""
        return RedPhaseOrchestrator(mock_test_executor, mock_phase_tracker)
    
    @pytest.mark.asyncio
    async def test_validate_red_phase_success(self, orchestrator, sample_feature, mock_test_executor):
        """Test successful RED phase validation when tests fail as expected"""
        # Configure test executor to return failed tests
        mock_test_executor.run_tests.return_value = {
            "status": "failed",
            "output": """
FAILED test_calculator.py::test_add_positive_numbers - AssertionError: assert 0 == 5
FAILED test_calculator.py::test_add_negative_numbers - AssertionError: assert 0 == -1
            """,
            "tests_run": 2,
            "tests_failed": 2
        }
        
        is_valid, failure_contexts = await orchestrator.validate_red_phase(
            sample_feature,
            "test_calculator.py",
            "/project/root"
        )
        
        assert is_valid is True
        assert len(failure_contexts) == 2
        assert failure_contexts[0].test_name == "test_add_positive_numbers"
        assert failure_contexts[0].failure_type == "assertion"
        
        # Verify test executor was called with expect_failure=True
        mock_test_executor.run_tests.assert_called_once_with(
            test_file="test_calculator.py",
            working_dir="/project/root",
            expect_failure=True
        )
    
    @pytest.mark.asyncio
    async def test_validate_red_phase_unexpected_pass(self, orchestrator, sample_feature, mock_test_executor):
        """Test RED phase validation fails when tests pass unexpectedly"""
        # Configure test executor to return passing tests
        mock_test_executor.run_tests.return_value = {
            "status": "passed",
            "output": "All tests passed!",
            "tests_run": 2,
            "tests_failed": 0
        }
        
        with pytest.raises(RedPhaseError) as exc_info:
            await orchestrator.validate_red_phase(
                sample_feature,
                "test_calculator.py",
                "/project/root"
            )
        
        assert "passed unexpectedly in RED phase" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_validate_red_phase_wrong_phase(self, orchestrator, sample_feature, mock_phase_tracker):
        """Test RED phase validation fails when not in RED phase"""
        # Set phase to YELLOW
        mock_phase_tracker.get_current_phase.return_value = TDDPhase.YELLOW
        
        with pytest.raises(RedPhaseError) as exc_info:
            await orchestrator.validate_red_phase(
                sample_feature,
                "test_calculator.py",
                "/project/root"
            )
        
        assert "not in RED phase" in str(exc_info.value)
        assert "YELLOW" in str(exc_info.value)
    
    def test_extract_failure_context_assertions(self, orchestrator):
        """Test extraction of assertion failure contexts"""
        test_result = {
            "status": "failed",
            "output": """
FAILED test_calculator.py::test_add - AssertionError: assert 0 == 5
FAILED test_calculator.py::test_subtract - AssertionError: assert 10 == 3
            """
        }
        
        contexts = orchestrator.extract_failure_context(test_result)
        
        assert len(contexts) == 2
        assert contexts[0].test_file == "test_calculator.py"
        assert contexts[0].test_name == "test_add"
        assert contexts[0].failure_type == "assertion"
        assert contexts[0].actual_value == "0"
        assert contexts[0].expected_value == "5"
    
    def test_extract_failure_context_import_errors(self, orchestrator):
        """Test extraction of import error contexts"""
        test_result = {
            "status": "failed",
            "output": """
ImportError: No module named 'calculator'
ModuleNotFoundError: No module named 'utils.math_helpers'
            """
        }
        
        contexts = orchestrator.extract_failure_context(test_result)
        
        assert len(contexts) == 2
        assert contexts[0].failure_type == "import_error"
        assert contexts[0].missing_component == "calculator"
        assert contexts[1].missing_component == "utils.math_helpers"
    
    def test_extract_failure_context_attribute_errors(self, orchestrator):
        """Test extraction of attribute error contexts"""
        test_result = {
            "status": "failed",
            "output": """
FAILED test_calc.py::test_method - AttributeError: 'Calculator' object has no attribute 'multiply'
            """
        }
        
        contexts = orchestrator.extract_failure_context(test_result)
        
        assert len(contexts) == 1
        assert contexts[0].failure_type == "attribute_error"
        assert contexts[0].missing_component == "Calculator.multiply"
    
    def test_extract_failure_context_name_errors(self, orchestrator):
        """Test extraction of name error contexts"""
        test_result = {
            "status": "failed",
            "output": """
FAILED test_func.py::test_function - NameError: name 'process_data' is not defined
            """
        }
        
        contexts = orchestrator.extract_failure_context(test_result)
        
        assert len(contexts) == 1
        assert contexts[0].failure_type == "name_error"
        assert contexts[0].missing_component == "process_data"
    
    def test_prepare_implementation_context(self, orchestrator, sample_feature):
        """Test preparation of implementation context from failures"""
        failure_contexts = [
            TestFailureContext(
                test_file="test_calc.py",
                test_name="test_add",
                failure_type="assertion",
                failure_message="assert 0 == 5",
                expected_value="5",
                actual_value="0"
            ),
            TestFailureContext(
                test_file="test_calc.py",
                test_name="import",
                failure_type="import_error",
                failure_message="No module named 'calculator'",
                missing_component="calculator"
            ),
            TestFailureContext(
                test_file="test_calc.py",
                test_name="test_multiply",
                failure_type="attribute_error",
                failure_message="no attribute 'multiply'",
                missing_component="Calculator.multiply"
            )
        ]
        
        context = orchestrator.prepare_implementation_context(sample_feature, failure_contexts)
        
        assert context["feature"]["id"] == "calculator_addition"
        assert context["failure_summary"]["total_failures"] == 3
        assert set(context["failure_summary"]["failure_types"]) == {
            "assertion", "import_error", "attribute_error"
        }
        assert set(context["missing_components"]) == {"calculator", "Calculator.multiply"}
        assert len(context["implementation_hints"]) >= 2
        assert len(context["detailed_failures"]) == 3
    
    @pytest.mark.asyncio
    async def test_enforce_red_phase_success(self, orchestrator, sample_feature, mock_test_executor):
        """Test successful RED phase enforcement"""
        # Configure test executor
        mock_test_executor.run_tests.return_value = {
            "status": "failed",
            "output": "FAILED test_calc.py::test_add - ImportError: No module named 'calculator'",
            "tests_run": 1,
            "tests_failed": 1
        }
        
        result = await orchestrator.enforce_red_phase(
            sample_feature,
            "test_calc.py",
            "/project/root"
        )
        
        assert result["red_phase_validated"] is True
        assert "validation_timestamp" in result
        assert result["failure_summary"]["total_failures"] == 1
        assert "calculator" in result["missing_components"]
    
    @pytest.mark.asyncio
    async def test_enforce_red_phase_validation_error(self, orchestrator, sample_feature, mock_test_executor):
        """Test RED phase enforcement handles validation errors"""
        # Configure test executor to return unexpected pass
        mock_test_executor.run_tests.return_value = {
            "status": "passed",
            "output": "All tests passed!",
            "tests_run": 1,
            "tests_failed": 0
        }
        
        with pytest.raises(RedPhaseError) as exc_info:
            await orchestrator.enforce_red_phase(
                sample_feature,
                "test_calc.py",
                "/project/root"
            )
        
        assert "RED phase enforcement failed" in str(exc_info.value)
    
    def test_test_failure_context_to_dict(self):
        """Test TestFailureContext serialization"""
        context = TestFailureContext(
            test_file="test.py",
            test_name="test_func",
            failure_type="assertion",
            failure_message="Failed",
            expected_value="1",
            actual_value="2",
            missing_component="func",
            line_number=42
        )
        
        result = context.to_dict()
        
        assert result["test_file"] == "test.py"
        assert result["test_name"] == "test_func"
        assert result["failure_type"] == "assertion"
        assert result["failure_message"] == "Failed"
        assert result["expected_value"] == "1"
        assert result["actual_value"] == "2"
        assert result["missing_component"] == "func"
        assert result["line_number"] == 42
    
    def test_parse_failure_details_complex_assertions(self, orchestrator):
        """Test parsing complex assertion patterns"""
        test_output = """
test_math.py", line 15
FAILED test_math.py::test_complex - AssertionError: assert (1, 2) == (3, 4)
        """
        
        context = orchestrator._parse_failure_details(
            "test_math.py",
            "test_complex",
            "AssertionError: assert (1, 2) == (3, 4)",
            test_output
        )
        
        assert context.failure_type == "assertion"
        assert context.actual_value == "(1, 2)"
        assert context.expected_value == "(3, 4)"
        assert context.line_number == 15
    
    def test_extract_failure_context_no_failures(self, orchestrator):
        """Test handling when no failure context can be extracted"""
        test_result = {
            "status": "failed",
            "output": "Some unexpected output format"
        }
        
        contexts = orchestrator.extract_failure_context(test_result)
        
        assert contexts == []
    
    @pytest.mark.asyncio
    async def test_validate_red_phase_no_context_extracted(self, orchestrator, sample_feature, mock_test_executor):
        """Test RED phase validation when no failure context can be extracted"""
        # Configure test executor with unparseable output
        mock_test_executor.run_tests.return_value = {
            "status": "failed",
            "output": "Unexpected test output format",
            "tests_run": 1,
            "tests_failed": 1
        }
        
        with pytest.raises(RedPhaseError) as exc_info:
            await orchestrator.validate_red_phase(
                sample_feature,
                "test_calc.py",
                "/project/root"
            )
        
        assert "no failure context could be extracted" in str(exc_info.value)