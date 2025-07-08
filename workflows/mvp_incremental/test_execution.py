"""
Phase 9: Test Execution Module (Enhanced for Operation Red Yellow)

This module implements test execution with enhanced capabilities for TDD workflow:
- Support for expect_failure parameter (RED phase validation)
- Enhanced test output parsing with detailed failure context
- Test result caching mechanism for performance
- Detailed failure context extraction for better debugging
"""

import asyncio
import os
import re
import json
import hashlib
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
from collections import defaultdict

from workflows.logger import workflow_logger as logger
from workflows.mvp_incremental.validator import CodeValidator
from workflows.mvp_incremental.error_analyzer import SimplifiedErrorAnalyzer, ErrorContext


@dataclass
class TestFailureDetail:
    """Detailed information about a test failure."""
    test_name: str
    test_file: str
    failure_type: str  # AssertionError, ImportError, etc.
    failure_message: str
    line_number: Optional[int] = None
    expected_value: Optional[str] = None
    actual_value: Optional[str] = None
    stack_trace: Optional[str] = None


@dataclass
class TestResult:
    """Enhanced result from running tests."""
    success: bool
    passed: int
    failed: int
    errors: List[str]
    output: str
    test_files: List[str]
    failure_details: List[TestFailureDetail] = field(default_factory=list)
    expected_failure: bool = False  # Was failure expected (RED phase)?
    execution_time: float = 0.0  # Time taken to run tests
    coverage: Optional[float] = None  # Test coverage percentage if available


@dataclass
class TestExecutionConfig:
    """Enhanced configuration for test execution."""
    run_tests: bool = True
    test_command: str = "pytest"
    test_timeout: int = 30
    fix_on_failure: bool = True
    max_fix_attempts: int = 2
    expect_failure: bool = False  # For RED phase - tests should fail
    cache_results: bool = True  # Cache test results for performance
    extract_coverage: bool = True  # Extract test coverage data
    verbose_output: bool = True  # Include detailed test output


class TestResultCache:
    """Cache for test results to avoid re-running identical tests."""
    
    def __init__(self):
        self._cache: Dict[str, TestResult] = {}
        self._max_cache_size = 100
    
    def _generate_key(self, code: str, test_files: List[str]) -> str:
        """Generate cache key from code and test files."""
        content = f"{code}:{':'.join(sorted(test_files))}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, code: str, test_files: List[str]) -> Optional[TestResult]:
        """Get cached result if available."""
        key = self._generate_key(code, test_files)
        return self._cache.get(key)
    
    def set(self, code: str, test_files: List[str], result: TestResult):
        """Cache a test result."""
        if len(self._cache) >= self._max_cache_size:
            # Remove oldest entry
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
        
        key = self._generate_key(code, test_files)
        self._cache[key] = result


class TestExecutor:
    """Enhanced test executor with TDD support and caching."""
    
    def __init__(self, validator: CodeValidator, config: TestExecutionConfig):
        self.validator = validator
        self.config = config
        self.error_analyzer = SimplifiedErrorAnalyzer()
        self._result_cache = TestResultCache() if config.cache_results else None
        
    async def execute_tests(self, 
                          code: str, 
                          feature_name: str,
                          test_files: Optional[List[str]] = None,
                          expect_failure: Optional[bool] = None) -> TestResult:
        """Execute tests with support for expected failures (RED phase).
        
        Args:
            code: The implementation code
            feature_name: Name of the feature being tested
            test_files: Optional list of test files to run
            expect_failure: Override config to expect test failure (RED phase)
        """
        if not self.config.run_tests:
            return TestResult(
                success=True, 
                passed=0, 
                failed=0, 
                errors=[], 
                output="Test execution disabled",
                test_files=[],
                expected_failure=False
            )
        
        # Use expect_failure parameter if provided, otherwise use config
        expect_failure = expect_failure if expect_failure is not None else self.config.expect_failure
            
        # Determine which tests to run
        if not test_files:
            test_files = self._find_test_files(code, feature_name)
            
        if not test_files:
            logger.info(f"No test files found for feature: {feature_name}")
            return TestResult(
                success=True,
                passed=0,
                failed=0,
                errors=[],
                output="No tests found",
                test_files=[],
                expected_failure=expect_failure
            )
        
        # Check cache if enabled
        if self._result_cache and not expect_failure:
            cached_result = self._result_cache.get(code, test_files)
            if cached_result:
                logger.info(f"Using cached test results for {feature_name}")
                return cached_result
            
        # Run the tests
        start_time = datetime.now()
        result = await self._run_tests(test_files, expect_failure)
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Update execution time
        result.execution_time = execution_time
        
        # Validate expected failure behavior
        if expect_failure:
            if result.failed == 0:
                # Tests should have failed but didn't - this is an error in RED phase
                logger.warning(f"Expected tests to fail for {feature_name} but they passed!")
                result.success = False
                result.errors.append("Tests passed when failure was expected (RED phase violation)")
            else:
                # Tests failed as expected - this is success in RED phase
                logger.info(f"Tests failed as expected for {feature_name} (RED phase confirmed)")
                result.success = True
                result.expected_failure = True
        
        # Cache successful results
        if self._result_cache and not expect_failure and result.success:
            self._result_cache.set(code, test_files, result)
            
        return result
        
    async def _run_tests(self, test_files: List[str], expect_failure: bool) -> TestResult:
        """Run pytest on the specified test files with enhanced output parsing."""
        # Build command with verbose output and coverage if requested
        test_command = f"{self.config.test_command} {' '.join(test_files)}"
        if self.config.verbose_output:
            test_command += " -v"
        if self.config.extract_coverage and not expect_failure:
            test_command += " --cov --cov-report=term-missing"
        
        try:
            # Use the validator's execute method to run tests
            result = await self.validator.execute_code(
                f"import subprocess; result = subprocess.run('{test_command}', shell=True, capture_output=True, text=True); print(result.stdout); print(result.stderr)",
                timeout=self.config.test_timeout
            )
            
            if result.success or expect_failure:
                # Parse test output (enhanced parsing)
                return self._parse_test_output_enhanced(result.output, test_files, expect_failure)
            else:
                return TestResult(
                    success=False,
                    passed=0,
                    failed=0,
                    errors=[result.error],
                    output=result.output,
                    test_files=test_files,
                    expected_failure=expect_failure
                )
                
        except Exception as e:
            return TestResult(
                success=False,
                passed=0,
                failed=0,
                errors=[str(e)],
                output="",
                test_files=test_files,
                expected_failure=expect_failure
            )
            
    def _parse_test_output_enhanced(self, output: str, test_files: List[str], expect_failure: bool) -> TestResult:
        """Enhanced parsing of pytest output with detailed failure extraction."""
        # Initialize counters
        passed = 0
        failed = 0
        errors = []
        failure_details = []
        coverage = None
        
        # Look for pytest summary line - handle different formats
        # Try most specific patterns first
        summary_patterns = [
            (r'=+ (\d+) failed, (\d+) passed', 'failed_first'),
            (r'(\d+) failed, (\d+) passed', 'failed_first'),
            (r'(\d+) passed, (\d+) failed', 'passed_first'),
            (r'(\d+) failed(?:, (\d+) passed)?', 'failed_first'),
            (r'(\d+) passed(?:, (\d+) failed)?', 'passed_first'),
            (r'(\d+) failed', 'failed_only'),
            (r'(\d+) passed', 'passed_only')
        ]
        
        for pattern, order in summary_patterns:
            summary_match = re.search(pattern, output)
            if summary_match:
                groups = summary_match.groups()
                if order == 'failed_first':
                    failed = int(groups[0] or 0)
                    passed = int(groups[1] or 0) if len(groups) > 1 else 0
                elif order == 'passed_first':
                    passed = int(groups[0] or 0)
                    failed = int(groups[1] or 0) if len(groups) > 1 else 0
                elif order == 'failed_only':
                    failed = int(groups[0] or 0)
                    passed = 0
                elif order == 'passed_only':
                    passed = int(groups[0] or 0)
                    failed = 0
                break
        
        # Extract detailed failure information
        if failed > 0 or "FAILED" in output:
            failure_details = self._extract_failure_details(output)
            errors = [f"{fd.test_name}: {fd.failure_message}" for fd in failure_details]
        
        # Extract coverage information if present
        coverage_match = re.search(r'TOTAL\s+\d+\s+\d+\s+(\d+)%', output)
        if coverage_match:
            coverage = float(coverage_match.group(1))
        
        # Check for other error indicators
        if "ERROR" in output and failed == 0:
            # Collection errors or import errors
            error_matches = re.findall(r'ERROR (.+?) - (.+)', output)
            for location, error_msg in error_matches:
                errors.append(f"ERROR {location}: {error_msg}")
                failed += 1
        
        # Determine success based on expectation
        if expect_failure:
            success = failed > 0  # Success if tests failed as expected
        else:
            success = failed == 0 and len(errors) == 0
        
        return TestResult(
            success=success,
            passed=passed,
            failed=failed,
            errors=errors,
            output=output,
            test_files=test_files,
            failure_details=failure_details,
            expected_failure=expect_failure,
            coverage=coverage
        )
    
    def _extract_failure_details(self, output: str) -> List[TestFailureDetail]:
        """Extract detailed failure information from pytest output."""
        details = []
        
        # Pattern to match test failures with context
        failure_pattern = r'FAILED ([\w/\.]+::[\w]+)(?:\[.*?\])? - (.+?)(?=\n(?:FAILED|PASSED|=|$))'
        matches = re.findall(failure_pattern, output, re.DOTALL)
        
        for test_path, failure_info in matches:
            # Parse test file and name
            if '::' in test_path:
                test_file, test_name = test_path.split('::', 1)
            else:
                test_file = test_path
                test_name = "unknown"
            
            # Determine failure type and message
            failure_type = "Unknown"
            failure_message = failure_info.strip()
            
            # Extract specific error types
            if "AssertionError" in failure_info:
                failure_type = "AssertionError"
                # Try to extract expected vs actual
                assert_match = re.search(r'assert (.+?) == (.+)', failure_info)
                if assert_match:
                    detail = TestFailureDetail(
                        test_name=test_name,
                        test_file=test_file,
                        failure_type=failure_type,
                        failure_message=failure_message,
                        expected_value=assert_match.group(2),
                        actual_value=assert_match.group(1)
                    )
                else:
                    detail = TestFailureDetail(
                        test_name=test_name,
                        test_file=test_file,
                        failure_type=failure_type,
                        failure_message=failure_message
                    )
            elif "ImportError" in failure_info:
                failure_type = "ImportError"
                detail = TestFailureDetail(
                    test_name=test_name,
                    test_file=test_file,
                    failure_type=failure_type,
                    failure_message=failure_message
                )
            elif "AttributeError" in failure_info:
                failure_type = "AttributeError"
                detail = TestFailureDetail(
                    test_name=test_name,
                    test_file=test_file,
                    failure_type=failure_type,
                    failure_message=failure_message
                )
            elif "TypeError" in failure_info:
                failure_type = "TypeError"
                detail = TestFailureDetail(
                    test_name=test_name,
                    test_file=test_file,
                    failure_type=failure_type,
                    failure_message=failure_message
                )
            else:
                detail = TestFailureDetail(
                    test_name=test_name,
                    test_file=test_file,
                    failure_type=failure_type,
                    failure_message=failure_message
                )
            
            # Extract line number if available
            line_match = re.search(r'line (\d+)', failure_info)
            if line_match:
                detail.line_number = int(line_match.group(1))
            
            # Extract stack trace if verbose
            if "\n" in failure_info:
                lines = failure_info.split("\n")
                if len(lines) > 2:
                    detail.stack_trace = "\n".join(lines[1:])
            
            details.append(detail)
        
        return details
            
    def _find_test_files(self, code: str, feature_name: str) -> List[str]:
        """Find test files related to the feature."""
        test_files = []
        
        # Look for test imports or references in the code
        test_patterns = [
            r'test_(\w+)\.py',
            r'(\w+)_test\.py',
            r'tests?/(\w+)',
        ]
        
        for pattern in test_patterns:
            matches = re.findall(pattern, code)
            for match in matches:
                # Construct possible test file paths
                candidates = [
                    f"test_{match}.py",
                    f"{match}_test.py",
                    f"tests/test_{match}.py",
                    f"tests/{match}_test.py"
                ]
                test_files.extend(candidates)
                
        # Also look for feature-specific test file
        feature_slug = feature_name.lower().replace(' ', '_')
        test_files.extend([
            f"test_{feature_slug}.py",
            f"tests/test_{feature_slug}.py"
        ])
        
        # Filter to existing files
        existing_files = []
        for file in test_files:
            if Path(file).exists():
                existing_files.append(file)
                
        return list(set(existing_files))  # Remove duplicates
        
    async def fix_test_failures(self,
                              code: str,
                              test_result: TestResult,
                              feature_name: str,
                              attempt: int = 1) -> Tuple[str, TestResult]:
        """Attempt to fix code based on test failures."""
        if test_result.success or not self.config.fix_on_failure:
            return code, test_result
            
        if attempt > self.config.max_fix_attempts:
            logger.warning(f"Max fix attempts ({self.config.max_fix_attempts}) reached for {feature_name}")
            return code, test_result
            
        # Analyze test failures
        error_context = ErrorContext(
            error_type="TestFailure",
            error_message="; ".join(test_result.errors),
            line_number=0,  # Tests don't have specific line numbers
            context_lines=[],
            stack_trace=test_result.output,
            recovery_hints=self._generate_test_fix_hints(test_result)
        )
        
        # Generate fix prompt
        fix_prompt = self._create_test_fix_prompt(
            code, 
            feature_name, 
            error_context,
            test_result
        )
        
        # This would normally call the coder agent to fix the code
        # For now, return the original code
        # In actual implementation, this would integrate with the coder agent
        
        logger.info(f"Would attempt to fix test failures for {feature_name}")
        return code, test_result
        
    def _generate_test_fix_hints(self, test_result: TestResult) -> List[str]:
        """Generate hints for fixing test failures."""
        hints = []
        
        for error in test_result.errors:
            if "AssertionError" in error:
                hints.append("Check that the implementation matches test expectations")
            elif "AttributeError" in error:
                hints.append("Ensure all required methods/attributes are implemented")
            elif "TypeError" in error:
                hints.append("Verify function signatures match test calls")
            elif "ImportError" in error:
                hints.append("Check that all necessary imports are included")
                
        return hints
        
    def _create_test_fix_prompt(self,
                              code: str,
                              feature_name: str,
                              error_context: ErrorContext,
                              test_result: TestResult) -> str:
        """Create a prompt for fixing test failures."""
        return f"""
The implementation of '{feature_name}' has failing tests.

Test Results:
- Passed: {test_result.passed}
- Failed: {test_result.failed}

Failures:
{chr(10).join(test_result.errors)}

Current Implementation:
```python
{code}
```

Test Output:
```
{test_result.output[-500:]}  # Last 500 chars
```

Please fix the implementation to make all tests pass. Focus on:
{chr(10).join(f"- {hint}" for hint in error_context.recovery_hints)}
"""


# Integration helper for the workflow
async def execute_and_fix_tests(
    code: str,
    feature_name: str,
    validator: CodeValidator,
    config: Optional[TestExecutionConfig] = None,
    expect_failure: Optional[bool] = None
) -> Tuple[str, TestResult]:
    """Execute tests and attempt fixes if needed.
    
    Args:
        code: Implementation code to test
        feature_name: Name of the feature
        validator: Code validator instance
        config: Test execution configuration
        expect_failure: Whether to expect test failure (RED phase)
    """
    if config is None:
        config = TestExecutionConfig()
        
    executor = TestExecutor(validator, config)
    
    # Run initial tests
    test_result = await executor.execute_tests(code, feature_name, expect_failure=expect_failure)
    
    # If tests fail unexpectedly, attempt to fix (not in RED phase)
    if not test_result.success and config.fix_on_failure and not expect_failure:
        code, test_result = await executor.fix_test_failures(
            code, test_result, feature_name
        )
        
    return code, test_result


# Helper to validate RED phase requirements
async def validate_red_phase(
    test_code: str,
    feature_name: str,
    validator: CodeValidator,
    config: Optional[TestExecutionConfig] = None
) -> TestResult:
    """Validate that tests fail without implementation (RED phase).
    
    This ensures TDD compliance by confirming tests fail before implementation.
    """
    if config is None:
        config = TestExecutionConfig(expect_failure=True, fix_on_failure=False)
    else:
        config.expect_failure = True
        config.fix_on_failure = False
    
    executor = TestExecutor(validator, config)
    
    # Run tests with empty/minimal code (should fail)
    empty_code = ""  # No implementation
    result = await executor.execute_tests(empty_code, feature_name, expect_failure=True)
    
    if result.success and result.expected_failure:
        logger.info(f"✅ RED phase validated: Tests fail without implementation for {feature_name}")
    else:
        logger.warning(f"⚠️ RED phase validation failed for {feature_name}")
    
    return result