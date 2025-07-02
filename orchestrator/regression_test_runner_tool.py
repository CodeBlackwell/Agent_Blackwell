import subprocess
import os
import json
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from beeai_framework.tools import Tool, ToolOutput
from beeai_framework.tools.types import ToolRunOptions
from beeai_framework.context import RunContext

class TestExecutionInput(BaseModel):
    """Input schema for test execution"""
    project_path: str = Field(description="Path to the project containing tests")
    test_command: Optional[str] = Field(default=None, description="Custom test command to run")
    
class TestResult(BaseModel):
    """Single test result"""
    name: str
    status: str  # "passed", "failed", "skipped"
    message: Optional[str] = None
    duration: Optional[float] = None

class TestExecutionResult(BaseModel):
    """Complete test execution results"""
    total_tests: int
    passed: int
    failed: int
    skipped: int
    success: bool
    test_results: List[TestResult]
    output: str
    command_used: str

class TestExecutionOutput(ToolOutput):
    """Output from test execution"""
    result: TestExecutionResult
    
    def get_text_content(self) -> str:
        r = self.result
        status = "✅ PASSED" if r.success else "❌ FAILED"
        
        output = f"""
TEST EXECUTION RESULTS {status}
=======================
Total Tests: {r.total_tests}
Passed: {r.passed} ✅
Failed: {r.failed} ❌
Skipped: {r.skipped} ⏭️

Command: {r.command_used}

Test Details:
"""
        for test in r.test_results[:10]:  # Show first 10 tests
            icon = {"passed": "✅", "failed": "❌", "skipped": "⏭️"}.get(test.status, "❓")
            output += f"  {icon} {test.name}\n"
            if test.message:
                output += f"     {test.message}\n"
        
        if len(r.test_results) > 10:
            output += f"  ... and {len(r.test_results) - 10} more tests\n"
            
        return output
    
    def is_empty(self) -> bool:
        return False

class TestRunnerTool(Tool[TestExecutionInput, ToolRunOptions, TestExecutionOutput]):
    """Tool that executes tests in a project"""
    name = "TestRunner"
    description = "Execute tests in a project and report results"
    input_schema = TestExecutionInput
    
    async def _run(
        self, input: TestExecutionInput, options: ToolRunOptions | None, context: RunContext
    ) -> TestExecutionOutput:
        """Execute tests and parse results"""
        project_path = Path(input.project_path)
        
        if not project_path.exists():
            raise ValueError(f"Project path does not exist: {project_path}")
        
        # Detect test framework and command
        test_command = input.test_command
        if not test_command:
            test_command = self._detect_test_command(project_path)
        
        # Execute tests
        result = await self._execute_tests(project_path, test_command)
        
        return TestExecutionOutput(result=result)
    
    def _detect_test_command(self, project_path: Path) -> str:
        """Detect the appropriate test command based on project type"""
        # Check for Node.js project
        package_json = project_path / "package.json"
        if package_json.exists():
            with open(package_json) as f:
                data = json.load(f)
                scripts = data.get("scripts", {})
                if "test" in scripts:
                    return "npm test"
                elif "jest" in data.get("devDependencies", {}):
                    return "npx jest"
                elif "mocha" in data.get("devDependencies", {}):
                    return "npx mocha"
        
        # Check for Python project
        if (project_path / "pytest.ini").exists() or (project_path / "tests").exists():
            return "pytest"
        elif (project_path / "test_*.py").exists():
            return "python -m unittest discover"
        
        # Check for requirements.txt
        requirements = project_path / "requirements.txt"
        if requirements.exists():
            with open(requirements) as f:
                content = f.read()
                if "pytest" in content:
                    return "pytest"
                elif "unittest" in content:
                    return "python -m unittest discover"
        
        # Default fallback
        return "npm test"  # Most common in web projects
    
    async def _execute_tests(self, project_path: Path, command: str) -> TestExecutionResult:
        """Execute the test command and parse results"""
        try:
            # Run tests
            process = subprocess.run(
                command.split(),
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            output = process.stdout + "\n" + process.stderr
            success = process.returncode == 0
            
            # Parse test results (simplified - in reality would parse specific formats)
            test_results = self._parse_test_output(output, command)
            
            passed = sum(1 for t in test_results if t.status == "passed")
            failed = sum(1 for t in test_results if t.status == "failed")
            skipped = sum(1 for t in test_results if t.status == "skipped")
            
            return TestExecutionResult(
                total_tests=len(test_results),
                passed=passed,
                failed=failed,
                skipped=skipped,
                success=success,
                test_results=test_results,
                output=output[:2000],  # Truncate long output
                command_used=command
            )
            
        except subprocess.TimeoutExpired:
            return TestExecutionResult(
                total_tests=0,
                passed=0,
                failed=0,
                skipped=0,
                success=False,
                test_results=[],
                output="Test execution timed out after 5 minutes",
                command_used=command
            )
        except Exception as e:
            return TestExecutionResult(
                total_tests=0,
                passed=0,
                failed=0,
                skipped=0,
                success=False,
                test_results=[],
                output=f"Error executing tests: {str(e)}",
                command_used=command
            )
    
    def _parse_test_output(self, output: str, command: str) -> List[TestResult]:
        """Parse test output to extract individual test results"""
        results = []
        
        # Simple parsing - in reality would use framework-specific parsers
        if "jest" in command or "mocha" in command:
            # Parse Jest/Mocha output
            for line in output.split('\n'):
                if "✓" in line or "✔" in line:
                    results.append(TestResult(
                        name=line.strip().replace("✓", "").replace("✔", "").strip(),
                        status="passed"
                    ))
                elif "✗" in line or "✖" in line:
                    results.append(TestResult(
                        name=line.strip().replace("✗", "").replace("✖", "").strip(),
                        status="failed"
                    ))
        elif "pytest" in command:
            # Parse pytest output
            for line in output.split('\n'):
                if "PASSED" in line:
                    results.append(TestResult(
                        name=line.split("::")[0] if "::" in line else "test",
                        status="passed"
                    ))
                elif "FAILED" in line:
                    results.append(TestResult(
                        name=line.split("::")[0] if "::" in line else "test",
                        status="failed"
                    ))
        
        # If no specific parsing worked, do generic parsing
        if not results:
            if "test" in output.lower() and ("pass" in output.lower() or "ok" in output.lower()):
                results.append(TestResult(name="Tests", status="passed"))
            elif "fail" in output.lower() or "error" in output.lower():
                results.append(TestResult(name="Tests", status="failed"))
        
        return results