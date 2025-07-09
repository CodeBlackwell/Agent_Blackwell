"""
RED Phase Orchestrator for MVP Incremental TDD Workflow

This module implements the RED phase of the TDD cycle where tests must fail first
before any implementation is allowed. It enforces test-first development by:
1. Running tests with failure expectation
2. Validating that tests actually fail
3. Extracting failure context for implementation guidance
4. Blocking progression if tests pass unexpectedly
"""

from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
import json
import re
from pathlib import Path
from datetime import datetime

from .tdd_phase_tracker import TDDPhase, TDDPhaseTracker
from .test_execution import TestExecutor
from .testable_feature_parser import TestableFeature


@dataclass
class TestFailureContext:
    """Captures context about test failures for implementation guidance"""
    test_file: str
    test_name: str
    failure_type: str  # e.g., "assertion", "import_error", "attribute_error"
    failure_message: str
    expected_value: Optional[str] = None
    actual_value: Optional[str] = None
    missing_component: Optional[str] = None  # For import/attribute errors
    line_number: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "test_file": self.test_file,
            "test_name": self.test_name,
            "failure_type": self.failure_type,
            "failure_message": self.failure_message,
            "expected_value": self.expected_value,
            "actual_value": self.actual_value,
            "missing_component": self.missing_component,
            "line_number": self.line_number
        }


class RedPhaseError(Exception):
    """Raised when RED phase validation fails"""
    pass


class RedPhaseOrchestrator:
    """
    Orchestrates the RED phase of TDD cycle
    
    Ensures tests fail before implementation is allowed and extracts
    failure context to guide the implementation phase.
    """
    
    def __init__(self, test_executor: TestExecutor, phase_tracker: TDDPhaseTracker):
        self.test_executor = test_executor
        self.phase_tracker = phase_tracker
        
    async def validate_red_phase(
        self, 
        feature: TestableFeature,
        test_file_path: str,
        project_root: str
    ) -> Tuple[bool, List[TestFailureContext]]:
        """
        Validate that we're in a proper RED phase (tests fail)
        
        Args:
            feature: The feature being implemented
            test_file_path: Path to the test file
            project_root: Root directory of the project
            
        Returns:
            Tuple of (is_valid_red_phase, failure_contexts)
            
        Raises:
            RedPhaseError: If validation fails unexpectedly
        """
        # Check current phase
        current_phase = self.phase_tracker.get_current_phase(feature.id)
        if current_phase != TDDPhase.RED:
            raise RedPhaseError(
                f"Feature '{feature.id}' is not in RED phase. Current phase: {current_phase}"
            )
        
        # Execute tests expecting failure
        result = await self.test_executor.execute_tests(
            code="",  # No implementation yet in RED phase
            feature_name=feature.title,
            test_files=[test_file_path],
            expect_failure=True
        )
        
        # Validate that tests actually failed
        if result.success and not result.expected_failure:
            # This is bad - tests should fail in RED phase
            raise RedPhaseError(
                f"Tests for feature '{feature.id}' passed unexpectedly in RED phase. "
                "Implementation may already exist or tests are not properly written."
            )
        
        # Extract failure context
        failure_contexts = self.extract_failure_context(result)
        
        if not failure_contexts:
            # Log the test output for debugging
            import logging
            logger = logging.getLogger("red_phase")
            logger.warning(f"Test output that couldn't be parsed:\n{result.output if hasattr(result, 'output') else 'No output'}")
            
            # For RED phase, if tests failed OR we expect failure, create a generic import error context
            # This handles cases where pytest fails to collect tests due to import errors
            if (hasattr(result, 'failed') and result.failed > 0) or \
               (hasattr(result, 'expected_failure') and result.expected_failure) or \
               (hasattr(result, 'errors') and result.errors):
                # Create a generic failure context for RED phase
                failure_contexts = [TestFailureContext(
                    test_file="test_feature.py",
                    test_name="import",
                    failure_type="import_error",
                    failure_message="Tests failed - likely due to missing implementation or import errors",
                    missing_component="main"
                )]
                logger.info("Created generic import error context for RED phase")
            else:
                # Only raise an error if tests actually passed when they shouldn't
                if hasattr(result, 'success') and result.success and not result.expected_failure:
                    raise RedPhaseError(
                        "Tests passed when they should have failed in RED phase. "
                        "Check that tests are properly written to fail without implementation."
                    )
                else:
                    # Create a fallback context for any other case
                    failure_contexts = [TestFailureContext(
                        test_file="test_feature.py",
                        test_name="unknown",
                        failure_type="collection_error",
                        failure_message="Test collection or execution failed - no implementation exists yet",
                        missing_component="implementation"
                    )]
        
        return True, failure_contexts
    
    def extract_failure_context(self, test_result: Dict[str, Any]) -> List[TestFailureContext]:
        """
        Extract detailed failure context from test results
        
        Args:
            test_result: Result from test executor
            
        Returns:
            List of failure contexts
        """
        failure_contexts = []
        output = test_result.output if hasattr(test_result, 'output') else ""
        
        # Parse pytest output for failures
        # Look for patterns like:
        # FAILED test_calculator.py::test_add - AssertionError: assert 0 == 5
        failed_pattern = r'FAILED\s+([^:]+)::(\w+)(?:\[.*?\])?\s+-\s+(.+?)(?:\n|$)'
        
        # Track which errors we've already processed to avoid duplicates
        processed_errors = set()
        
        for match in re.finditer(failed_pattern, output):
            test_file = match.group(1)
            test_name = match.group(2)
            error_msg = match.group(3)
            
            # Mark this error as processed
            processed_errors.add(error_msg)
            
            context = self._parse_failure_details(test_file, test_name, error_msg, output)
            if context:
                failure_contexts.append(context)
        
        # Also check for import errors or module not found (but skip if already processed)
        import_error_pattern = r'(ImportError|ModuleNotFoundError):\s+(.+?)(?:\n|$)'
        for match in re.finditer(import_error_pattern, output):
            error_type = match.group(1)
            error_msg = match.group(2)
            
            # Skip if this error was already processed in FAILED pattern
            full_error = f"{error_type}: {error_msg}"
            if any(full_error in proc_err for proc_err in processed_errors):
                continue
            
            # Extract module/component name
            missing_component = None
            if "No module named" in error_msg:
                module_match = re.search(r"No module named ['\"](.+?)['\"]", error_msg)
                if module_match:
                    missing_component = module_match.group(1)
            elif "cannot import name" in error_msg:
                import_match = re.search(r"cannot import name ['\"](.+?)['\"]", error_msg)
                if import_match:
                    missing_component = import_match.group(1)
            
            context = TestFailureContext(
                test_file="unknown",
                test_name="import",
                failure_type="import_error",
                failure_message=error_msg,
                missing_component=missing_component
            )
            failure_contexts.append(context)
        
        return failure_contexts
    
    def _parse_failure_details(
        self, 
        test_file: str, 
        test_name: str, 
        error_msg: str,
        full_output: str
    ) -> Optional[TestFailureContext]:
        """
        Parse detailed failure information from error message
        
        Args:
            test_file: Test file name
            test_name: Test method name
            error_msg: Error message
            full_output: Full test output
            
        Returns:
            TestFailureContext or None
        """
        context = TestFailureContext(
            test_file=test_file,
            test_name=test_name,
            failure_type="unknown",
            failure_message=error_msg
        )
        
        # Detect import errors first (can appear in FAILED lines)
        if "ImportError" in error_msg or "ModuleNotFoundError" in error_msg:
            context.failure_type = "import_error"
            
            # Extract missing module
            if "No module named" in error_msg:
                module_match = re.search(r"No module named ['\"](.+?)['\"]", error_msg)
                if module_match:
                    context.missing_component = module_match.group(1)
            elif "cannot import name" in error_msg:
                import_match = re.search(r"cannot import name ['\"](.+?)['\"]", error_msg)
                if import_match:
                    context.missing_component = import_match.group(1)
        
        # Detect assertion errors
        elif "AssertionError" in error_msg:
            context.failure_type = "assertion"
            
            # Try to extract expected vs actual values
            # Pattern: assert actual == expected
            # Updated pattern to handle parentheses better
            assert_pattern = r'assert\s+(.+?)\s+==\s+(.+?)$'
            match = re.search(assert_pattern, error_msg)
            if match:
                context.actual_value = match.group(1).strip()
                context.expected_value = match.group(2).strip()
        
        # Detect attribute errors
        elif "AttributeError" in error_msg:
            context.failure_type = "attribute_error"
            
            # Extract missing attribute
            attr_pattern = r"'(.+?)' object has no attribute '(.+?)'"
            match = re.search(attr_pattern, error_msg)
            if match:
                context.missing_component = f"{match.group(1)}.{match.group(2)}"
        
        # Detect name errors
        elif "NameError" in error_msg:
            context.failure_type = "name_error"
            
            # Extract undefined name
            name_pattern = r"name '(.+?)' is not defined"
            match = re.search(name_pattern, error_msg)
            if match:
                context.missing_component = match.group(1)
        
        # Detect type errors
        elif "TypeError" in error_msg:
            context.failure_type = "type_error"
        
        # Try to find line number from traceback
        # Look for pattern like "test_file.py", line 42
        line_pattern = rf'{re.escape(test_file)}", line (\d+)'
        line_match = re.search(line_pattern, full_output)
        if line_match:
            context.line_number = int(line_match.group(1))
        
        return context
    
    def prepare_implementation_context(
        self, 
        feature: TestableFeature,
        failure_contexts: List[TestFailureContext]
    ) -> Dict[str, Any]:
        """
        Prepare context information for the implementation phase
        
        Args:
            feature: The feature being implemented
            failure_contexts: List of test failure contexts
            
        Returns:
            Dictionary with implementation guidance
        """
        # Group failures by type
        failures_by_type = {}
        for context in failure_contexts:
            if context.failure_type not in failures_by_type:
                failures_by_type[context.failure_type] = []
            failures_by_type[context.failure_type].append(context)
        
        # Extract missing components
        missing_components = set()
        for context in failure_contexts:
            if context.missing_component:
                missing_components.add(context.missing_component)
        
        # Build implementation hints
        implementation_hints = []
        
        if "import_error" in failures_by_type:
            implementation_hints.append(
                "Create the required modules/classes that tests are trying to import"
            )
        
        if "attribute_error" in failures_by_type or "name_error" in failures_by_type:
            implementation_hints.append(
                "Implement the missing attributes, methods, or variables that tests expect"
            )
        
        if "assertion" in failures_by_type:
            implementation_hints.append(
                "Implement logic to make assertions pass with expected values"
            )
        
        return {
            "feature": feature.to_dict(),
            "failure_summary": {
                "total_failures": len(failure_contexts),
                "failure_types": list(failures_by_type.keys()),
                "failures_by_type": {
                    ftype: len(contexts) 
                    for ftype, contexts in failures_by_type.items()
                }
            },
            "missing_components": list(missing_components),
            "implementation_hints": implementation_hints,
            "detailed_failures": [ctx.to_dict() for ctx in failure_contexts]
        }
    
    async def enforce_red_phase(
        self,
        feature: TestableFeature,
        test_file_path: str,
        project_root: str
    ) -> Dict[str, Any]:
        """
        Main method to enforce RED phase for a feature
        
        Args:
            feature: The feature being implemented
            test_file_path: Path to the test file
            project_root: Root directory of the project
            
        Returns:
            Implementation context if RED phase is valid
            
        Raises:
            RedPhaseError: If RED phase validation fails
        """
        try:
            # Validate RED phase
            is_valid, failure_contexts = await self.validate_red_phase(
                feature, test_file_path, project_root
            )
            
            if not is_valid:
                raise RedPhaseError("RED phase validation failed")
            
            # Prepare implementation context
            impl_context = self.prepare_implementation_context(feature, failure_contexts)
            
            # Add RED phase confirmation
            impl_context["red_phase_validated"] = True
            impl_context["validation_timestamp"] = datetime.now().isoformat()
            
            return impl_context
            
        except Exception as e:
            # Log the error and re-raise
            error_context = {
                "error": str(e),
                "feature": feature.id,
                "phase": "RED",
                "test_file": test_file_path
            }
            raise RedPhaseError(f"RED phase enforcement failed: {str(e)}") from e