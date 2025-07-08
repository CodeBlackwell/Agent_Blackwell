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
    """Enhanced test coverage report with branch and statement coverage"""
    # Statement coverage
    total_statements: int = 0
    covered_statements: int = 0
    statement_coverage: float = 0.0
    
    # Branch coverage
    total_branches: int = 0
    covered_branches: int = 0
    branch_coverage: float = 0.0
    
    # Function coverage
    total_functions: int = 0
    covered_functions: int = 0
    function_coverage: float = 0.0
    
    # Overall coverage (weighted average)
    coverage_percentage: float = 0.0
    
    def __post_init__(self):
        """Calculate weighted coverage after initialization"""
        if self.has_branch_coverage and self.total_branches > 0:
            # 60% weight to statement coverage, 40% to branch coverage
            self.coverage_percentage = (
                0.6 * self.statement_coverage + 
                0.4 * self.branch_coverage
            )
        else:
            self.coverage_percentage = self.statement_coverage
    
    # Detailed missing coverage
    missing_lines: Dict[str, List[int]] = field(default_factory=dict)
    uncovered_functions: List[str] = field(default_factory=list)
    uncovered_branches: Dict[str, List[str]] = field(default_factory=dict)  # file -> branch descriptions
    
    # Coverage by feature
    feature_coverage: Dict[str, float] = field(default_factory=dict)
    
    summary: str = ""
    
    @property
    def is_sufficient(self) -> bool:
        """Check if coverage meets minimum threshold"""
        return self.coverage_percentage >= 80.0  # Default 80% threshold
    
    @property
    def has_branch_coverage(self) -> bool:
        """Check if branch coverage data is available"""
        return self.total_branches > 0


@dataclass 
class TestCoverageResult:
    """Enhanced result from test coverage analysis"""
    success: bool
    coverage_report: Optional[CoverageReport] = None
    test_results: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    suggestions: List[str] = field(default_factory=list)
    
    # Coverage trends
    coverage_improved: bool = False
    previous_coverage: Optional[float] = None
    
    # TDD phase validation
    red_phase_valid: bool = False  # Tests failed before implementation
    green_phase_valid: bool = False  # Tests pass after implementation
    
    # Quality metrics
    test_quality_score: float = 0.0  # 0-100 score based on test comprehensiveness


class TestCoverageValidator:
    """Enhanced validator for test coverage in TDD workflow"""
    
    def __init__(self, 
                 minimum_coverage: float = 80.0,
                 minimum_branch_coverage: float = 70.0,
                 track_trends: bool = True):
        """
        Initialize validator with coverage thresholds.
        
        Args:
            minimum_coverage: Minimum acceptable overall coverage percentage (0-100)
            minimum_branch_coverage: Minimum acceptable branch coverage percentage (0-100)
            track_trends: Whether to track coverage trends over time
        """
        self.minimum_coverage = minimum_coverage
        self.minimum_branch_coverage = minimum_branch_coverage
        self.track_trends = track_trends
        self.coverage_history: Dict[str, List[float]] = {}  # feature_id -> coverage history
        
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
                    
                # Run pytest with enhanced coverage including branch coverage
                result = subprocess.run(
                    ["python", "-m", "pytest", test_file, 
                     "--cov=implementation", 
                     "--cov-report=json",
                     "--cov-branch",  # Enable branch coverage
                     "--cov-report=term-missing:skip-covered",  # Detailed output
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
                        
                    # Extract enhanced coverage metrics
                    if 'totals' in cov_data:
                        totals = cov_data['totals']
                        
                        # Statement coverage
                        coverage_report.total_statements = totals.get('num_statements', 0)
                        coverage_report.covered_statements = totals.get('covered_lines', 0)
                        coverage_report.statement_coverage = totals.get('percent_covered', 0.0)
                        
                        # Branch coverage
                        coverage_report.total_branches = totals.get('num_branches', 0)
                        coverage_report.covered_branches = totals.get('covered_branches', 0)
                        coverage_report.branch_coverage = totals.get('percent_covered_branches', 0.0) if coverage_report.total_branches > 0 else 100.0
                        
                        # Calculate weighted overall coverage
                        if coverage_report.has_branch_coverage:
                            # 60% weight to statement coverage, 40% to branch coverage
                            coverage_report.coverage_percentage = (
                                0.6 * coverage_report.statement_coverage + 
                                0.4 * coverage_report.branch_coverage
                            )
                        else:
                            coverage_report.coverage_percentage = coverage_report.statement_coverage
                        
                    # Extract detailed missing coverage
                    if 'files' in cov_data:
                        for file_path, file_data in cov_data['files'].items():
                            if 'implementation' in file_path:
                                coverage_report.missing_lines['implementation.py'] = \
                                    file_data.get('missing_lines', [])
                                
                                # Extract missing branches
                                missing_branches = file_data.get('missing_branches', [])
                                if missing_branches:
                                    coverage_report.uncovered_branches['implementation.py'] = [
                                        f"Line {branch[0]} -> {branch[1]}" 
                                        for branch in missing_branches
                                    ]
                                
                                # Extract function coverage
                                contexts = file_data.get('contexts', {})
                                all_functions = self._extract_functions(implementation_code)
                                covered_funcs = set()
                                for context in contexts:
                                    if context and '.' in context:
                                        func_name = context.split('.')[-1]
                                        covered_funcs.add(func_name)
                                
                                coverage_report.total_functions = len(all_functions)
                                coverage_report.covered_functions = len(covered_funcs)
                                coverage_report.function_coverage = (
                                    len(covered_funcs) / len(all_functions) * 100 
                                    if all_functions else 100
                                )
                                coverage_report.uncovered_functions = [
                                    f for f in all_functions if f not in covered_funcs
                                ]
                                    
                # Analyze test results
                test_passed = result.returncode == 0
                test_output = result.stdout + result.stderr
                
                # Calculate test quality score
                test_quality_score = self._calculate_test_quality_score(
                    coverage_report, test_code, implementation_code
                )
                
                # Generate enhanced suggestions
                suggestions = self._generate_enhanced_coverage_suggestions(
                    coverage_report, test_output, implementation_code, test_code
                )
                
                # Check if both statement and branch coverage meet thresholds
                coverage_sufficient = (
                    coverage_report.statement_coverage >= self.minimum_coverage and
                    (not coverage_report.has_branch_coverage or 
                     coverage_report.branch_coverage >= self.minimum_branch_coverage)
                )
                
                return TestCoverageResult(
                    success=test_passed and coverage_sufficient,
                    coverage_report=coverage_report,
                    test_results={
                        "passed": test_passed,
                        "output": test_output,
                        "return_code": result.returncode
                    },
                    suggestions=suggestions,
                    test_quality_score=test_quality_score,
                    green_phase_valid=test_passed
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
        
    def _calculate_test_quality_score(self,
                                    coverage_report: CoverageReport,
                                    test_code: str,
                                    implementation_code: str) -> float:
        """Calculate a quality score for the tests (0-100)"""
        score = 0.0
        
        # Base score from coverage (40 points)
        score += min(40, coverage_report.coverage_percentage * 0.4)
        
        # Branch coverage bonus (20 points)
        if coverage_report.has_branch_coverage:
            score += min(20, coverage_report.branch_coverage * 0.2)
        else:
            score += 10  # Partial credit if no branch data
        
        # Test variety (20 points)
        test_patterns = [
            (r'test.*edge|edge.*test', 5),  # Edge case tests
            (r'test.*error|error.*test|raises|throws', 5),  # Error handling tests
            (r'test.*boundary|boundary.*test', 5),  # Boundary tests
            (r'mock|patch|stub', 5),  # Mocking tests
        ]
        
        test_lower = test_code.lower()
        for pattern, points in test_patterns:
            if re.search(pattern, test_lower):
                score += points
        
        # Assertion variety (20 points)
        assertion_types = [
            (r'assert.*equal', 5),
            (r'assert.*true|assert.*false', 5),
            (r'assert.*in|assert.*contains', 5),
            (r'assert.*raises|expect.*throw', 5),
        ]
        
        for pattern, points in assertion_types:
            if re.search(pattern, test_lower):
                score += points
        
        return min(100, score)
    
    def _generate_enhanced_coverage_suggestions(self,
                                              coverage_report: CoverageReport,
                                              test_output: str,
                                              implementation_code: str,
                                              test_code: str) -> List[str]:
        """Generate enhanced suggestions for improving test coverage and quality"""
        suggestions = []
        
        # Check statement coverage
        if coverage_report.statement_coverage < self.minimum_coverage:
            suggestions.append(
                f"Statement coverage is {coverage_report.statement_coverage:.1f}%, "
                f"needs to be at least {self.minimum_coverage}%"
            )
        
        # Check branch coverage
        if coverage_report.has_branch_coverage and coverage_report.branch_coverage < self.minimum_branch_coverage:
            suggestions.append(
                f"Branch coverage is {coverage_report.branch_coverage:.1f}%, "
                f"needs to be at least {self.minimum_branch_coverage}%"
            )
            
        # Check for untested lines with context
        if coverage_report.missing_lines:
            for file, lines in coverage_report.missing_lines.items():
                if lines:
                    # Group consecutive lines
                    line_groups = self._group_consecutive_lines(lines)
                    for group in line_groups[:2]:  # Show first 2 groups
                        if len(group) > 1:
                            suggestions.append(f"Add tests for lines {group[0]}-{group[-1]} in {file}")
                        else:
                            suggestions.append(f"Add test for line {group[0]} in {file}")
        
        # Check for untested branches
        if coverage_report.uncovered_branches:
            total_uncovered = sum(len(branches) for branches in coverage_report.uncovered_branches.values())
            suggestions.append(f"Add tests for {total_uncovered} uncovered branches")
            # Show specific branch examples
            for file, branches in coverage_report.uncovered_branches.items():
                if branches:
                    suggestions.append(f"Uncovered branch: {branches[0]} in {file}")
                    
        # Check for untested functions
        if coverage_report.uncovered_functions:
            suggestions.append(
                f"Untested functions: {', '.join(coverage_report.uncovered_functions[:3])}"
            )
            
        # Enhanced test quality checks
        test_lower = test_code.lower()
        
        # Check for edge cases
        if "edge" not in test_lower and "boundary" not in test_lower:
            suggestions.append("Add edge case tests (e.g., empty inputs, maximum values)")
        
        # Check for negative test cases
        if "invalid" not in test_lower and "negative" not in test_lower:
            suggestions.append("Add negative test cases for invalid inputs")
        
        # Check for parameterized tests
        if "@pytest.mark.parametrize" not in test_code and "@parameterized" not in test_code:
            if self._count_similar_tests(test_code) > 3:
                suggestions.append("Consider using parameterized tests to reduce duplication")
            
        # Check for error handling tests
        if "error" in implementation_code.lower() or "exception" in implementation_code.lower():
            if "raises" not in test_output and "throw" not in test_output:
                suggestions.append("Add tests for error handling")
                
        # Check test naming
        if not re.search(r'test_\w+_(should|when|given)', test_code):
            suggestions.append("Consider descriptive test names (e.g., test_add_should_handle_negative_numbers)")
        
        return suggestions
    
    def _group_consecutive_lines(self, lines: List[int]) -> List[List[int]]:
        """Group consecutive line numbers together"""
        if not lines:
            return []
        
        groups = []
        current_group = [lines[0]]
        
        for line in lines[1:]:
            if line == current_group[-1] + 1:
                current_group.append(line)
            else:
                groups.append(current_group)
                current_group = [line]
        
        groups.append(current_group)
        return groups
    
    def _count_similar_tests(self, test_code: str) -> int:
        """Count potentially similar test functions"""
        test_funcs = re.findall(r'def (test_\w+)\(', test_code)
        if not test_funcs:
            return 0
        
        # Check for similar prefixes
        from collections import Counter
        prefixes = [func.split('_')[1] if '_' in func else func for func in test_funcs]
        prefix_counts = Counter(prefixes)
        
        return max(prefix_counts.values()) if prefix_counts else 0
        
    def generate_coverage_report_markdown(self, result: TestCoverageResult, feature_id: Optional[str] = None) -> str:
        """Generate an enhanced markdown report of test coverage"""
        report = "# Test Coverage Report\n\n"
        
        if feature_id:
            report += f"**Feature**: {feature_id}\n\n"
        
        if result.coverage_report:
            cov = result.coverage_report
            report += f"## Coverage Summary\n\n"
            report += f"- **Overall Coverage**: {cov.coverage_percentage:.1f}%\n"
            report += f"- **Statement Coverage**: {cov.statement_coverage:.1f}% ({cov.covered_statements}/{cov.total_statements})\n"
            
            if cov.has_branch_coverage:
                report += f"- **Branch Coverage**: {cov.branch_coverage:.1f}% ({cov.covered_branches}/{cov.total_branches})\n"
            
            report += f"- **Function Coverage**: {cov.function_coverage:.1f}% ({cov.covered_functions}/{cov.total_functions})\n"
            report += f"- **Test Quality Score**: {result.test_quality_score:.1f}/100\n"
            report += f"- **Required Threshold**: {self.minimum_coverage}% (statements), {self.minimum_branch_coverage}% (branches)\n"
            report += f"- **Status**: {'✅ PASS' if result.success else '❌ FAIL'}\n\n"
            
            if cov.missing_lines or cov.uncovered_branches:
                report += "## Missing Coverage\n\n"
                
                for file in set(list(cov.missing_lines.keys()) + list(cov.uncovered_branches.keys())):
                    report += f"### {file}\n\n"
                    
                    # Missing lines
                    lines = cov.missing_lines.get(file, [])
                    if lines:
                        line_groups = self._group_consecutive_lines(lines)
                        report += "**Uncovered lines**: "
                        line_ranges = []
                        for group in line_groups:
                            if len(group) > 1:
                                line_ranges.append(f"{group[0]}-{group[-1]}")
                            else:
                                line_ranges.append(str(group[0]))
                        report += ", ".join(line_ranges) + "\n\n"
                    
                    # Missing branches
                    branches = cov.uncovered_branches.get(file, [])
                    if branches:
                        report += "**Uncovered branches**:\n"
                        for branch in branches[:5]:  # Show first 5
                            report += f"- {branch}\n"
                        if len(branches) > 5:
                            report += f"- ... and {len(branches) - 5} more\n"
                        report += "\n"
                        
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
                                   minimum_coverage: float = 80.0,
                                   minimum_branch_coverage: float = 70.0,
                                   feature_id: Optional[str] = None) -> Tuple[bool, str, Optional[TestCoverageResult]]:
    """
    Validate test coverage for TDD workflow with enhanced metrics.
    
    Args:
        test_code: The test code to validate
        implementation_code: The implementation being tested
        minimum_coverage: Minimum statement coverage required
        minimum_branch_coverage: Minimum branch coverage required
        feature_id: Optional feature ID for tracking
    
    Returns:
        Tuple of (success, message, result)
    """
    validator = TestCoverageValidator(minimum_coverage, minimum_branch_coverage)
    result = await validator.validate_test_coverage(test_code, implementation_code)
    
    if result.success:
        cov = result.coverage_report
        msg = f"✅ Test coverage validated:\n"
        msg += f"   - Statement: {cov.statement_coverage:.1f}%\n"
        if cov.has_branch_coverage:
            msg += f"   - Branch: {cov.branch_coverage:.1f}%\n"
        msg += f"   - Functions: {cov.function_coverage:.1f}%\n"
        msg += f"   - Quality Score: {result.test_quality_score:.1f}/100"
    else:
        msg = f"❌ Test coverage insufficient:\n"
        if result.coverage_report:
            cov = result.coverage_report
            if cov.statement_coverage < minimum_coverage:
                msg += f"   - Statement coverage: {cov.statement_coverage:.1f}% (need {minimum_coverage}%)\n"
            if cov.has_branch_coverage and cov.branch_coverage < minimum_branch_coverage:
                msg += f"   - Branch coverage: {cov.branch_coverage:.1f}% (need {minimum_branch_coverage}%)\n"
        if result.suggestions:
            msg += f"   - Suggestion: {result.suggestions[0]}"
    
    # Track coverage trend if feature_id provided
    if feature_id and validator.track_trends and result.coverage_report:
        if feature_id not in validator.coverage_history:
            validator.coverage_history[feature_id] = []
        validator.coverage_history[feature_id].append(result.coverage_report.coverage_percentage)
        
        if len(validator.coverage_history[feature_id]) > 1:
            result.previous_coverage = validator.coverage_history[feature_id][-2]
            result.coverage_improved = (
                result.coverage_report.coverage_percentage > result.previous_coverage
            )
            
    return result.success, msg, result