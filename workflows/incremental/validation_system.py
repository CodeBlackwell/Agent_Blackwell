"""
Enhanced validation system with granular progress metrics for incremental development.
"""
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import re
import ast
from collections import defaultdict


class ValidationLevel(Enum):
    """Levels of validation granularity."""
    SYNTAX = "syntax"
    IMPORTS = "imports"
    STRUCTURE = "structure"
    FUNCTIONALITY = "functionality"
    TESTS = "tests"
    INTEGRATION = "integration"


class TestGranularity(Enum):
    """Granularity levels for test execution."""
    FILE = "file"
    CLASS = "class"
    METHOD = "method"
    ASSERTION = "assertion"


@dataclass
class ValidationCheckpoint:
    """Represents a validation checkpoint with progress information."""
    level: ValidationLevel
    passed: bool
    details: str
    timestamp: datetime = field(default_factory=datetime.now)
    sub_checks: List[Tuple[str, bool]] = field(default_factory=list)
    
    def get_progress_percentage(self) -> float:
        """Calculate progress percentage for this checkpoint."""
        if not self.sub_checks:
            return 100.0 if self.passed else 0.0
        
        passed_count = sum(1 for _, passed in self.sub_checks if passed)
        return (passed_count / len(self.sub_checks)) * 100.0


@dataclass
class TestProgress:
    """Tracks granular test execution progress."""
    test_file: str
    total_tests: int = 0
    executed_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    skipped_tests: int = 0
    test_details: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    def add_test_result(self, test_name: str, passed: bool, duration: float = 0.0, 
                       error: Optional[str] = None):
        """Record a test result."""
        self.executed_tests += 1
        if passed:
            self.passed_tests += 1
        else:
            self.failed_tests += 1
        
        self.test_details[test_name] = {
            "passed": passed,
            "duration": duration,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_pass_rate(self) -> float:
        """Get test pass rate."""
        if self.executed_tests == 0:
            return 0.0
        return (self.passed_tests / self.executed_tests) * 100.0
    
    def get_execution_rate(self) -> float:
        """Get test execution rate."""
        if self.total_tests == 0:
            return 0.0
        return (self.executed_tests / self.total_tests) * 100.0


@dataclass
class FeatureValidationProgress:
    """Comprehensive validation progress for a feature."""
    feature_id: str
    checkpoints: List[ValidationCheckpoint] = field(default_factory=list)
    test_progress: Dict[str, TestProgress] = field(default_factory=dict)
    partial_implementations: Dict[str, float] = field(default_factory=dict)
    integration_status: Dict[str, bool] = field(default_factory=dict)
    
    def add_checkpoint(self, level: ValidationLevel, passed: bool, details: str,
                      sub_checks: Optional[List[Tuple[str, bool]]] = None):
        """Add a validation checkpoint."""
        checkpoint = ValidationCheckpoint(
            level=level,
            passed=passed,
            details=details,
            sub_checks=sub_checks or []
        )
        self.checkpoints.append(checkpoint)
    
    def get_overall_progress(self) -> float:
        """Calculate overall validation progress."""
        if not self.checkpoints:
            return 0.0
        
        # Weight different validation levels
        weights = {
            ValidationLevel.SYNTAX: 0.1,
            ValidationLevel.IMPORTS: 0.1,
            ValidationLevel.STRUCTURE: 0.15,
            ValidationLevel.FUNCTIONALITY: 0.25,
            ValidationLevel.TESTS: 0.25,
            ValidationLevel.INTEGRATION: 0.15
        }
        
        total_weight = 0.0
        weighted_progress = 0.0
        
        for checkpoint in self.checkpoints:
            weight = weights.get(checkpoint.level, 0.1)
            progress = checkpoint.get_progress_percentage()
            weighted_progress += weight * progress
            total_weight += weight
        
        if total_weight > 0:
            return weighted_progress / total_weight
        return 0.0
    
    def get_blocking_issues(self) -> List[str]:
        """Get list of blocking issues preventing progress."""
        blocking = []
        
        # Check for syntax errors (always blocking)
        syntax_checks = [c for c in self.checkpoints if c.level == ValidationLevel.SYNTAX]
        if syntax_checks and not all(c.passed for c in syntax_checks):
            blocking.append("Syntax errors must be fixed")
        
        # Check for import errors (usually blocking)
        import_checks = [c for c in self.checkpoints if c.level == ValidationLevel.IMPORTS]
        if import_checks and not all(c.passed for c in import_checks):
            blocking.append("Import/dependency errors must be resolved")
        
        # Check for critical test failures
        if self.test_progress:
            critical_failures = []
            for test_file, progress in self.test_progress.items():
                if progress.get_pass_rate() < 20:  # Less than 20% passing
                    critical_failures.append(test_file)
            
            if critical_failures:
                blocking.append(f"Critical test failures in: {', '.join(critical_failures)}")
        
        return blocking


class GranularValidator:
    """
    Enhanced validator that provides granular progress tracking and partial success metrics.
    """
    
    def __init__(self):
        self.validation_history: Dict[str, List[FeatureValidationProgress]] = defaultdict(list)
    
    def validate_syntax(self, code: str, filename: str) -> ValidationCheckpoint:
        """Validate Python syntax with detailed feedback."""
        sub_checks = []
        
        try:
            # Try to parse the code
            tree = ast.parse(code, filename=filename)
            sub_checks.append(("Basic syntax parsing", True))
            
            # Check for common syntax patterns
            has_functions = any(isinstance(node, ast.FunctionDef) for node in ast.walk(tree))
            has_classes = any(isinstance(node, ast.ClassDef) for node in ast.walk(tree))
            
            if filename.endswith('.py') and not filename.endswith('__init__.py'):
                if not has_functions and not has_classes:
                    sub_checks.append(("Contains code structure", False))
                else:
                    sub_checks.append(("Contains code structure", True))
            
            return ValidationCheckpoint(
                level=ValidationLevel.SYNTAX,
                passed=True,
                details="Syntax validation passed",
                sub_checks=sub_checks
            )
            
        except SyntaxError as e:
            return ValidationCheckpoint(
                level=ValidationLevel.SYNTAX,
                passed=False,
                details=f"Syntax error at line {e.lineno}: {e.msg}",
                sub_checks=[("Basic syntax parsing", False)]
            )
        except Exception as e:
            return ValidationCheckpoint(
                level=ValidationLevel.SYNTAX,
                passed=False,
                details=f"Validation error: {str(e)}",
                sub_checks=[("Basic syntax parsing", False)]
            )
    
    def validate_imports(self, code: str, available_modules: Set[str]) -> ValidationCheckpoint:
        """Validate imports and dependencies."""
        sub_checks = []
        issues = []
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module_name = alias.name.split('.')[0]
                        if module_name in available_modules or module_name in {'os', 'sys', 'json', 're'}:
                            sub_checks.append((f"Import {module_name}", True))
                        else:
                            sub_checks.append((f"Import {module_name}", False))
                            issues.append(f"Missing module: {module_name}")
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        module_name = node.module.split('.')[0]
                        if module_name in available_modules or module_name in {'os', 'sys', 'json', 're'}:
                            sub_checks.append((f"Import from {module_name}", True))
                        else:
                            sub_checks.append((f"Import from {module_name}", False))
                            issues.append(f"Missing module: {module_name}")
            
            passed = all(check[1] for check in sub_checks) if sub_checks else True
            details = "All imports validated" if passed else f"Import issues: {', '.join(issues)}"
            
            return ValidationCheckpoint(
                level=ValidationLevel.IMPORTS,
                passed=passed,
                details=details,
                sub_checks=sub_checks
            )
            
        except Exception as e:
            return ValidationCheckpoint(
                level=ValidationLevel.IMPORTS,
                passed=False,
                details=f"Import validation error: {str(e)}",
                sub_checks=[]
            )
    
    def validate_structure(self, code: str, expected_components: List[str]) -> ValidationCheckpoint:
        """Validate code structure against expected components."""
        sub_checks = []
        
        try:
            tree = ast.parse(code)
            
            # Extract defined components
            defined_functions = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
            defined_classes = {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
            defined_components = defined_functions | defined_classes
            
            # Check expected components
            for component in expected_components:
                found = component in defined_components
                sub_checks.append((f"Component '{component}'", found))
            
            # Additional structure checks
            has_docstrings = any(
                ast.get_docstring(node) for node in ast.walk(tree)
                if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module))
            )
            sub_checks.append(("Has docstrings", has_docstrings))
            
            passed = all(check[1] for check in sub_checks if check[0].startswith("Component"))
            missing = [check[0].replace("Component '", "").rstrip("'") 
                      for check in sub_checks 
                      if check[0].startswith("Component") and not check[1]]
            
            details = "All expected components found" if passed else f"Missing: {', '.join(missing)}"
            
            return ValidationCheckpoint(
                level=ValidationLevel.STRUCTURE,
                passed=passed,
                details=details,
                sub_checks=sub_checks
            )
            
        except Exception as e:
            return ValidationCheckpoint(
                level=ValidationLevel.STRUCTURE,
                passed=False,
                details=f"Structure validation error: {str(e)}",
                sub_checks=[]
            )
    
    def parse_test_output(self, test_output: str) -> Dict[str, TestProgress]:
        """Parse test output to extract granular test results."""
        test_files = defaultdict(lambda: TestProgress(test_file=""))
        
        # Pattern for pytest output
        test_pattern = re.compile(r'(test_\w+\.py)::(test_\w+)\s+(\w+)')
        summary_pattern = re.compile(r'(\d+) passed(?:,\s*(\d+) failed)?(?:,\s*(\d+) skipped)?')
        
        for match in test_pattern.finditer(test_output):
            file_name = match.group(1)
            test_name = match.group(2)
            result = match.group(3).lower()
            
            if file_name not in test_files:
                test_files[file_name].test_file = file_name
            
            test_files[file_name].total_tests += 1
            test_files[file_name].add_test_result(
                test_name=test_name,
                passed=(result == "passed"),
                error=None if result == "passed" else f"Test {result}"
            )
        
        # Parse summary if available
        summary_match = summary_pattern.search(test_output)
        if summary_match:
            passed = int(summary_match.group(1) or 0)
            failed = int(summary_match.group(2) or 0)
            skipped = int(summary_match.group(3) or 0)
            
            # If we don't have detailed results, create a summary entry
            if not test_files:
                summary_progress = TestProgress(test_file="all_tests")
                summary_progress.total_tests = passed + failed + skipped
                summary_progress.executed_tests = passed + failed
                summary_progress.passed_tests = passed
                summary_progress.failed_tests = failed
                summary_progress.skipped_tests = skipped
                test_files["all_tests"] = summary_progress
        
        return dict(test_files)
    
    def create_validation_report(self, 
                               feature_id: str,
                               code_files: Dict[str, str],
                               test_output: Optional[str] = None,
                               expected_components: Optional[Dict[str, List[str]]] = None) -> FeatureValidationProgress:
        """Create a comprehensive validation report for a feature."""
        progress = FeatureValidationProgress(feature_id=feature_id)
        
        # Validate each file
        for filename, code in code_files.items():
            # Syntax validation
            syntax_checkpoint = self.validate_syntax(code, filename)
            progress.add_checkpoint(
                syntax_checkpoint.level,
                syntax_checkpoint.passed,
                f"{filename}: {syntax_checkpoint.details}",
                syntax_checkpoint.sub_checks
            )
            
            # Only continue if syntax is valid
            if syntax_checkpoint.passed:
                # Import validation
                available_modules = set(code_files.keys())
                import_checkpoint = self.validate_imports(code, available_modules)
                progress.add_checkpoint(
                    import_checkpoint.level,
                    import_checkpoint.passed,
                    f"{filename}: {import_checkpoint.details}",
                    import_checkpoint.sub_checks
                )
                
                # Structure validation if expected components provided
                if expected_components and filename in expected_components:
                    structure_checkpoint = self.validate_structure(
                        code, 
                        expected_components[filename]
                    )
                    progress.add_checkpoint(
                        structure_checkpoint.level,
                        structure_checkpoint.passed,
                        f"{filename}: {structure_checkpoint.details}",
                        structure_checkpoint.sub_checks
                    )
        
        # Test validation if output provided
        if test_output:
            test_results = self.parse_test_output(test_output)
            progress.test_progress = test_results
            
            # Create test checkpoint
            total_tests = sum(p.total_tests for p in test_results.values())
            passed_tests = sum(p.passed_tests for p in test_results.values())
            
            test_sub_checks = [
                (f"{file}: {p.passed_tests}/{p.total_tests} passed", 
                 p.get_pass_rate() >= 80)
                for file, p in test_results.items()
            ]
            
            progress.add_checkpoint(
                ValidationLevel.TESTS,
                all(p.get_pass_rate() >= 80 for p in test_results.values()),
                f"{passed_tests}/{total_tests} tests passed",
                test_sub_checks
            )
        
        # Store in history
        self.validation_history[feature_id].append(progress)
        
        return progress
    
    def get_improvement_suggestions(self, feature_id: str) -> List[str]:
        """Get specific improvement suggestions based on validation history."""
        if feature_id not in self.validation_history:
            return []
        
        suggestions = []
        latest = self.validation_history[feature_id][-1]
        
        # Analyze checkpoints
        failed_levels = defaultdict(list)
        for checkpoint in latest.checkpoints:
            if not checkpoint.passed:
                failed_levels[checkpoint.level].append(checkpoint.details)
        
        # Generate suggestions
        if ValidationLevel.SYNTAX in failed_levels:
            suggestions.append("Fix syntax errors first - check error messages for line numbers")
        
        if ValidationLevel.IMPORTS in failed_levels:
            suggestions.append("Ensure all dependencies are properly imported or implemented")
        
        if ValidationLevel.STRUCTURE in failed_levels:
            suggestions.append("Implement all required functions and classes as specified")
        
        if ValidationLevel.TESTS in failed_levels:
            # Analyze which tests are failing most
            if latest.test_progress:
                worst_files = sorted(
                    latest.test_progress.items(),
                    key=lambda x: x[1].get_pass_rate()
                )[:3]
                
                for file, progress in worst_files:
                    if progress.get_pass_rate() < 50:
                        suggestions.append(
                            f"Focus on fixing tests in {file} "
                            f"({progress.failed_tests} failures)"
                        )
        
        # Check for partial implementations
        if latest.partial_implementations:
            incomplete = [name for name, pct in latest.partial_implementations.items() if pct < 80]
            if incomplete:
                suggestions.append(f"Complete implementations for: {', '.join(incomplete)}")
        
        return suggestions