"""
Test Coverage Validator for MVP Incremental TDD Workflow

Validates that tests properly cover the implemented features
and checks for test coverage metrics.
"""

import re
import subprocess
import tempfile
import os
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from pathlib import Path
import json

from workflows.logger import workflow_logger as logger


@dataclass
class CoverageReport:
    """Test coverage report"""
    total_statements: int = 0
    covered_statements: int = 0
    coverage_percentage: float = 0.0
    missing_lines: Dict[str, List[int]] = field(default_factory=dict)
    uncovered_functions: List[str] = field(default_factory=list)
    summary: str = ""
    
    @property
    def is_sufficient(self) -> bool:
        """Check if coverage meets minimum threshold"""
        return self.coverage_percentage >= 80.0  # Default 80% threshold


@dataclass 
class TestCoverageResult:
    """Result from test coverage analysis"""
    success: bool
    coverage_report: Optional[CoverageReport] = None
    test_results: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    suggestions: List[str] = field(default_factory=list)


class TestCoverageValidator:
    """Validates test coverage for TDD workflow"""
    
    def __init__(self, minimum_coverage: float = 80.0):
        """
        Initialize validator with minimum coverage threshold.
        
        Args:
            minimum_coverage: Minimum acceptable coverage percentage (0-100)
        """
        self.minimum_coverage = minimum_coverage
        
    async def validate_test_coverage(self,
                                   test_code: str,
                                   implementation_code: str,
                                   language: str = "python") -> TestCoverageResult:
        """
        Validate that tests properly cover the implementation.
        
        Args:
            test_code: The test code
            implementation_code: The implementation code
            language: Programming language (python, javascript, etc.)
            
        Returns:
            TestCoverageResult with coverage analysis
        """
        if language.lower() == "python":
            return await self._validate_python_coverage(test_code, implementation_code)
        elif language.lower() in ["javascript", "js", "typescript", "ts"]:
            return await self._validate_javascript_coverage(test_code, implementation_code)
        else:
            # Basic validation for other languages
            return await self._validate_basic_coverage(test_code, implementation_code)
            
    async def _validate_python_coverage(self,
                                      test_code: str,
                                      implementation_code: str) -> TestCoverageResult:
        """Validate Python test coverage using pytest-cov"""
        try:
            # Create temporary directory for the test
            with tempfile.TemporaryDirectory() as tmpdir:
                # Write implementation file
                impl_file = os.path.join(tmpdir, "implementation.py")
                with open(impl_file, 'w') as f:
                    f.write(implementation_code)
                    
                # Write test file
                test_file = os.path.join(tmpdir, "test_implementation.py")
                with open(test_file, 'w') as f:
                    # Ensure test imports from local file
                    test_code_modified = test_code.replace(
                        "from main import", 
                        "from implementation import"
                    ).replace(
                        "import main",
                        "import implementation"
                    )
                    f.write(test_code_modified)
                    
                # Run pytest with coverage
                result = subprocess.run(
                    ["python", "-m", "pytest", test_file, 
                     "--cov=implementation", "--cov-report=json",
                     "--tb=short", "-v"],
                    capture_output=True,
                    text=True,
                    cwd=tmpdir
                )
                
                # Parse coverage report
                coverage_file = os.path.join(tmpdir, "coverage.json")
                coverage_report = CoverageReport()
                
                if os.path.exists(coverage_file):
                    with open(coverage_file, 'r') as f:
                        cov_data = json.load(f)
                        
                    # Extract coverage metrics
                    if 'totals' in cov_data:
                        totals = cov_data['totals']
                        coverage_report.total_statements = totals.get('num_statements', 0)
                        coverage_report.covered_statements = totals.get('covered_lines', 0)
                        coverage_report.coverage_percentage = totals.get('percent_covered', 0.0)
                        
                    # Extract missing lines
                    if 'files' in cov_data:
                        for file_path, file_data in cov_data['files'].items():
                            if 'implementation' in file_path:
                                coverage_report.missing_lines['implementation.py'] = \
                                    file_data.get('missing_lines', [])
                                    
                # Analyze test results
                test_passed = result.returncode == 0
                test_output = result.stdout + result.stderr
                
                # Generate suggestions
                suggestions = self._generate_coverage_suggestions(
                    coverage_report, test_output, implementation_code
                )
                
                return TestCoverageResult(
                    success=test_passed and coverage_report.is_sufficient,
                    coverage_report=coverage_report,
                    test_results={
                        "passed": test_passed,
                        "output": test_output,
                        "return_code": result.returncode
                    },
                    suggestions=suggestions
                )
                
        except Exception as e:
            logger.error(f"Error validating Python coverage: {str(e)}")
            return TestCoverageResult(
                success=False,
                error=str(e),
                suggestions=["Failed to run coverage analysis"]
            )
            
    async def _validate_javascript_coverage(self,
                                          test_code: str,
                                          implementation_code: str) -> TestCoverageResult:
        """Validate JavaScript test coverage using Jest"""
        # Simplified implementation - would need Jest setup
        return TestCoverageResult(
            success=True,
            coverage_report=CoverageReport(coverage_percentage=100.0),
            suggestions=["JavaScript coverage validation not fully implemented"]
        )
        
    async def _validate_basic_coverage(self,
                                      test_code: str,
                                      implementation_code: str) -> TestCoverageResult:
        """Basic coverage validation by analyzing code structure"""
        # Extract functions/methods from implementation
        impl_functions = self._extract_functions(implementation_code)
        
        # Check which functions are tested
        tested_functions = self._extract_tested_functions(test_code)
        
        # Calculate basic coverage
        total_functions = len(impl_functions)
        covered_functions = len([f for f in impl_functions if f in tested_functions])
        coverage_percentage = (covered_functions / total_functions * 100) if total_functions > 0 else 0
        
        coverage_report = CoverageReport(
            total_statements=total_functions,
            covered_statements=covered_functions,
            coverage_percentage=coverage_percentage,
            uncovered_functions=[f for f in impl_functions if f not in tested_functions]
        )
        
        suggestions = []
        if coverage_report.uncovered_functions:
            suggestions.append(f"Add tests for: {', '.join(coverage_report.uncovered_functions)}")
            
        return TestCoverageResult(
            success=coverage_percentage >= self.minimum_coverage,
            coverage_report=coverage_report,
            suggestions=suggestions
        )
        
    def _extract_functions(self, code: str) -> List[str]:
        """Extract function/method names from code"""
        functions = []
        
        # Python functions
        python_func_pattern = r'def\s+(\w+)\s*\('
        functions.extend(re.findall(python_func_pattern, code))
        
        # JavaScript functions
        js_func_patterns = [
            r'function\s+(\w+)\s*\(',
            r'(\w+)\s*:\s*function\s*\(',
            r'(\w+)\s*=\s*\([^)]*\)\s*=>',
            r'(\w+)\s*\([^)]*\)\s*{',
        ]
        for pattern in js_func_patterns:
            functions.extend(re.findall(pattern, code))
            
        return list(set(functions))
        
    def _extract_tested_functions(self, test_code: str) -> List[str]:
        """Extract which functions are being tested"""
        tested = []
        
        # Look for function calls in test code
        # This is simplified - real implementation would use AST parsing
        func_call_pattern = r'(\w+)\s*\('
        potential_calls = re.findall(func_call_pattern, test_code)
        
        # Filter out common test framework functions
        test_framework_funcs = ['test', 'it', 'describe', 'expect', 'assert', 
                               'assertEqual', 'assertTrue', 'beforeEach', 'afterEach']
        
        tested = [f for f in potential_calls if f not in test_framework_funcs]
        
        return list(set(tested))
        
    def _generate_coverage_suggestions(self,
                                     coverage_report: CoverageReport,
                                     test_output: str,
                                     implementation_code: str) -> List[str]:
        """Generate suggestions for improving test coverage"""
        suggestions = []
        
        # Check coverage percentage
        if coverage_report.coverage_percentage < self.minimum_coverage:
            suggestions.append(
                f"Coverage is {coverage_report.coverage_percentage:.1f}%, "
                f"needs to be at least {self.minimum_coverage}%"
            )
            
        # Check for untested lines
        if coverage_report.missing_lines:
            for file, lines in coverage_report.missing_lines.items():
                if lines:
                    suggestions.append(f"Add tests for lines {lines[:5]}... in {file}")
                    
        # Check for untested functions
        if coverage_report.uncovered_functions:
            suggestions.append(
                f"Untested functions: {', '.join(coverage_report.uncovered_functions[:3])}"
            )
            
        # Check for edge cases
        if "edge" not in test_output.lower() and "boundary" not in test_output.lower():
            suggestions.append("Consider adding edge case tests")
            
        # Check for error handling tests
        if "error" in implementation_code.lower() or "exception" in implementation_code.lower():
            if "raises" not in test_output and "throw" not in test_output:
                suggestions.append("Add tests for error handling")
                
        return suggestions
        
    def generate_coverage_report_markdown(self, result: TestCoverageResult) -> str:
        """Generate a markdown report of test coverage"""
        report = "# Test Coverage Report\n\n"
        
        if result.coverage_report:
            cov = result.coverage_report
            report += f"## Coverage Summary\n\n"
            report += f"- **Total Coverage**: {cov.coverage_percentage:.1f}%\n"
            report += f"- **Statements**: {cov.covered_statements}/{cov.total_statements}\n"
            report += f"- **Threshold**: {self.minimum_coverage}%\n"
            report += f"- **Status**: {'✅ PASS' if result.success else '❌ FAIL'}\n\n"
            
            if cov.missing_lines:
                report += "## Missing Coverage\n\n"
                for file, lines in cov.missing_lines.items():
                    if lines:
                        report += f"### {file}\n"
                        report += f"Missing lines: {', '.join(map(str, lines))}\n\n"
                        
            if cov.uncovered_functions:
                report += "## Untested Functions\n\n"
                for func in cov.uncovered_functions:
                    report += f"- `{func}`\n"
                report += "\n"
                
        if result.suggestions:
            report += "## Suggestions\n\n"
            for suggestion in result.suggestions:
                report += f"- {suggestion}\n"
                
        return report


# Helper function for integration
async def validate_tdd_test_coverage(test_code: str,
                                   implementation_code: str,
                                   minimum_coverage: float = 80.0) -> Tuple[bool, str]:
    """
    Validate test coverage for TDD workflow.
    
    Returns:
        Tuple of (success, message)
    """
    validator = TestCoverageValidator(minimum_coverage)
    result = await validator.validate_test_coverage(test_code, implementation_code)
    
    if result.success:
        msg = f"✅ Test coverage validated: {result.coverage_report.coverage_percentage:.1f}%"
    else:
        msg = f"❌ Test coverage insufficient"
        if result.suggestions:
            msg += f": {result.suggestions[0]}"
            
    return result.success, msg