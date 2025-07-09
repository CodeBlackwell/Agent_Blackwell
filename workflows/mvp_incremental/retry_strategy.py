"""
Retry Strategy for MVP Incremental Workflow
Handles retrying failed feature implementations with TDD test-driven context
"""
from typing import Dict, Optional, Tuple, List, Set, Any
from dataclasses import dataclass, field
import re
from workflows.mvp_incremental.error_analyzer import SimplifiedErrorAnalyzer, ErrorCategory
# Import TestFailureContext from red_phase if available
try:
    from workflows.mvp_incremental.red_phase import TestFailureContext
except ImportError:
    # Define a simple version if red_phase is not available
    @dataclass
    class TestFailureContext:
        test_file: str
        test_name: str
        failure_type: str
        failure_message: str
        expected_value: Optional[str] = None
        actual_value: Optional[str] = None
        missing_component: Optional[str] = None
        line_number: Optional[int] = None


@dataclass
class RetryConfig:
    """Configuration for retry behavior with TDD enhancements"""
    max_retries: int = 2  # Maximum retries per feature
    extract_error_context: bool = True  # Whether to extract error context for retry
    modify_prompt_on_retry: bool = True  # Whether to modify the prompt based on errors
    include_test_context: bool = True  # Whether to include detailed test failure context
    track_test_progression: bool = True  # Whether to track which tests pass/fail across retries
    max_test_specific_hints: int = 5  # Maximum number of test-specific hints to generate


@dataclass
class TestProgressionTracker:
    """Tracks test pass/fail status across retry attempts"""
    failing_tests: Set[str] = field(default_factory=set)  # Tests that are currently failing
    passed_tests: Set[str] = field(default_factory=set)  # Tests that started passing
    persistent_failures: Set[str] = field(default_factory=set)  # Tests that keep failing
    attempt_history: List[Dict[str, Any]] = field(default_factory=list)  # History of each attempt


class RetryStrategy:
    """Handles retry logic for failed features with TDD test-driven enhancements"""
    
    def __init__(self):
        self.error_analyzer = SimplifiedErrorAnalyzer()
        self.test_progression: Dict[str, TestProgressionTracker] = {}  # Track progression per feature
    
    def should_retry(self, validation_error: Optional[str], retry_count: int, config: RetryConfig) -> bool:
        """
        Determine if a feature should be retried based on the error and retry count.
        """
        if retry_count >= config.max_retries:
            return False
            
        if not validation_error:
            return False
        
        # Phase 5: Use error analyzer for better categorization
        error_info = self.error_analyzer.analyze_error(validation_error)
        
        # Don't retry on import errors (usually missing dependencies)
        if error_info.category == ErrorCategory.IMPORT:
            return False
            
        # Don't retry on certain types of errors
        non_retryable_patterns = [
            r"permission denied",  # File system issues
            r"disk full",  # System issues
            r"timeout",  # Execution timeout
            r"memory",  # Memory issues
            r"recursion",  # Stack overflow
        ]
        
        error_lower = validation_error.lower()
        for pattern in non_retryable_patterns:
            if re.search(pattern, error_lower):
                return False
        
        # Retry on syntax and runtime errors
        if error_info.category in [ErrorCategory.SYNTAX, ErrorCategory.RUNTIME]:
            return True
        
        # Retry on validation errors if they seem fixable
        if error_info.category == ErrorCategory.VALIDATION:
            # Only retry test failures if we haven't tried too many times
            return retry_count < 1  # More conservative for test failures
        
        # Default: retry unknown errors once
        return retry_count < 1
    
    def extract_error_context(
        self, 
        validation_output: str,
        test_failure_contexts: Optional[List[TestFailureContext]] = None
    ) -> Dict[str, str]:
        """
        Extract useful context from validation error output.
        Enhanced with error analyzer and test failure context integration.
        
        Args:
            validation_output: Raw validation output
            test_failure_contexts: Optional test failure contexts for enhanced analysis
            
        Returns:
            Dictionary with error context information
        """
        context = {
            "error_type": "",
            "error_message": "",
            "error_line": "",
            "error_file": "",
            "full_error": "",
            "recovery_hint": "",
            "error_category": "",
            "test_failure_count": "0",
            "primary_failure_type": ""
        }
        
        # If we have test failure contexts, use them for enhanced analysis
        if test_failure_contexts:
            context["test_failure_count"] = str(len(test_failure_contexts))
            
            # Determine primary failure type
            failure_types = [f.failure_type for f in test_failure_contexts]
            if failure_types:
                # Count occurrences of each type
                type_counts = {}
                for ft in failure_types:
                    type_counts[ft] = type_counts.get(ft, 0) + 1
                # Get most common type
                context["primary_failure_type"] = max(type_counts, key=type_counts.get)
            
            # Build consolidated error message from test failures
            if test_failure_contexts:
                error_messages = []
                for failure in test_failure_contexts[:3]:  # First 3 failures
                    msg = f"{failure.test_name}: {failure.failure_message}"
                    error_messages.append(msg)
                context["error_message"] = "; ".join(error_messages)
                
                # Generate recovery hint based on failure patterns
                hints = self.generate_test_specific_hints(test_failure_contexts, max_hints=1)
                if hints:
                    context["recovery_hint"] = hints[0]
        
        # Extract error details after DETAILS:
        if "DETAILS:" in validation_output:
            error_details = validation_output.split("DETAILS:")[1].strip()
            context["full_error"] = error_details
            
            # Use error analyzer for better analysis
            error_info = self.error_analyzer.analyze_error(error_details)
            
            # Update context with analyzer results (don't override if already set from test contexts)
            if not context["error_type"]:
                context["error_type"] = error_info.error_type or ""
            if not context["error_category"]:
                context["error_category"] = error_info.category.value
            if not context["recovery_hint"]:
                context["recovery_hint"] = error_info.recovery_hint
            
            if error_info.file_path and not context["error_file"]:
                context["error_file"] = error_info.file_path
            if error_info.line_number and not context["error_line"]:
                context["error_line"] = str(error_info.line_number)
            
            # Extract error message if not already set
            if not context["error_message"]:
                error_msg_match = re.search(r'\w+Error:\s*(.+?)(?:\n|$)', error_details)
                if error_msg_match:
                    context["error_message"] = error_msg_match.group(1).strip()
                else:
                    # Use first line as message if no standard error format
                    first_line = error_details.split('\n')[0]
                    context["error_message"] = first_line
        
        return context
    
    def generate_test_specific_hints(
        self, 
        test_failures: List[TestFailureContext],
        max_hints: int = 5
    ) -> List[str]:
        """
        Generate specific hints based on test failure patterns.
        
        Args:
            test_failures: List of test failure contexts
            max_hints: Maximum number of hints to generate
            
        Returns:
            List of actionable hints for fixing the failures
        """
        hints = []
        
        # Group failures by type
        import_errors = [f for f in test_failures if f.failure_type == "import_error"]
        assertion_errors = [f for f in test_failures if f.failure_type == "assertion"]
        attribute_errors = [f for f in test_failures if f.failure_type == "attribute_error"]
        name_errors = [f for f in test_failures if f.failure_type == "name_error"]
        
        # Generate hints for import errors
        if import_errors:
            missing_modules = set(f.missing_component for f in import_errors if f.missing_component)
            if missing_modules:
                hints.append(f"Create missing modules/files: {', '.join(missing_modules)}")
        
        # Generate hints for assertion errors
        if assertion_errors:
            for failure in assertion_errors[:2]:  # Show up to 2 assertion hints
                if failure.expected_value and failure.actual_value:
                    hints.append(
                        f"Fix {failure.test_name}: Expected '{failure.expected_value}' "
                        f"but got '{failure.actual_value}'"
                    )
                else:
                    hints.append(f"Fix assertion in {failure.test_name}: {failure.failure_message}")
        
        # Generate hints for attribute errors
        if attribute_errors:
            missing_attrs = set(f.missing_component for f in attribute_errors if f.missing_component)
            if missing_attrs:
                for attr in list(missing_attrs)[:2]:  # Show up to 2 attribute hints
                    if '.' in attr:
                        obj, attr_name = attr.rsplit('.', 1)
                        hints.append(f"Add method/attribute '{attr_name}' to {obj}")
                    else:
                        hints.append(f"Define missing attribute: {attr}")
        
        # Generate hints for name errors
        if name_errors:
            undefined_names = set(f.missing_component for f in name_errors if f.missing_component)
            if undefined_names:
                hints.append(f"Define missing names: {', '.join(list(undefined_names)[:3])}")
        
        return hints[:max_hints]
    
    def track_test_progression(
        self,
        feature_id: str,
        current_failures: List[TestFailureContext],
        retry_count: int
    ) -> TestProgressionTracker:
        """
        Track which tests are passing/failing across retry attempts.
        
        Args:
            feature_id: Feature being retried
            current_failures: Current test failures
            retry_count: Current retry attempt number
            
        Returns:
            TestProgressionTracker with updated status
        """
        if feature_id not in self.test_progression:
            self.test_progression[feature_id] = TestProgressionTracker()
        
        tracker = self.test_progression[feature_id]
        
        # Get current failing test names
        current_failing = {f"{f.test_file}::{f.test_name}" for f in current_failures}
        
        # Update progression
        if retry_count > 0:
            # Tests that started passing
            newly_passed = tracker.failing_tests - current_failing
            tracker.passed_tests.update(newly_passed)
            
            # Tests that are persistently failing
            persistent = tracker.failing_tests & current_failing
            tracker.persistent_failures.update(persistent)
        
        # Update current state
        tracker.failing_tests = current_failing
        
        # Record attempt history
        tracker.attempt_history.append({
            "retry_count": retry_count,
            "failing_count": len(current_failing),
            "passed_count": len(tracker.passed_tests),
            "persistent_count": len(tracker.persistent_failures)
        })
        
        return tracker
    
    def create_retry_prompt(
        self,
        original_context: str,
        feature: Dict[str, str],
        validation_output: str,
        error_context: Dict[str, str],
        retry_count: int,
        accumulated_code: Dict[str, str],
        test_failure_contexts: Optional[List[TestFailureContext]] = None,
        config: Optional[RetryConfig] = None
    ) -> str:
        """
        Create an enhanced prompt for retry that includes error information and test-driven context.
        
        Args:
            original_context: Original implementation context
            feature: Feature being implemented
            validation_output: Full validation output
            error_context: Extracted error context
            retry_count: Current retry attempt
            accumulated_code: Code written so far
            test_failure_contexts: List of test failure contexts from RED phase
            config: Retry configuration
            
        Returns:
            Enhanced retry prompt with test-specific guidance
        """
        config = config or RetryConfig()
        
        # Track test progression if available
        test_progression_info = ""
        test_specific_section = ""
        
        if test_failure_contexts and config.include_test_context:
            # Track progression
            feature_id = feature.get('id', feature['title'])
            tracker = self.track_test_progression(feature_id, test_failure_contexts, retry_count)
            
            # Generate test-specific hints
            hints = self.generate_test_specific_hints(
                test_failure_contexts, 
                config.max_test_specific_hints
            )
            
            # Build test failure details
            test_details = []
            for failure in test_failure_contexts[:5]:  # Show up to 5 test failures
                detail = f"- {failure.test_name} in {failure.test_file}"
                if failure.failure_type == "assertion" and failure.expected_value:
                    detail += f"\n    Expected: {failure.expected_value}"
                    detail += f"\n    Actual: {failure.actual_value}"
                elif failure.missing_component:
                    detail += f"\n    Missing: {failure.missing_component}"
                detail += f"\n    Error: {failure.failure_message}"
                test_details.append(detail)
            
            # Build progression info
            if retry_count > 0 and tracker.passed_tests:
                test_progression_info = f"""
TEST PROGRESSION:
✅ Tests that started passing: {len(tracker.passed_tests)}
❌ Tests still failing: {len(tracker.failing_tests)}
🔄 Persistent failures: {len(tracker.persistent_failures)}
"""
            
            test_specific_section = f"""
FAILING TESTS (TDD):
{chr(10).join(test_details)}

TEST-DRIVEN HINTS:
{chr(10).join(f"- {hint}" for hint in hints)}
{test_progression_info}"""
        
        retry_prompt = f"""
You previously implemented a feature that FAILED validation. You need to FIX the implementation.

RETRY ATTEMPT: {retry_count}

FEATURE TO IMPLEMENT: {feature['title']}
Description: {feature['description']}
{test_specific_section}

VALIDATION FAILED WITH ERROR:
{error_context.get('full_error', validation_output)}

ERROR SUMMARY:
- Error Category: {error_context.get('error_category', 'unknown')}
- Error Type: {error_context.get('error_type', 'Unknown')}
- Error Message: {error_context.get('error_message', 'See full error above')}
{f"- Error Line: {error_context['error_line']}" if error_context.get('error_line') else ''}
{f"- Error File: {error_context['error_file']}" if error_context.get('error_file') else ''}

RECOVERY HINT:
{error_context.get('recovery_hint', 'Review the error and fix the code')}

CURRENT CODE THAT NEEDS FIXING:
{_format_existing_code_for_retry(accumulated_code)}

CRITICAL INSTRUCTIONS FOR RETRY:
1. CAREFULLY read the error message and understand what went wrong
2. FIX the specific error in the existing code - focus on making the failing tests pass
3. DO NOT rewrite everything - only fix what's broken
4. Ensure all imports are correct
5. Ensure proper error handling where needed
6. Test your logic mentally before submitting

OUTPUT FORMAT:
For each file you modify or create, use this format:

```python
# filename: path/to/file.py
<file contents>
```

FOCUS ON FIXING THE ERROR - do not add new features or change working code unnecessarily.
"""
        return retry_prompt
    
    @staticmethod
    def get_backoff_message(retry_count: int, max_retries: int) -> str:
        """
        Get a user-friendly message about the retry attempt.
        """
        if retry_count == 1:
            return "🔄 First retry attempt..."
        elif retry_count == max_retries:
            return f"🔄 Final retry attempt ({retry_count}/{max_retries})..."
        else:
            return f"🔄 Retry attempt {retry_count}/{max_retries}..."


def _format_existing_code_for_retry(code_dict: Dict[str, str]) -> str:
    """Format existing code for retry context - show full files for error context."""
    if not code_dict:
        return "No existing code yet."
    
    formatted = []
    for filename in sorted(code_dict.keys()):
        formatted.append(f"\n--- {filename} ---")
        formatted.append(code_dict[filename])
    
    return "\n".join(formatted)