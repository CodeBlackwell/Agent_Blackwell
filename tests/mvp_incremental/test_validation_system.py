"""
Unit tests for the granular validation system
"""
import pytest
from datetime import datetime
from workflows.incremental.validation_system import (
    ValidationLevel, TestGranularity, ValidationCheckpoint,
    TestProgress, FeatureValidationProgress, GranularValidator
)


class TestValidationCheckpoint:
    """Test ValidationCheckpoint functionality"""
    
    def test_checkpoint_creation(self):
        """Test creating a validation checkpoint"""
        checkpoint = ValidationCheckpoint(
            level=ValidationLevel.SYNTAX,
            passed=True,
            details="Syntax validation passed"
        )
        
        assert checkpoint.level == ValidationLevel.SYNTAX
        assert checkpoint.passed is True
        assert checkpoint.details == "Syntax validation passed"
        assert isinstance(checkpoint.timestamp, datetime)
        assert checkpoint.sub_checks == []
    
    def test_checkpoint_progress_no_subchecks(self):
        """Test progress calculation without sub-checks"""
        checkpoint = ValidationCheckpoint(
            level=ValidationLevel.SYNTAX,
            passed=True,
            details="Test"
        )
        assert checkpoint.get_progress_percentage() == 100.0
        
        checkpoint.passed = False
        assert checkpoint.get_progress_percentage() == 0.0
    
    def test_checkpoint_progress_with_subchecks(self):
        """Test progress calculation with sub-checks"""
        sub_checks = [
            ("Check 1", True),
            ("Check 2", True),
            ("Check 3", False),
            ("Check 4", True)
        ]
        checkpoint = ValidationCheckpoint(
            level=ValidationLevel.IMPORTS,
            passed=False,
            details="Some imports failed",
            sub_checks=sub_checks
        )
        
        assert checkpoint.get_progress_percentage() == 75.0


class TestTestProgress:
    """Test TestProgress tracking functionality"""
    
    def test_test_progress_initialization(self):
        """Test TestProgress initialization"""
        progress = TestProgress(test_file="test_example.py")
        
        assert progress.test_file == "test_example.py"
        assert progress.total_tests == 0
        assert progress.executed_tests == 0
        assert progress.passed_tests == 0
        assert progress.failed_tests == 0
        assert progress.skipped_tests == 0
        assert progress.test_details == {}
    
    def test_add_test_result_passed(self):
        """Test adding a passed test result"""
        progress = TestProgress(test_file="test_example.py")
        progress.add_test_result("test_foo", passed=True, duration=0.5)
        
        assert progress.executed_tests == 1
        assert progress.passed_tests == 1
        assert progress.failed_tests == 0
        assert "test_foo" in progress.test_details
        assert progress.test_details["test_foo"]["passed"] is True
        assert progress.test_details["test_foo"]["duration"] == 0.5
        assert progress.test_details["test_foo"]["error"] is None
    
    def test_add_test_result_failed(self):
        """Test adding a failed test result"""
        progress = TestProgress(test_file="test_example.py")
        progress.add_test_result("test_bar", passed=False, duration=0.3, error="AssertionError")
        
        assert progress.executed_tests == 1
        assert progress.passed_tests == 0
        assert progress.failed_tests == 1
        assert "test_bar" in progress.test_details
        assert progress.test_details["test_bar"]["passed"] is False
        assert progress.test_details["test_bar"]["error"] == "AssertionError"
    
    def test_pass_rate_calculation(self):
        """Test pass rate calculation"""
        progress = TestProgress(test_file="test_example.py")
        
        # No tests executed
        assert progress.get_pass_rate() == 0.0
        
        # Add some test results
        progress.add_test_result("test_1", passed=True)
        progress.add_test_result("test_2", passed=True)
        progress.add_test_result("test_3", passed=False)
        progress.add_test_result("test_4", passed=True)
        
        assert progress.get_pass_rate() == 75.0
    
    def test_execution_rate_calculation(self):
        """Test execution rate calculation"""
        progress = TestProgress(test_file="test_example.py")
        progress.total_tests = 10
        
        assert progress.get_execution_rate() == 0.0
        
        progress.add_test_result("test_1", passed=True)
        progress.add_test_result("test_2", passed=False)
        
        assert progress.get_execution_rate() == 20.0


class TestFeatureValidationProgress:
    """Test FeatureValidationProgress functionality"""
    
    def test_feature_validation_initialization(self):
        """Test FeatureValidationProgress initialization"""
        progress = FeatureValidationProgress(feature_id="feature_1")
        
        assert progress.feature_id == "feature_1"
        assert progress.checkpoints == []
        assert progress.test_progress == {}
        assert progress.partial_implementations == {}
        assert progress.integration_status == {}
    
    def test_add_checkpoint(self):
        """Test adding checkpoints"""
        progress = FeatureValidationProgress(feature_id="feature_1")
        
        progress.add_checkpoint(
            ValidationLevel.SYNTAX,
            passed=True,
            details="Syntax OK",
            sub_checks=[("Basic parsing", True)]
        )
        
        assert len(progress.checkpoints) == 1
        assert progress.checkpoints[0].level == ValidationLevel.SYNTAX
        assert progress.checkpoints[0].passed is True
        assert progress.checkpoints[0].sub_checks == [("Basic parsing", True)]
    
    def test_overall_progress_calculation(self):
        """Test overall progress calculation with weighted checkpoints"""
        progress = FeatureValidationProgress(feature_id="feature_1")
        
        # Add checkpoints with different levels
        progress.add_checkpoint(ValidationLevel.SYNTAX, True, "OK", [("Parse", True)])
        progress.add_checkpoint(ValidationLevel.IMPORTS, True, "OK", [("Import1", True), ("Import2", True)])
        progress.add_checkpoint(ValidationLevel.STRUCTURE, False, "Missing", [("Class1", True), ("Class2", False)])
        progress.add_checkpoint(ValidationLevel.FUNCTIONALITY, True, "OK", [("Func1", True)])
        progress.add_checkpoint(ValidationLevel.TESTS, False, "Failed", [("Test1", False), ("Test2", False)])
        
        # Calculate expected progress
        # SYNTAX: 0.1 * 100 = 10
        # IMPORTS: 0.1 * 100 = 10
        # STRUCTURE: 0.15 * 50 = 7.5
        # FUNCTIONALITY: 0.25 * 100 = 25
        # TESTS: 0.25 * 0 = 0
        # Total weight: 0.85
        # Expected: (10 + 10 + 7.5 + 25 + 0) / 0.85 ≈ 61.76
        
        overall = progress.get_overall_progress()
        assert 61 < overall < 62
    
    def test_blocking_issues_detection(self):
        """Test detection of blocking issues"""
        progress = FeatureValidationProgress(feature_id="feature_1")
        
        # No issues initially
        assert progress.get_blocking_issues() == []
        
        # Add syntax error
        progress.add_checkpoint(ValidationLevel.SYNTAX, False, "Syntax error")
        blocking = progress.get_blocking_issues()
        assert len(blocking) == 1
        assert "Syntax errors must be fixed" in blocking[0]
        
        # Add import error
        progress.add_checkpoint(ValidationLevel.IMPORTS, False, "Import error")
        blocking = progress.get_blocking_issues()
        assert len(blocking) == 2
        assert any("Import/dependency errors" in issue for issue in blocking)
        
        # Add critical test failures
        test_prog = TestProgress(test_file="test_critical.py")
        test_prog.total_tests = 10
        test_prog.passed_tests = 1
        test_prog.failed_tests = 9
        progress.test_progress["test_critical.py"] = test_prog
        
        blocking = progress.get_blocking_issues()
        assert len(blocking) == 3
        assert any("Critical test failures" in issue for issue in blocking)


class TestGranularValidator:
    """Test GranularValidator functionality"""
    
    @pytest.fixture
    def validator(self):
        """Create a validator instance"""
        return GranularValidator()
    
    def test_validate_syntax_valid(self, validator):
        """Test syntax validation with valid code"""
        code = """
def hello_world():
    '''Say hello'''
    print("Hello, World!")

class MyClass:
    def __init__(self):
        self.value = 42
"""
        checkpoint = validator.validate_syntax(code, "test.py")
        
        assert checkpoint.level == ValidationLevel.SYNTAX
        assert checkpoint.passed is True
        assert "Syntax validation passed" in checkpoint.details
        assert len(checkpoint.sub_checks) >= 2
        assert checkpoint.sub_checks[0] == ("Basic syntax parsing", True)
        assert checkpoint.sub_checks[1] == ("Contains code structure", True)
    
    def test_validate_syntax_invalid(self, validator):
        """Test syntax validation with invalid code"""
        code = """
def hello_world()  # Missing colon
    print("Hello")
"""
        checkpoint = validator.validate_syntax(code, "test.py")
        
        assert checkpoint.level == ValidationLevel.SYNTAX
        assert checkpoint.passed is False
        assert "Syntax error" in checkpoint.details
        assert checkpoint.sub_checks == [("Basic syntax parsing", False)]
    
    def test_validate_imports_valid(self, validator):
        """Test import validation with valid imports"""
        code = """
import os
import sys
from json import dumps
from mymodule import helper
"""
        available_modules = {"mymodule"}
        checkpoint = validator.validate_imports(code, available_modules)
        
        assert checkpoint.level == ValidationLevel.IMPORTS
        assert checkpoint.passed is True
        assert "All imports validated" in checkpoint.details
        assert len(checkpoint.sub_checks) == 4
    
    def test_validate_imports_missing(self, validator):
        """Test import validation with missing imports"""
        code = """
import os
import unknown_module
from another_unknown import something
"""
        available_modules = set()
        checkpoint = validator.validate_imports(code, available_modules)
        
        assert checkpoint.level == ValidationLevel.IMPORTS
        assert checkpoint.passed is False
        assert "Import issues" in checkpoint.details
        assert "unknown_module" in checkpoint.details
        assert "another_unknown" in checkpoint.details
    
    def test_validate_structure(self, validator):
        """Test structure validation"""
        code = """
def process_data(data):
    return data * 2

class DataProcessor:
    def __init__(self):
        self.data = []
    
    def add_data(self, item):
        self.data.append(item)
"""
        expected = ["process_data", "DataProcessor", "add_data"]
        checkpoint = validator.validate_structure(code, expected)
        
        assert checkpoint.level == ValidationLevel.STRUCTURE
        assert checkpoint.passed is True
        assert all(check[1] for check in checkpoint.sub_checks if check[0].startswith("Component"))
    
    def test_parse_test_output_pytest(self, validator):
        """Test parsing pytest output"""
        test_output = """
test_example.py::test_addition PASSED
test_example.py::test_subtraction FAILED
test_example.py::test_multiplication PASSED
test_another.py::test_division PASSED
test_another.py::test_modulo FAILED

================ 3 passed, 2 failed in 0.5s ================
"""
        results = validator.parse_test_output(test_output)
        
        assert len(results) == 2
        assert "test_example.py" in results
        assert "test_another.py" in results
        
        example_progress = results["test_example.py"]
        assert example_progress.total_tests == 3
        assert example_progress.passed_tests == 2
        assert example_progress.failed_tests == 1
    
    def test_create_validation_report(self, validator):
        """Test creating a comprehensive validation report"""
        code_files = {
            "main.py": """
def main():
    print("Hello")

if __name__ == "__main__":
    main()
""",
            "helper.py": """
def helper_function(x):
    return x * 2
"""
        }
        
        test_output = """
test_main.py::test_main PASSED
test_helper.py::test_helper_function PASSED
================ 2 passed in 0.1s ================
"""
        
        expected_components = {
            "main.py": ["main"],
            "helper.py": ["helper_function"]
        }
        
        report = validator.create_validation_report(
            feature_id="feature_1",
            code_files=code_files,
            test_output=test_output,
            expected_components=expected_components
        )
        
        assert report.feature_id == "feature_1"
        assert len(report.checkpoints) > 0
        assert len(report.test_progress) > 0
        assert report.get_overall_progress() > 0
    
    def test_get_improvement_suggestions(self, validator):
        """Test getting improvement suggestions"""
        # Create a failed validation report
        progress = FeatureValidationProgress(feature_id="feature_1")
        progress.add_checkpoint(ValidationLevel.SYNTAX, False, "Syntax error at line 5")
        progress.add_checkpoint(ValidationLevel.IMPORTS, False, "Missing module: requests")
        
        validator.validation_history["feature_1"].append(progress)
        
        suggestions = validator.get_improvement_suggestions("feature_1")
        
        assert len(suggestions) >= 2
        assert any("syntax errors" in s.lower() for s in suggestions)
        assert any("dependencies" in s.lower() for s in suggestions)
    
    def test_get_improvement_suggestions_test_failures(self, validator):
        """Test suggestions for test failures"""
        progress = FeatureValidationProgress(feature_id="feature_2")
        
        # Add test progress with low pass rate
        test_prog = TestProgress(test_file="test_failing.py")
        test_prog.total_tests = 10
        test_prog.passed_tests = 3
        test_prog.failed_tests = 7
        progress.test_progress["test_failing.py"] = test_prog
        
        progress.add_checkpoint(ValidationLevel.TESTS, False, "Tests failed")
        
        validator.validation_history["feature_2"].append(progress)
        
        suggestions = validator.get_improvement_suggestions("feature_2")
        
        assert any("test_failing.py" in s for s in suggestions)
        assert any("7 failures" in s for s in suggestions)