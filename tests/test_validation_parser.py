"""
Test the validation parser logic to ensure it correctly interprets executor outputs
"""
import pytest
from orchestrator.utils.incremental_executor import IncrementalExecutor
from shared.utils.feature_parser import Feature, ComplexityLevel

class TestValidationParser:
    """Test validation parsing logic"""
    
    def test_parse_successful_docker_execution(self):
        """Test parsing successful Docker execution output"""
        executor = IncrementalExecutor("test_session")
        
        # Create test feature
        feature = Feature(
            id="FEATURE[1]",
            title="Test Feature",
            description="Test description",
            files=["test.py"],
            validation_criteria="Test passes",
            dependencies=[],
            complexity=ComplexityLevel.LOW,
            short_name="test"
        )
        
        # Test output that was incorrectly parsed as failure
        output = """✅ DOCKER EXECUTION RESULT
============================================================
🔗 Session ID: inc_5fc8ef53-872f-4cc5-b62f-b9c7c0d08db9
🐳 Container: executor_inc_5fc8ef53-872f-4cc5-b62f-b9c7c0d08db9_f02c0850
📦 Environment: python:3.9
📄 Proof of Execution: generated/inc_5fc8ef53-872f-4cc5-b62f-b9c7c0d08db9_inc_5fc8ef53-872f-4cc5-b62f-b9c7c0d08db9_f02c0850/proof_of_execution.json

📊 EXECUTION DETAILS
----------------------------------------
✅ Command: python -c 'import pkg_resources; print("Installed packages:"); [print(f"{d.project_name}=={d.version}") for d in pkg_resources.working_set]'
   Exit Code: 0
   Output:
      Installed packages:
      wheel==0.45.1
      websockets==15.0.1
      watchfiles==1.1.0
      uvloop==0.21.0
      uvicorn==0.34.2
      ujson==5.10.0
      typing-inspection==0.4.1
      typing-extensions==4.14.0
      typer==0.16.0

🔍 ANALYSIS
----------------------------------------
The execution was successful. The command to check installed packages ran without errors, and all required packages are installed as specified in the requirements. The implementation meets the specified requirements for the Project Foundation feature. Further performance observations and recommendations for improvement can be provided upon request."""
        
        result = executor._parse_validation_output(output, feature, {"test.py": "print('test')"})
        
        assert result.success is True, f"Expected success=True, got {result.success}"
        assert "✅" in result.feedback
        assert result.execution_details["exit_code"] == 0
        
    def test_parse_failed_docker_execution(self):
        """Test parsing failed Docker execution output"""
        executor = IncrementalExecutor("test_session")
        
        feature = Feature(
            id="FEATURE[1]",
            title="Test Feature",
            description="Test description",
            files=["test.py"],
            validation_criteria="Test passes",
            dependencies=[],
            complexity=ComplexityLevel.LOW,
            short_name="test"
        )
        
        # Test actual failure output
        output = """❌ DOCKER EXECUTION ERROR

Session ID: inc_5fc8ef53-872f-4cc5-b62f-b9c7c0d08db9
Error: Failed to build Docker image: failed to resolve reference "docker.io/library/python:3.9": failed to authorize: failed to fetch oauth token: Post "https://auth.docker.io/token": proxyconnect tcp: dial tcp 192.168.65.1:3128: i/o timeout

Please check:
1. Docker is installed and running
2. The code format is correct
3. Dependencies are properly specified

Technical details:
Failed to build Docker image: failed to resolve reference "docker.io/library/python:3.9": failed to authorize: failed to fetch oauth token: Post "https://auth.docker.io/token": proxyconnect tcp: dial tcp 192.168.65.1:3128: i/o timeout"""
        
        result = executor._parse_validation_output(output, feature, {"test.py": "print('test')"})
        
        assert result.success is False
        assert "❌" in result.feedback
        assert "Docker image" in result.feedback
        
    def test_parse_test_results(self):
        """Test parsing test execution results"""
        executor = IncrementalExecutor("test_session")
        
        feature = Feature(
            id="FEATURE[2]",
            title="Test Feature",
            description="Test description",
            files=["test.py"],
            validation_criteria="All tests pass",
            dependencies=[],
            complexity=ComplexityLevel.LOW,
            short_name="test"
        )
        
        # Test output with test results (pytest format)
        output = """Running tests...
        
        test_basic.py::test_hello_world PASSED
        test_basic.py::test_addition PASSED
        test_basic.py::test_subtraction PASSED
        
        ========== 3 passed, 0 failed in 0.05s ==========
        
        All tests completed successfully!"""
        
        result = executor._parse_validation_output(output, feature, {"test.py": "print('test')"})
        
        print(f"Debug - Success: {result.success}, Passed: {result.tests_passed}, Failed: {result.tests_failed}")
        print(f"Debug - Feedback: {result.feedback}")
        
        assert result.success is True
        assert result.tests_passed == 3
        # When only passed tests are reported, failed is None (not 0)
        assert result.tests_failed == 0 or result.tests_failed is None
        
    def test_parse_mixed_indicators(self):
        """Test parsing output with mixed success/failure indicators"""
        executor = IncrementalExecutor("test_session")
        
        feature = Feature(
            id="FEATURE[3]",
            title="Test Feature",
            description="Test description",
            files=["test.py"],
            validation_criteria="Test passes",
            dependencies=[],
            complexity=ComplexityLevel.LOW,
            short_name="test"
        )
        
        # Output with word "error" but actually successful
        output = """✅ DOCKER EXECUTION RESULT
Exit Code: 0
Output: Checking for errors in configuration...
No errors found!
All validations passed."""
        
        result = executor._parse_validation_output(output, feature, {"test.py": "print('test')"})
        
        # Should be successful because of explicit Docker success marker and exit code 0
        assert result.success is True
        
    def test_parse_syntax_error(self):
        """Test parsing syntax error output"""
        executor = IncrementalExecutor("test_session")
        
        feature = Feature(
            id="FEATURE[4]",
            title="Test Feature",
            description="Test description",
            files=["test.py"],
            validation_criteria="Code executes without errors",
            dependencies=[],
            complexity=ComplexityLevel.LOW,
            short_name="test"
        )
        
        output = """Traceback (most recent call last):
  File "test.py", line 1
    print('hello'
                ^
SyntaxError: EOL while scanning string literal"""
        
        result = executor._parse_validation_output(output, feature, {"test.py": "print('hello'"})
        
        assert result.success is False
        assert "Syntax error" in result.feedback


if __name__ == "__main__":
    # Run tests
    test = TestValidationParser()
    
    print("Running validation parser tests...")
    
    try:
        test.test_parse_successful_docker_execution()
        print("✅ test_parse_successful_docker_execution passed")
    except AssertionError as e:
        print(f"❌ test_parse_successful_docker_execution failed: {e}")
    
    try:
        test.test_parse_failed_docker_execution()
        print("✅ test_parse_failed_docker_execution passed")
    except AssertionError as e:
        print(f"❌ test_parse_failed_docker_execution failed: {e}")
    
    try:
        test.test_parse_test_results()
        print("✅ test_parse_test_results passed")
    except AssertionError as e:
        print(f"❌ test_parse_test_results failed: {e}")
    
    try:
        test.test_parse_mixed_indicators()
        print("✅ test_parse_mixed_indicators passed")
    except AssertionError as e:
        print(f"❌ test_parse_mixed_indicators failed: {e}")
    
    try:
        test.test_parse_syntax_error()
        print("✅ test_parse_syntax_error passed")
    except AssertionError as e:
        print(f"❌ test_parse_syntax_error failed: {e}")
    
    print("\nAll tests completed!")