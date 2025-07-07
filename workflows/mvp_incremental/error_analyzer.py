"""
Simplified Error Analyzer for MVP Incremental Workflow
Provides basic error categorization and recovery hints
"""
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class ErrorCategory(Enum):
    """Basic error categories for MVP"""
    SYNTAX = "syntax"
    IMPORT = "import"
    RUNTIME = "runtime"
    VALIDATION = "validation"
    UNKNOWN = "unknown"


@dataclass
class ErrorInfo:
    """Simplified error information"""
    category: ErrorCategory
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    error_type: Optional[str] = None
    recovery_hint: Optional[str] = None


@dataclass
class ErrorContext:
    """Context information for an error"""
    error_type: str
    error_message: str
    line_number: int
    context_lines: List[str]
    stack_trace: str
    recovery_hints: List[str]


class SimplifiedErrorAnalyzer:
    """
    Simplified error analyzer for MVP incremental workflow.
    Provides basic error categorization and recovery hints.
    """
    
    def __init__(self):
        # Simple patterns for error categorization
        self.error_patterns = {
            ErrorCategory.SYNTAX: [
                r"SyntaxError",
                r"invalid syntax",
                r"unexpected indent",
                r"IndentationError",
                r"expected .*:",
                r"unexpected EOF",
                r"unmatched"
            ],
            ErrorCategory.IMPORT: [
                r"ImportError",
                r"ModuleNotFoundError",
                r"No module named",
                r"cannot import name",
                r"attempted relative import"
            ],
            ErrorCategory.RUNTIME: [
                r"NameError",
                r"TypeError",
                r"AttributeError",
                r"ValueError",
                r"KeyError",
                r"IndexError",
                r"UnboundLocalError",
                r"ZeroDivisionError"
            ],
            ErrorCategory.VALIDATION: [
                r"AssertionError",
                r"test.*failed",
                r"FAILED",
                r"does not match",
                r"expected.*but got"
            ]
        }
        
        # Recovery hints by category
        self.recovery_hints = {
            ErrorCategory.SYNTAX: {
                "default": "Check for missing colons, brackets, or indentation errors",
                "SyntaxError": "Review syntax - missing colons after if/def/class, unclosed brackets",
                "IndentationError": "Fix indentation - use consistent spaces or tabs",
                "unexpected EOF": "Check for unclosed brackets, quotes, or incomplete blocks"
            },
            ErrorCategory.IMPORT: {
                "default": "Verify module exists and import path is correct",
                "ModuleNotFoundError": "Module not installed or not in Python path",
                "ImportError": "Check if importing correct name from module",
                "relative import": "Use absolute imports or check package structure"
            },
            ErrorCategory.RUNTIME: {
                "default": "Check variable definitions and type compatibility",
                "NameError": "Variable or function not defined - check spelling and scope",
                "TypeError": "Check argument types and number of parameters",
                "AttributeError": "Object doesn't have this attribute - check method/property name",
                "ValueError": "Invalid value passed to function - check input constraints",
                "KeyError": "Dictionary key doesn't exist - check key name or use .get()",
                "IndexError": "List/array index out of range - check length before accessing",
                "ZeroDivisionError": "Add check for zero before division"
            },
            ErrorCategory.VALIDATION: {
                "default": "Review test expectations and implementation logic",
                "AssertionError": "Test assertion failed - check expected vs actual values",
                "FAILED": "Test failed - review test logic and implementation"
            }
        }
    
    def analyze_error(self, error_message: str) -> ErrorInfo:
        """
        Analyze an error message and return structured error information.
        """
        # Categorize the error
        category = self._categorize_error(error_message)
        
        # Extract error type
        error_type = self._extract_error_type(error_message)
        
        # Extract file location
        file_path, line_number = self._extract_location(error_message)
        
        # Generate recovery hint
        recovery_hint = self._get_recovery_hint(category, error_type, error_message)
        
        return ErrorInfo(
            category=category,
            message=error_message,
            file_path=file_path,
            line_number=line_number,
            error_type=error_type,
            recovery_hint=recovery_hint
        )
    
    def _categorize_error(self, error_message: str) -> ErrorCategory:
        """Categorize error based on patterns."""
        for category, patterns in self.error_patterns.items():
            for pattern in patterns:
                if re.search(pattern, error_message, re.IGNORECASE):
                    return category
        return ErrorCategory.UNKNOWN
    
    def _extract_error_type(self, error_message: str) -> Optional[str]:
        """Extract the specific error type (e.g., 'SyntaxError', 'NameError')."""
        # Look for Python error types
        match = re.search(r'(\w+Error):', error_message)
        if match:
            return match.group(1)
        return None
    
    def _extract_location(self, error_message: str) -> Tuple[Optional[str], Optional[int]]:
        """Extract file path and line number from error message."""
        # Pattern for Python traceback: File "path/to/file.py", line 123
        match = re.search(r'File ["\']([^"\']+)["\'], line (\d+)', error_message)
        if match:
            return match.group(1), int(match.group(2))
        
        # Pattern for simpler format: path/to/file.py:123
        match = re.search(r'(\S+\.py):(\d+)', error_message)
        if match:
            return match.group(1), int(match.group(2))
        
        return None, None
    
    def _get_recovery_hint(self, category: ErrorCategory, error_type: Optional[str], 
                          error_message: str) -> str:
        """Generate a recovery hint based on error category and type."""
        category_hints = self.recovery_hints.get(category, {})
        
        # Try specific error type first
        if error_type and error_type in category_hints:
            return category_hints[error_type]
        
        # Check for specific patterns in message
        for key, hint in category_hints.items():
            if key != "default" and key.lower() in error_message.lower():
                return hint
        
        # Fall back to default hint for category
        return category_hints.get("default", "Review the error message and fix the code")
    
    def create_error_context_prompt(self, error_info: ErrorInfo, 
                                   feature_description: str,
                                   code_snippet: Optional[str] = None) -> str:
        """
        Create a prompt that includes error context for the coder agent.
        Used when retrying after validation failure.
        """
        prompt_parts = [
            f"The implementation of '{feature_description}' failed with an error.",
            "",
            "ERROR DETAILS:",
            f"- Category: {error_info.category.value}",
            f"- Type: {error_info.error_type or 'Unknown'}",
            f"- Message: {error_info.message}"
        ]
        
        if error_info.file_path:
            prompt_parts.append(f"- File: {error_info.file_path}")
        if error_info.line_number:
            prompt_parts.append(f"- Line: {error_info.line_number}")
        
        prompt_parts.extend([
            "",
            "RECOVERY HINT:",
            error_info.recovery_hint,
            "",
            "Please fix the error based on the above information."
        ])
        
        if code_snippet:
            prompt_parts.extend([
                "",
                "RELEVANT CODE:",
                "```python",
                code_snippet,
                "```"
            ])
        
        return "\n".join(prompt_parts)
    
    def extract_error_lines(self, error_message: str) -> List[str]:
        """
        Extract the most relevant lines from an error message.
        Useful for creating concise error summaries.
        """
        lines = error_message.strip().split('\n')
        relevant_lines = []
        
        for line in lines:
            # Skip empty lines and long traceback lines
            if not line.strip() or line.strip().startswith('File "<'):
                continue
            
            # Include lines with error types or important keywords
            if any(pattern in line for pattern in ['Error:', 'error:', 'FAIL', 'assert', 'line']):
                relevant_lines.append(line.strip())
            
            # Limit to avoid too much noise
            if len(relevant_lines) >= 3:
                break
        
        return relevant_lines or [lines[0]] if lines else []