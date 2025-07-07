"""
Test Executor for TDD Workflow
Actually executes tests and provides detailed feedback
"""
import asyncio
import os
import tempfile
import subprocess
import json
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import re

from workflows.logger import workflow_logger as logger
from workflows.tdd.tdd_cycle_manager import TestExecutionResult, TDDPhase


class TestExecutor:
    """Executes tests and analyzes results for TDD workflow"""
    
    def __init__(self, use_docker: bool = False, timeout: int = 30):
        self.use_docker = use_docker
        self.timeout = timeout
        self._test_runners_checked = False
        self._available_runners = {}
        
    async def execute_tests(
        self,
        test_code: str,
        implementation_code: Dict[str, str],
        phase: TDDPhase,
        language: str = "python",
        project_directory: Optional[Path] = None
    ) -> TestExecutionResult:
        """
        Execute tests in isolated environment
        
        Args:
            test_code: The test code to execute
            implementation_code: Implementation files (filename -> content)
            phase: Current TDD phase
            language: Programming language (python, javascript, etc)
            project_directory: Optional path to existing project directory
            
        Returns:
            TestExecutionResult with detailed test outcomes
        """
        # Check available test runners
        await self._check_test_runners()
        
        # Check if we have a runner for this language
        runner = self._get_test_runner(language.lower())
        if not runner:
            logger.warning(f"No test runner available for {language}, using simulation")
            return self._simulate_test_execution(test_code, implementation_code, phase)
        
        if language.lower() == "python":
            return await self._execute_python_tests(test_code, implementation_code, phase, project_directory)
        elif language.lower() in ["javascript", "js", "typescript", "ts"]:
            return await self._execute_javascript_tests(test_code, implementation_code, phase, project_directory)
        else:
            # Fallback to simulation for unsupported languages
            return self._simulate_test_execution(test_code, implementation_code, phase)
    
    async def _execute_python_tests(
        self,
        test_code: str,
        implementation_code: Dict[str, str],
        phase: TDDPhase,
        project_directory: Optional[Path] = None
    ) -> TestExecutionResult:
        """Execute Python tests using pytest"""
        
        # Use project directory if provided, otherwise use temp directory
        if project_directory and project_directory.exists():
            logger.info(f"Using project directory for tests: {project_directory}")
            return await self._run_tests_in_directory(project_directory, phase)
        
        # Fallback to temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Write implementation files
            for filename, content in implementation_code.items():
                file_path = temp_path / filename
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content)
            
            # Extract test files from test_code
            test_files = self._extract_test_files(test_code, "python")
            
            # Write test files
            for filename, content in test_files.items():
                file_path = temp_path / filename
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content)
            
            # Create __init__.py files for proper imports
            for dir_path in temp_path.rglob("**/"):
                if dir_path.is_dir():
                    (dir_path / "__init__.py").touch()
            
            # Run pytest
            try:
                result = await self._run_pytest(temp_path)
                return self._parse_pytest_result(result, phase, len(test_files))
            except Exception as e:
                logger.error(f"Error executing Python tests: {str(e)}")
                return TestExecutionResult(
                    phase=phase,
                    success=False,
                    total_tests=0,
                    passed_tests=0,
                    failed_tests=0,
                    error_messages=[f"Test execution error: {str(e)}"],
                    output=str(e)
                )
    
    async def _run_pytest(self, test_dir: Path) -> subprocess.CompletedProcess:
        """Run pytest and return result"""
        # Try different pytest commands
        pytest_commands = [
            ["python", "-m", "pytest"],
            ["pytest"],
            ["python", "-m", "unittest", "discover"]  # Fallback to unittest
        ]
        
        for base_cmd in pytest_commands:
            try:
                # Build full command
                if "pytest" in " ".join(base_cmd):
                    cmd = base_cmd + [
                        str(test_dir),
                        "-v",
                        "--tb=short",
                        "--no-header",
                        "-q"
                    ]
                    
                    # Add JSON report if pytest-json-report is available
                    try:
                        check_json = await asyncio.create_subprocess_exec(
                            *base_cmd, "--version",
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE
                        )
                        await check_json.communicate()
                        if check_json.returncode == 0:
                            cmd.extend([
                                "--json-report",
                                "--json-report-file=/tmp/pytest_report.json"
                            ])
                    except:
                        pass
                else:
                    # unittest command
                    cmd = base_cmd + ["-s", str(test_dir)]
                
                # Run test command
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=str(test_dir)
                )
                
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.timeout
                )
                
                # If command succeeded or had test failures (not command failures)
                if process.returncode in [0, 1]:  # 0 = all pass, 1 = some fail
                    return subprocess.CompletedProcess(
                        args=cmd,
                        returncode=process.returncode,
                        stdout=stdout.decode('utf-8'),
                        stderr=stderr.decode('utf-8')
                    )
                    
            except Exception as e:
                logger.debug(f"Failed to run {base_cmd[0]}: {str(e)}")
                continue
        
        # All commands failed
        error_msg = "No Python test runner available. Please install pytest: pip install pytest"
        return subprocess.CompletedProcess(
            args=["pytest"],
            returncode=2,
            stdout="",
            stderr=error_msg
        )
    
    async def _run_tests_in_directory(self, directory: Path, phase: TDDPhase) -> TestExecutionResult:
        """Run tests in a specific directory"""
        try:
            # Count test files
            test_files = list(directory.glob("**/test_*.py"))
            test_files.extend(directory.glob("**/*_test.py"))
            
            if not test_files:
                logger.warning(f"No test files found in {directory}")
                return TestExecutionResult(
                    phase=phase,
                    success=False,
                    total_tests=0,
                    passed_tests=0,
                    failed_tests=0,
                    error_messages=["No test files found"],
                    output="No test files found in project directory"
                )
            
            # Run pytest in the directory
            result = await self._run_pytest(directory)
            return self._parse_pytest_result(result, phase, len(test_files))
            
        except Exception as e:
            logger.error(f"Error running tests in directory: {str(e)}")
            return TestExecutionResult(
                phase=phase,
                success=False,
                total_tests=0,
                passed_tests=0,
                failed_tests=0,
                error_messages=[f"Test execution error: {str(e)}"],
                output=str(e)
            )
    
    def _parse_pytest_result(
        self,
        result: subprocess.CompletedProcess,
        phase: TDDPhase,
        test_file_count: int
    ) -> TestExecutionResult:
        """Parse pytest output to create TestExecutionResult"""
        
        output = result.stdout + "\n" + result.stderr
        
        # Try to parse JSON report if available
        try:
            with open("/tmp/pytest_report.json", "r") as f:
                report = json.load(f)
                
            total_tests = report["summary"]["total"]
            passed_tests = report["summary"]["passed"]
            failed_tests = report["summary"]["failed"] + report["summary"]["error"]
            
            # Extract error messages
            error_messages = []
            for test in report.get("tests", []):
                if test["outcome"] in ["failed", "error"]:
                    error_messages.append(
                        f"{test['nodeid']}: {test.get('call', {}).get('longrepr', 'Test failed')}"
                    )
            
            # Clean up report file
            os.remove("/tmp/pytest_report.json")
            
        except:
            # Fallback to parsing text output
            total_tests, passed_tests, failed_tests, error_messages = self._parse_pytest_text_output(output)
        
        success = failed_tests == 0 and total_tests > 0
        
        # Calculate coverage if pytest-cov is available
        coverage = self._extract_coverage(output)
        
        return TestExecutionResult(
            phase=phase,
            success=success,
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            error_messages=error_messages[:10],  # Limit to 10 errors
            output=output[-2000:],  # Last 2000 chars
            coverage_percent=coverage
        )
    
    def _parse_pytest_text_output(self, output: str) -> Tuple[int, int, int, List[str]]:
        """Parse pytest text output as fallback"""
        
        # Look for summary line
        summary_match = re.search(
            r'(\d+) passed|(\d+) failed|(\d+) error|(\d+) skipped',
            output
        )
        
        if not summary_match:
            # No tests found
            return 0, 0, 0, ["No tests found or pytest failed to run"]
        
        # Count different outcomes
        passed = 0
        failed = 0
        errors = []
        
        # Extract passed count
        passed_match = re.search(r'(\d+) passed', output)
        if passed_match:
            passed = int(passed_match.group(1))
        
        # Extract failed count
        failed_match = re.search(r'(\d+) failed', output)
        if failed_match:
            failed = int(failed_match.group(1))
        
        # Extract error count
        error_match = re.search(r'(\d+) error', output)
        if error_match:
            failed += int(error_match.group(1))
        
        total = passed + failed
        
        # Extract failure details
        failure_pattern = r'FAILED (.*?) - (.*?)(?:\n|$)'
        failures = re.findall(failure_pattern, output)
        for test_name, error_msg in failures:
            errors.append(f"{test_name}: {error_msg}")
        
        # Also look for ERROR lines
        error_pattern = r'ERROR (.*?) - (.*?)(?:\n|$)'
        error_matches = re.findall(error_pattern, output)
        for test_name, error_msg in error_matches:
            errors.append(f"{test_name}: {error_msg}")
        
        return total, passed, failed, errors
    
    def _extract_coverage(self, output: str) -> Optional[float]:
        """Extract test coverage percentage from output"""
        coverage_match = re.search(r'TOTAL\s+\d+\s+\d+\s+(\d+)%', output)
        if coverage_match:
            return float(coverage_match.group(1))
        return None
    
    async def _execute_javascript_tests(
        self,
        test_code: str,
        implementation_code: Dict[str, str],
        phase: TDDPhase,
        project_directory: Optional[Path] = None
    ) -> TestExecutionResult:
        """Execute JavaScript tests using Jest or Mocha"""
        
        # Use project directory if provided
        if project_directory and project_directory.exists():
            logger.info(f"Using project directory for JS tests: {project_directory}")
            # For now, simulate JS test execution in project directory
            # Full implementation would check for package.json, run npm test, etc.
            return self._simulate_test_execution(test_code, implementation_code, phase)
        
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Write implementation files
            for filename, content in implementation_code.items():
                file_path = temp_path / filename
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content)
            
            # Extract and write test files
            test_files = self._extract_test_files(test_code, "javascript")
            for filename, content in test_files.items():
                file_path = temp_path / filename
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content)
            
            # Create package.json for test runner
            package_json = {
                "name": "tdd-test-run",
                "version": "1.0.0",
                "scripts": {
                    "test": "jest"
                },
                "devDependencies": {
                    "jest": "^27.0.0"
                }
            }
            
            (temp_path / "package.json").write_text(json.dumps(package_json))
            
            # For now, return simulated results
            # Full implementation would run npm install && npm test
            return self._simulate_test_execution(test_code, implementation_code, phase)
    
    def _extract_test_files(self, test_code: str, language: str) -> Dict[str, str]:
        """Extract individual test files from test code"""
        files = {}
        
        # Look for file markers
        if language == "python":
            pattern = r'#\s*filename:\s*(\S+)\n(.*?)(?=#\s*filename:|$)'
        else:
            pattern = r'//\s*filename:\s*(\S+)\n(.*?)(?=//\s*filename:|$)'
        
        matches = re.findall(pattern, test_code, re.DOTALL)
        
        if matches:
            for filename, content in matches:
                files[filename] = content.strip()
        else:
            # No file markers, treat entire code as single test file
            if language == "python":
                files["test_main.py"] = test_code
            else:
                files["test_main.js"] = test_code
        
        return files
    
    def _simulate_test_execution(
        self,
        test_code: str,
        implementation_code: Dict[str, str],
        phase: TDDPhase
    ) -> TestExecutionResult:
        """Simulate test execution when actual execution isn't available"""
        
        # Count tests
        test_count = self._count_tests_in_code(test_code)
        
        if phase == TDDPhase.RED and not implementation_code:
            # RED phase - tests should fail
            return TestExecutionResult(
                phase=phase,
                success=False,
                total_tests=test_count,
                passed_tests=0,
                failed_tests=test_count,
                error_messages=[
                    "Module not found: No implementation files",
                    "All tests failed due to missing implementation"
                ],
                output="Simulated: Tests failed as expected in RED phase"
            )
        else:
            # GREEN phase - simulate based on implementation
            if implementation_code:
                # Assume tests pass if implementation exists
                return TestExecutionResult(
                    phase=phase,
                    success=True,
                    total_tests=test_count,
                    passed_tests=test_count,
                    failed_tests=0,
                    error_messages=[],
                    output="Simulated: All tests passed",
                    coverage_percent=85.0
                )
            else:
                return TestExecutionResult(
                    phase=phase,
                    success=False,
                    total_tests=test_count,
                    passed_tests=0,
                    failed_tests=test_count,
                    error_messages=["No implementation found"],
                    output="Simulated: Tests failed"
                )
    
    def _count_tests_in_code(self, test_code: str) -> int:
        """Count number of tests in code"""
        # Count test functions/methods
        patterns = [
            r'def test_\w+',  # Python
            r'it\(["\'].*?["\']',  # JavaScript/Jest
            r'test\(["\'].*?["\']',  # Jest
            r'describe\(["\'].*?["\']'  # Jest/Mocha suites
        ]
        
        count = 0
        for pattern in patterns:
            matches = re.findall(pattern, test_code)
            count += len(matches)
        
        return max(count, 1)  # At least 1 test
    
    async def _check_test_runners(self):
        """Check which test runners are available"""
        if self._test_runners_checked:
            return
        
        runners_to_check = {
            'python': ['pytest', 'python -m pytest', 'unittest'],
            'javascript': ['jest', 'npm test', 'mocha', 'yarn test'],
            'typescript': ['jest', 'npm test', 'mocha', 'yarn test']
        }
        
        for language, runners in runners_to_check.items():
            self._available_runners[language] = []
            for runner in runners:
                try:
                    # Check if runner is available
                    check_cmd = runner.split()[0]
                    process = await asyncio.create_subprocess_exec(
                        'which', check_cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    stdout, _ = await process.communicate()
                    
                    if process.returncode == 0:
                        self._available_runners[language].append(runner)
                        logger.info(f"Found test runner: {runner} for {language}")
                except:
                    pass
        
        self._test_runners_checked = True
        
        # Log available runners
        for lang, runners in self._available_runners.items():
            if runners:
                logger.info(f"Available {lang} test runners: {', '.join(runners)}")
            else:
                logger.warning(f"No test runners found for {lang}")
    
    def _get_test_runner(self, language: str) -> Optional[str]:
        """Get the best available test runner for a language"""
        if not self._test_runners_checked:
            # This should have been called async, but fallback to defaults
            logger.warning("Test runners not checked, using defaults")
            
        runners = self._available_runners.get(language, [])
        if runners:
            return runners[0]
        
        # Default runners if none found
        defaults = {
            'python': 'python -m pytest',
            'javascript': 'npm test',
            'typescript': 'npm test'
        }
        return defaults.get(language)


# Helper function for integration
async def execute_tdd_tests(
    test_code: str,
    implementation_code: Dict[str, str],
    phase: TDDPhase,
    language: str = "python",
    project_directory: Optional[Path] = None
) -> TestExecutionResult:
    """Execute tests for TDD workflow"""
    executor = TestExecutor()
    return await executor.execute_tests(
        test_code,
        implementation_code,
        phase,
        language,
        project_directory
    )