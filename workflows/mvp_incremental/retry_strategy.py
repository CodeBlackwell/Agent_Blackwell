"""
Retry Strategy for MVP Incremental Workflow
Handles retrying failed feature implementations
"""
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
import re
from workflows.mvp_incremental.error_analyzer import SimplifiedErrorAnalyzer, ErrorCategory


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_retries: int = 2  # Maximum retries per feature
    extract_error_context: bool = True  # Whether to extract error context for retry
    modify_prompt_on_retry: bool = True  # Whether to modify the prompt based on errors


class RetryStrategy:
    """Handles retry logic for failed features"""
    
    def __init__(self):
        self.error_analyzer = SimplifiedErrorAnalyzer()
    
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
    
    def extract_error_context(self, validation_output: str) -> Dict[str, str]:
        """
        Extract useful context from validation error output.
        Phase 5: Enhanced with error analyzer.
        """
        context = {
            "error_type": "",
            "error_message": "",
            "error_line": "",
            "error_file": "",
            "full_error": "",
            "recovery_hint": "",
            "error_category": ""
        }
        
        # Extract error details after DETAILS:
        if "DETAILS:" in validation_output:
            error_details = validation_output.split("DETAILS:")[1].strip()
            context["full_error"] = error_details
            
            # Use error analyzer for better analysis
            error_info = self.error_analyzer.analyze_error(error_details)
            
            # Update context with analyzer results
            context["error_type"] = error_info.error_type or ""
            context["error_category"] = error_info.category.value
            context["recovery_hint"] = error_info.recovery_hint
            
            if error_info.file_path:
                context["error_file"] = error_info.file_path
            if error_info.line_number:
                context["error_line"] = str(error_info.line_number)
            
            # Extract error message
            error_msg_match = re.search(r'\w+Error:\s*(.+?)(?:\n|$)', error_details)
            if error_msg_match:
                context["error_message"] = error_msg_match.group(1).strip()
            else:
                # Use first line as message if no standard error format
                first_line = error_details.split('\n')[0]
                context["error_message"] = first_line
        
        return context
    
    def create_retry_prompt(
        self,
        original_context: str,
        feature: Dict[str, str],
        validation_output: str,
        error_context: Dict[str, str],
        retry_count: int,
        accumulated_code: Dict[str, str]
    ) -> str:
        """
        Create an enhanced prompt for retry that includes error information.
        """
        retry_prompt = f"""
You previously implemented a feature that FAILED validation. You need to FIX the implementation.

RETRY ATTEMPT: {retry_count}

FEATURE TO IMPLEMENT: {feature['title']}
Description: {feature['description']}

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
2. FIX the specific error in the existing code
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