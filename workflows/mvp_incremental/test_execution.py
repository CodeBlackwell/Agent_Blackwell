"""
Phase 9: Test Execution Module

This module implements test execution after each feature implementation,
providing a verification loop to ensure code correctness.
"""

import asyncio
import os
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

from shared.utils import logger
from workflows.mvp_incremental.validator import CodeValidator
from workflows.mvp_incremental.error_analyzer import ErrorAnalyzer, ErrorContext


@dataclass
class TestResult:
    """Result from running tests."""
    success: bool
    passed: int
    failed: int
    errors: List[str]
    output: str
    test_files: List[str]


@dataclass
class TestExecutionConfig:
    """Configuration for test execution."""
    run_tests: bool = True
    test_command: str = "pytest"
    test_timeout: int = 30
    fix_on_failure: bool = True
    max_fix_attempts: int = 2


class TestExecutor:
    """Handles test execution after feature implementation."""
    
    def __init__(self, validator: CodeValidator, config: TestExecutionConfig):
        self.validator = validator
        self.config = config
        self.error_analyzer = ErrorAnalyzer()
        
    async def execute_tests(self, 
                          code: str, 
                          feature_name: str,
                          test_files: Optional[List[str]] = None) -> TestResult:
        """Execute tests for the implemented feature."""
        if not self.config.run_tests:
            return TestResult(
                success=True, 
                passed=0, 
                failed=0, 
                errors=[], 
                output="Test execution disabled",
                test_files=[]
            )
            
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
                test_files=[]
            )
            
        # Run the tests
        return await self._run_tests(test_files)
        
    async def _run_tests(self, test_files: List[str]) -> TestResult:
        """Run pytest on the specified test files."""
        test_command = f"{self.config.test_command} {' '.join(test_files)} -v"
        
        try:
            # Use the validator's execute method to run tests
            result = await self.validator.execute_code(
                f"import subprocess; result = subprocess.run('{test_command}', shell=True, capture_output=True, text=True); print(result.stdout); print(result.stderr)",
                timeout=self.config.test_timeout
            )
            
            if result.success:
                # Parse test output
                return self._parse_test_output(result.output, test_files)
            else:
                return TestResult(
                    success=False,
                    passed=0,
                    failed=0,
                    errors=[result.error],
                    output=result.output,
                    test_files=test_files
                )
                
        except Exception as e:
            return TestResult(
                success=False,
                passed=0,
                failed=0,
                errors=[str(e)],
                output="",
                test_files=test_files
            )
            
    def _parse_test_output(self, output: str, test_files: List[str]) -> TestResult:
        """Parse pytest output to extract results."""
        # Look for pytest summary line
        summary_match = re.search(r'(\d+) passed(?:, (\d+) failed)?', output)
        
        if summary_match:
            passed = int(summary_match.group(1))
            failed = int(summary_match.group(2) or 0)
            
            # Extract failure details
            errors = []
            if failed > 0:
                # Find FAILED lines
                failure_lines = re.findall(r'FAILED (.+?) - (.+)', output)
                for test_name, error_msg in failure_lines:
                    errors.append(f"{test_name}: {error_msg}")
                    
            return TestResult(
                success=failed == 0,
                passed=passed,
                failed=failed,
                errors=errors,
                output=output,
                test_files=test_files
            )
        else:
            # Could not parse output, assume failure
            return TestResult(
                success=False,
                passed=0,
                failed=0,
                errors=["Could not parse test output"],
                output=output,
                test_files=test_files
            )
            
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
    config: Optional[TestExecutionConfig] = None
) -> Tuple[str, TestResult]:
    """Execute tests and attempt fixes if needed."""
    if config is None:
        config = TestExecutionConfig()
        
    executor = TestExecutor(validator, config)
    
    # Run initial tests
    test_result = await executor.execute_tests(code, feature_name)
    
    # If tests fail, attempt to fix
    if not test_result.success and config.fix_on_failure:
        code, test_result = await executor.fix_test_failures(
            code, test_result, feature_name
        )
        
    return code, test_result