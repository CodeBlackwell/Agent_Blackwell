"""Test Runner Agent for GREEN phase - Runs tests and validates they pass"""

import asyncio
import subprocess
import tempfile
import time
from pathlib import Path
from typing import AsyncGenerator, Dict, Any, List

from models.flagship_models import (
    AgentType, TDDPhase, PhaseResult, TestResult, TestStatus
)
from models.execution_tracer import ExecutionTracer
from utils.command_tracer import create_traced_runner


class TestRunnerFlagship:
    """Agent responsible for running tests and validating they pass in the GREEN phase"""
    
    def __init__(self, tracer: ExecutionTracer = None, file_manager=None):
        self.agent_type = AgentType.TEST_RUNNER
        self.phase = TDDPhase.GREEN
        self.tracer = tracer
        self.file_manager = file_manager
        self.run_command = create_traced_runner(tracer)
    
    async def run_tests(self, test_code: str, implementation_code: str, 
                       context: Dict[str, Any] = None) -> AsyncGenerator[str, None]:
        """
        Run tests and report results
        
        Args:
            test_code: The test code to run
            implementation_code: The implementation code to test
            context: Additional context
            
        Yields:
            Test execution results as they're generated
        """
        yield f"🟢 GREEN Phase: Running tests to validate implementation...\n"
        
        # Check if we should use file manager to get files
        if self.file_manager:
            file_context = self.file_manager.get_file_context("test_runner")
            all_files = file_context.get("all_python_files", [])
            
            if all_files:
                yield f"📁 Found {len(all_files)} Python file(s) in session\n"
                
                # Try to read test and implementation from file manager
                if not test_code:
                    test_file = next((f for f in all_files if "test" in f), None)
                    if test_file:
                        test_code = self.file_manager.read_file(test_file) or test_code
                        yield f"  - Loaded test code from {test_file}\n"
                        
                if not implementation_code:
                    impl_file = next((f for f in all_files if "test" not in f and f.endswith(".py")), None)
                    if impl_file:
                        implementation_code = self.file_manager.read_file(impl_file) or implementation_code
                        yield f"  - Loaded implementation from {impl_file}\n"
        
        # Create temporary directory for test execution
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Write files
            test_file = temp_path / "test_implementation.py"
            
            # Determine implementation file name based on imports in test code
            if "from calculator import" in test_code:
                impl_file = temp_path / "calculator.py"
            elif "from greet import" in test_code:
                impl_file = temp_path / "greet.py"
            else:
                impl_file = temp_path / "main.py"
            
            yield f"Writing test files to temporary directory...\n"
            
            # Write implementation
            impl_file.write_text(implementation_code)
            yield f"✓ Implementation written to {impl_file.name}\n"
            
            # Write tests
            test_file.write_text(test_code)
            yield f"✓ Tests written to {test_file.name}\n\n"
            
            # Run tests
            yield "Running tests with pytest...\n"
            yield "=" * 60 + "\n"
            
            test_results = []
            start_time = time.time()
            
            try:
                # Run pytest with detailed output
                result = self.run_command(
                    ["python", "-m", "pytest", str(test_file), "-v", "--tb=short"],
                    cwd=temp_dir,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                duration = time.time() - start_time
                
                # Parse and yield output
                output_lines = result.stdout.split('\n')
                for line in output_lines:
                    yield line + '\n'
                    await asyncio.sleep(0.01)
                
                # Parse test results
                test_results = self._parse_pytest_output(result.stdout, result.stderr, result.returncode)
                
                # Summary
                yield "\n" + "=" * 60 + "\n"
                yield self._format_test_summary(test_results, duration)
                
            except subprocess.TimeoutExpired:
                yield "\n❌ ERROR: Test execution timed out after 30 seconds\n"
                test_results = [TestResult(
                    test_name="test_execution",
                    status=TestStatus.ERROR,
                    error_message="Test execution timed out"
                )]
            except Exception as e:
                yield f"\n❌ ERROR: Failed to run tests: {str(e)}\n"
                test_results = [TestResult(
                    test_name="test_execution",
                    status=TestStatus.ERROR,
                    error_message=str(e)
                )]
            
            # Store results
            self._test_results = test_results
            self._all_passed = all(t.status == TestStatus.PASSED for t in test_results)
    
    def _parse_pytest_output(self, stdout: str, stderr: str, returncode: int) -> List[TestResult]:
        """Parse pytest output to extract test results"""
        test_results = []
        
        # Simple parsing - look for test result lines
        lines = stdout.split('\n')
        for line in lines:
            line = line.strip()
            
            # Match test result lines (e.g., "test_addition PASSED")
            if '::' in line and any(status in line for status in ['PASSED', 'FAILED', 'ERROR', 'SKIPPED']):
                parts = line.split('::')
                if len(parts) >= 2:
                    test_name = parts[1].split()[0]
                    
                    if 'PASSED' in line:
                        status = TestStatus.PASSED
                        error_msg = None
                    elif 'FAILED' in line:
                        status = TestStatus.FAILED
                        # Try to extract error message
                        error_msg = self._extract_error_message(stdout, test_name)
                    elif 'ERROR' in line:
                        status = TestStatus.ERROR
                        error_msg = self._extract_error_message(stdout, test_name)
                    else:
                        status = TestStatus.SKIPPED
                        error_msg = None
                    
                    test_results.append(TestResult(
                        test_name=test_name,
                        status=status,
                        error_message=error_msg,
                        stdout=stdout if status != TestStatus.PASSED else None
                    ))
        
        # If no results parsed but we have output, create a summary result
        if not test_results:
            if returncode == 0:
                # All tests passed but couldn't parse individual results
                test_results.append(TestResult(
                    test_name="all_tests",
                    status=TestStatus.PASSED,
                    stdout=stdout
                ))
            else:
                # Tests failed
                test_results.append(TestResult(
                    test_name="test_execution",
                    status=TestStatus.FAILED,
                    error_message="Test execution failed",
                    stdout=stdout,
                    stderr=stderr
                ))
        
        return test_results
    
    def _extract_error_message(self, output: str, test_name: str) -> str:
        """Extract error message for a specific test from pytest output"""
        lines = output.split('\n')
        in_test = False
        error_lines = []
        
        for line in lines:
            if test_name in line and 'FAILED' in line:
                in_test = True
                continue
            elif in_test:
                if line.strip() and not line.startswith(' '):
                    # Reached next test or section
                    break
                elif line.strip():
                    error_lines.append(line.strip())
        
        return ' '.join(error_lines[:3]) if error_lines else "Test failed"
    
    def _format_test_summary(self, test_results: List[TestResult], duration: float) -> str:
        """Format a summary of test results"""
        total = len(test_results)
        passed = sum(1 for t in test_results if t.status == TestStatus.PASSED)
        failed = sum(1 for t in test_results if t.status == TestStatus.FAILED)
        errors = sum(1 for t in test_results if t.status == TestStatus.ERROR)
        skipped = sum(1 for t in test_results if t.status == TestStatus.SKIPPED)
        
        lines = [
            "Test Summary:",
            f"Total Tests: {total}",
            f"✅ Passed: {passed}",
        ]
        
        if failed > 0:
            lines.append(f"❌ Failed: {failed}")
        if errors > 0:
            lines.append(f"💥 Errors: {errors}")
        if skipped > 0:
            lines.append(f"⏭️  Skipped: {skipped}")
        
        lines.append(f"Duration: {duration:.2f}s")
        
        if passed == total:
            lines.append("\n🎉 All tests passed! Ready to proceed.")
        else:
            lines.append("\n⚠️  Some tests failed. Implementation needs revision.")
        
        return '\n'.join(lines)
    
    def get_test_results(self) -> List[TestResult]:
        """Get the test execution results"""
        return getattr(self, '_test_results', [])
    
    def all_tests_passed(self) -> bool:
        """Check if all tests passed"""
        return getattr(self, '_all_passed', False)
    
    def create_phase_result(self, success: bool = None, error: str = None) -> PhaseResult:
        """Create a PhaseResult for this agent's execution"""
        if success is None:
            success = self.all_tests_passed()
        
        test_results = self.get_test_results()
        
        # Create output summary
        output_lines = []
        for result in test_results:
            status_emoji = {
                TestStatus.PASSED: "✅",
                TestStatus.FAILED: "❌",
                TestStatus.ERROR: "💥",
                TestStatus.SKIPPED: "⏭️",
                TestStatus.NOT_RUN: "⏸️"
            }.get(result.status, "❓")
            
            output_lines.append(f"{status_emoji} {result.test_name}: {result.status.name}")
            if result.error_message:
                output_lines.append(f"   Error: {result.error_message}")
        
        return PhaseResult(
            phase=self.phase,
            success=success,
            agent=self.agent_type,
            output='\n'.join(output_lines),
            test_results=test_results,
            error=error,
            metadata={
                "all_passed": self.all_tests_passed(),
                "test_count": len(test_results),
                "passed_count": sum(1 for t in test_results if t.status == TestStatus.PASSED),
                "failed_count": sum(1 for t in test_results if t.status == TestStatus.FAILED)
            }
        )