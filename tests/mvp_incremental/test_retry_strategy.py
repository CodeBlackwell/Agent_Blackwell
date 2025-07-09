"""
Test TDD-Driven Retry Strategy for MVP Incremental Workflow

Tests the enhanced retry strategy with test-driven context and failure tracking.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import List, Dict

from workflows.mvp_incremental.retry_strategy import (
    RetryStrategy, 
    RetryConfig, 
    TestProgressionTracker,
    TestFailureContext
)
from workflows.mvp_incremental.error_analyzer import ErrorCategory


class TestRetryDecisions:
    """Test retry decision logic"""
    
    def test_should_retry_with_retries_remaining(self):
        """Test that retry is allowed when under max retries"""
        strategy = RetryStrategy()
        config = RetryConfig(max_retries=3)
        
        # Syntax and runtime errors should retry multiple times
        with patch.object(strategy.error_analyzer, 'analyze_error') as mock_analyze:
            # Syntax error - should retry multiple times
            mock_analyze.return_value = Mock(category=ErrorCategory.SYNTAX)
            assert strategy.should_retry("SyntaxError: invalid syntax", 0, config) == True
            assert strategy.should_retry("SyntaxError: invalid syntax", 1, config) == True
            assert strategy.should_retry("SyntaxError: invalid syntax", 2, config) == True
            
            # Runtime error - should retry multiple times  
            mock_analyze.return_value = Mock(category=ErrorCategory.RUNTIME)
            assert strategy.should_retry("RuntimeError: test failed", 0, config) == True
            assert strategy.should_retry("RuntimeError: test failed", 1, config) == True
            
        # Should not retry after max retries
        assert strategy.should_retry("AssertionError", 3, config) == False
    
    def test_should_not_retry_without_error(self):
        """Test that retry is not attempted without an error"""
        strategy = RetryStrategy()
        config = RetryConfig(max_retries=3)
        
        assert strategy.should_retry(None, 0, config) == False
        assert strategy.should_retry("", 0, config) == False
    
    def test_should_not_retry_non_retryable_errors(self):
        """Test that certain errors are not retried"""
        strategy = RetryStrategy()
        config = RetryConfig(max_retries=3)
        
        # Permission errors
        assert strategy.should_retry("PermissionError: permission denied", 0, config) == False
        
        # System errors
        assert strategy.should_retry("OSError: disk full", 0, config) == False
        
        # Timeout errors
        assert strategy.should_retry("TimeoutError: execution timeout", 0, config) == False
        
        # Memory errors
        assert strategy.should_retry("MemoryError: out of memory", 0, config) == False
        
        # Recursion errors
        assert strategy.should_retry("RecursionError: maximum recursion depth exceeded", 0, config) == False
    
    def test_should_not_retry_import_errors(self):
        """Test that import errors are not retried (usually missing dependencies)"""
        strategy = RetryStrategy()
        config = RetryConfig(max_retries=3)
        
        with patch.object(strategy.error_analyzer, 'analyze_error') as mock_analyze:
            mock_analyze.return_value = Mock(category=ErrorCategory.IMPORT)
            
            assert strategy.should_retry("ImportError: No module named 'missing'", 0, config) == False
    
    def test_conservative_retry_for_validation_errors(self):
        """Test that validation errors have more conservative retry logic"""
        strategy = RetryStrategy()
        config = RetryConfig(max_retries=3)
        
        with patch.object(strategy.error_analyzer, 'analyze_error') as mock_analyze:
            mock_analyze.return_value = Mock(category=ErrorCategory.VALIDATION)
            
            # Should retry once for validation errors
            assert strategy.should_retry("ValidationError: test failed", 0, config) == True
            assert strategy.should_retry("ValidationError: test failed", 1, config) == False


class TestErrorContextExtraction:
    """Test error context extraction with TDD enhancements"""
    
    def test_extract_context_with_test_failures(self):
        """Test extracting context with test failure contexts"""
        strategy = RetryStrategy()
        
        test_failures = [
            TestFailureContext(
                test_file="test_calculator.py",
                test_name="test_add",
                failure_type="assertion",
                failure_message="assert 0 == 5",
                expected_value="5",
                actual_value="0"
            ),
            TestFailureContext(
                test_file="test_calculator.py",
                test_name="test_subtract",
                failure_type="import_error",
                failure_message="No module named 'calculator'",
                missing_component="calculator"
            )
        ]
        
        context = strategy.extract_error_context("", test_failures)
        
        assert context["test_failure_count"] == "2"
        assert context["primary_failure_type"] == "assertion"
        assert "test_add: assert 0 == 5" in context["error_message"]
        assert "test_subtract: No module named 'calculator'" in context["error_message"]
    
    def test_extract_context_without_test_failures(self):
        """Test extracting context from validation output only"""
        strategy = RetryStrategy()
        
        validation_output = """
        VALIDATION FAILED
        DETAILS:
        SyntaxError: invalid syntax
        File "calculator.py", line 5
        """
        
        context = strategy.extract_error_context(validation_output)
        
        assert context["error_type"] == "SyntaxError"
        assert context["error_message"] == "invalid syntax"
        assert context["error_file"] == "calculator.py"
        assert context["error_line"] == "5"
    
    def test_extract_context_combined(self):
        """Test extracting context from both test failures and validation output"""
        strategy = RetryStrategy()
        
        test_failures = [
            TestFailureContext(
                test_file="test_calc.py",
                test_name="test_multiply",
                failure_type="name_error",
                failure_message="name 'multiply' is not defined",
                missing_component="multiply"
            )
        ]
        
        validation_output = """
        DETAILS:
        NameError: name 'divide' is not defined
        """
        
        context = strategy.extract_error_context(validation_output, test_failures)
        
        # Test failure context should take precedence
        assert context["test_failure_count"] == "1"
        assert "test_multiply" in context["error_message"]
        assert context["recovery_hint"] == "Define missing names: multiply"


class TestFixHintGeneration:
    """Test generation of test-specific fix hints"""
    
    def test_generate_import_error_hints(self):
        """Test hints for import errors"""
        strategy = RetryStrategy()
        
        failures = [
            TestFailureContext(
                test_file="test_app.py",
                test_name="test_import",
                failure_type="import_error",
                failure_message="No module named 'app'",
                missing_component="app"
            ),
            TestFailureContext(
                test_file="test_utils.py",
                test_name="test_helper",
                failure_type="import_error",
                failure_message="cannot import name 'helper'",
                missing_component="helper"
            )
        ]
        
        hints = strategy.generate_test_specific_hints(failures)
        
        # Check that we get a hint about creating missing modules
        assert any("Create missing modules/files:" in hint for hint in hints)
        # Check that both modules are mentioned (order may vary due to set)
        modules_hint = next(hint for hint in hints if "Create missing modules/files:" in hint)
        assert "app" in modules_hint
        assert "helper" in modules_hint
    
    def test_generate_assertion_hints(self):
        """Test hints for assertion errors"""
        strategy = RetryStrategy()
        
        failures = [
            TestFailureContext(
                test_file="test_math.py",
                test_name="test_add",
                failure_type="assertion",
                failure_message="assert 0 == 10",
                expected_value="10",
                actual_value="0"
            ),
            TestFailureContext(
                test_file="test_math.py",
                test_name="test_multiply",
                failure_type="assertion", 
                failure_message="assert None is not None"
            )
        ]
        
        hints = strategy.generate_test_specific_hints(failures)
        
        assert any("Fix test_add: Expected '10' but got '0'" in hint for hint in hints)
        assert any("Fix assertion in test_multiply" in hint for hint in hints)
    
    def test_generate_attribute_hints(self):
        """Test hints for attribute errors"""
        strategy = RetryStrategy()
        
        failures = [
            TestFailureContext(
                test_file="test_class.py",
                test_name="test_method",
                failure_type="attribute_error",
                failure_message="'Calculator' object has no attribute 'divide'",
                missing_component="Calculator.divide"
            )
        ]
        
        hints = strategy.generate_test_specific_hints(failures)
        
        assert any("Add method/attribute 'divide' to Calculator" in hint for hint in hints)
    
    def test_generate_name_error_hints(self):
        """Test hints for name errors"""
        strategy = RetryStrategy()
        
        failures = [
            TestFailureContext(
                test_file="test_funcs.py",
                test_name="test_process",
                failure_type="name_error",
                failure_message="name 'process_data' is not defined",
                missing_component="process_data"
            ),
            TestFailureContext(
                test_file="test_funcs.py",
                test_name="test_validate",
                failure_type="name_error",
                failure_message="name 'validate_input' is not defined",
                missing_component="validate_input"
            )
        ]
        
        hints = strategy.generate_test_specific_hints(failures)
        
        # Check that we get a hint about defining missing names
        assert any("Define missing names:" in hint for hint in hints)
        # Check that both names are mentioned (order may vary due to set)
        names_hint = next(hint for hint in hints if "Define missing names:" in hint)
        assert "process_data" in names_hint
        assert "validate_input" in names_hint
    
    def test_max_hints_limit(self):
        """Test that hint generation respects max_hints parameter"""
        strategy = RetryStrategy()
        
        # Create many failures
        failures = [
            TestFailureContext(
                test_file=f"test_{i}.py",
                test_name=f"test_{i}",
                failure_type="assertion",
                failure_message=f"assert {i} == {i+1}",
                expected_value=str(i+1),
                actual_value=str(i)
            )
            for i in range(10)
        ]
        
        hints = strategy.generate_test_specific_hints(failures, max_hints=3)
        
        assert len(hints) <= 3


class TestProgressionTracking:
    """Test tracking of test pass/fail progression across retries"""
    
    def test_track_initial_failures(self):
        """Test tracking failures on first attempt"""
        strategy = RetryStrategy()
        
        failures = [
            TestFailureContext(
                test_file="test_app.py",
                test_name="test_one",
                failure_type="assertion",
                failure_message="failed"
            ),
            TestFailureContext(
                test_file="test_app.py",
                test_name="test_two",
                failure_type="assertion",
                failure_message="failed"
            )
        ]
        
        tracker = strategy.track_test_progression("feature1", failures, 0)
        
        assert len(tracker.failing_tests) == 2
        assert len(tracker.passed_tests) == 0
        assert len(tracker.persistent_failures) == 0
        assert tracker.attempt_history[0]["failing_count"] == 2
    
    def test_track_test_improvements(self):
        """Test tracking when some tests start passing"""
        strategy = RetryStrategy()
        
        # First attempt - 3 failures
        failures1 = [
            TestFailureContext(test_file="test.py", test_name="test_a", failure_type="assertion", failure_message=""),
            TestFailureContext(test_file="test.py", test_name="test_b", failure_type="assertion", failure_message=""),
            TestFailureContext(test_file="test.py", test_name="test_c", failure_type="assertion", failure_message="")
        ]
        
        strategy.track_test_progression("feature1", failures1, 0)
        
        # Second attempt - only 2 failures (test_a passes)
        failures2 = [
            TestFailureContext(test_file="test.py", test_name="test_b", failure_type="assertion", failure_message=""),
            TestFailureContext(test_file="test.py", test_name="test_c", failure_type="assertion", failure_message="")
        ]
        
        tracker = strategy.track_test_progression("feature1", failures2, 1)
        
        assert len(tracker.failing_tests) == 2
        assert len(tracker.passed_tests) == 1
        assert "test.py::test_a" in tracker.passed_tests
        assert len(tracker.persistent_failures) == 2
    
    def test_track_all_tests_passing(self):
        """Test tracking when all tests eventually pass"""
        strategy = RetryStrategy()
        
        # First attempt - failures
        failures1 = [
            TestFailureContext(test_file="test.py", test_name="test_x", failure_type="assertion", failure_message="")
        ]
        
        strategy.track_test_progression("feature1", failures1, 0)
        
        # Second attempt - no failures
        tracker = strategy.track_test_progression("feature1", [], 1)
        
        assert len(tracker.failing_tests) == 0
        assert len(tracker.passed_tests) == 1
        assert tracker.attempt_history[1]["failing_count"] == 0
        assert tracker.attempt_history[1]["passed_count"] == 1


class TestRetryPromptGeneration:
    """Test generation of enhanced retry prompts"""
    
    def test_basic_retry_prompt(self):
        """Test basic retry prompt without test context"""
        strategy = RetryStrategy()
        config = RetryConfig(include_test_context=False)
        
        prompt = strategy.create_retry_prompt(
            original_context="",
            feature={"title": "Calculator", "description": "Basic math operations"},
            validation_output="SyntaxError: invalid syntax",
            error_context={"error_type": "SyntaxError", "error_message": "invalid syntax", "full_error": ""},
            retry_count=1,
            accumulated_code={"calculator.py": "def add(a, b)\n    return a + b"},
            config=config
        )
        
        assert "RETRY ATTEMPT: 1" in prompt
        assert "Calculator" in prompt
        assert "SyntaxError" in prompt
        assert "calculator.py" in prompt
    
    def test_retry_prompt_with_test_context(self):
        """Test retry prompt with test failure context"""
        strategy = RetryStrategy()
        config = RetryConfig(include_test_context=True)
        
        test_failures = [
            TestFailureContext(
                test_file="test_calc.py",
                test_name="test_add",
                failure_type="assertion",
                failure_message="assert 0 == 5",
                expected_value="5",
                actual_value="0"
            )
        ]
        
        prompt = strategy.create_retry_prompt(
            original_context="",
            feature={"id": "calc1", "title": "Calculator", "description": "Math operations"},
            validation_output="Tests failed",
            error_context={"error_type": "", "error_message": "", "full_error": ""},
            retry_count=1,
            accumulated_code={"calculator.py": "def add(a, b):\n    return 0"},
            test_failure_contexts=test_failures,
            config=config
        )
        
        assert "FAILING TESTS (TDD):" in prompt
        assert "test_add in test_calc.py" in prompt
        assert "Expected: 5" in prompt
        assert "Actual: 0" in prompt
        assert "TEST-DRIVEN HINTS:" in prompt
    
    def test_retry_prompt_with_progression(self):
        """Test retry prompt showing test progression"""
        strategy = RetryStrategy()
        config = RetryConfig(include_test_context=True, track_test_progression=True)
        
        # Simulate first attempt with 3 failures
        failures1 = [
            TestFailureContext(test_file="test.py", test_name=f"test_{i}", failure_type="assertion", failure_message="")
            for i in range(3)
        ]
        strategy.track_test_progression("feature1", failures1, 0)
        
        # Second attempt with only 1 failure
        failures2 = [
            TestFailureContext(test_file="test.py", test_name="test_0", failure_type="assertion", failure_message="")
        ]
        
        prompt = strategy.create_retry_prompt(
            original_context="",
            feature={"id": "feature1", "title": "Feature", "description": "Description"},
            validation_output="",
            error_context={"error_type": "", "error_message": "", "full_error": ""},
            retry_count=1,
            accumulated_code={},
            test_failure_contexts=failures2,
            config=config
        )
        
        # Check for progression info
        assert "TEST PROGRESSION:" in prompt
        assert "Tests that started passing: 2" in prompt
        assert "Tests still failing: 1" in prompt
    
    def test_retry_prompt_format(self):
        """Test that retry prompt has correct format and sections"""
        strategy = RetryStrategy()
        
        prompt = strategy.create_retry_prompt(
            original_context="",
            feature={"title": "Test Feature", "description": "Test description"},
            validation_output="Error details",
            error_context={
                "error_type": "TypeError",
                "error_message": "unsupported operand",
                "error_category": "runtime",
                "recovery_hint": "Check types",
                "full_error": "Full error trace"
            },
            retry_count=2,
            accumulated_code={"main.py": "code here"}
        )
        
        # Check all required sections are present
        assert "RETRY ATTEMPT: 2" in prompt
        assert "FEATURE TO IMPLEMENT:" in prompt
        assert "VALIDATION FAILED WITH ERROR:" in prompt
        assert "ERROR SUMMARY:" in prompt
        assert "RECOVERY HINT:" in prompt
        assert "CURRENT CODE THAT NEEDS FIXING:" in prompt
        assert "CRITICAL INSTRUCTIONS FOR RETRY:" in prompt
        assert "OUTPUT FORMAT:" in prompt


class TestIntegration:
    """Test integration with other components"""
    
    def test_retry_strategy_initialization(self):
        """Test that retry strategy initializes correctly"""
        strategy = RetryStrategy()
        
        assert hasattr(strategy, 'error_analyzer')
        assert hasattr(strategy, 'test_progression')
        assert isinstance(strategy.test_progression, dict)
    
    def test_multiple_features_tracking(self):
        """Test tracking progression for multiple features"""
        strategy = RetryStrategy()
        
        # Track feature 1
        failures1 = [TestFailureContext(test_file="test1.py", test_name="test", failure_type="assertion", failure_message="")]
        strategy.track_test_progression("feature1", failures1, 0)
        
        # Track feature 2
        failures2 = [TestFailureContext(test_file="test2.py", test_name="test", failure_type="assertion", failure_message="")]
        strategy.track_test_progression("feature2", failures2, 0)
        
        assert "feature1" in strategy.test_progression
        assert "feature2" in strategy.test_progression
        assert len(strategy.test_progression["feature1"].failing_tests) == 1
        assert len(strategy.test_progression["feature2"].failing_tests) == 1
    
    def test_config_defaults(self):
        """Test that RetryConfig has sensible defaults"""
        config = RetryConfig()
        
        assert config.max_retries == 2
        assert config.extract_error_context == True
        assert config.modify_prompt_on_retry == True
        assert config.include_test_context == True
        assert config.track_test_progression == True
        assert config.max_test_specific_hints == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])