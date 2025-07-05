"""
Advanced error analysis and recovery system for incremental development.
Categorizes errors, suggests fixes, and provides context-aware recovery strategies.
"""
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import re
import ast
import difflib
from collections import defaultdict


class ErrorCategory(Enum):
    """Categories of errors with different recovery strategies."""
    SYNTAX_ERROR = "syntax_error"
    IMPORT_ERROR = "import_error"
    NAME_ERROR = "name_error"
    TYPE_ERROR = "type_error"
    ATTRIBUTE_ERROR = "attribute_error"
    VALUE_ERROR = "value_error"
    INDEX_ERROR = "index_error"
    KEY_ERROR = "key_error"
    ASSERTION_ERROR = "assertion_error"
    RUNTIME_ERROR = "runtime_error"
    TEST_FAILURE = "test_failure"
    DEPENDENCY_ERROR = "dependency_error"
    INTEGRATION_ERROR = "integration_error"
    UNKNOWN = "unknown"


@dataclass
class ErrorContext:
    """Contextual information about an error."""
    error_type: ErrorCategory
    error_message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    stack_trace: Optional[str] = None
    related_files: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def get_location_string(self) -> str:
        """Get a formatted location string."""
        if self.file_path and self.line_number:
            return f"{self.file_path}:{self.line_number}"
        elif self.file_path:
            return self.file_path
        return "unknown location"


@dataclass
class RecoverySuggestion:
    """A suggestion for recovering from an error."""
    strategy: str
    description: str
    code_changes: Optional[Dict[str, str]] = None
    confidence: float = 0.5
    requires_context: bool = False
    
    def apply_changes(self, current_code: Dict[str, str]) -> Dict[str, str]:
        """Apply suggested code changes."""
        if not self.code_changes:
            return current_code
        
        updated_code = current_code.copy()
        for file_path, changes in self.code_changes.items():
            if file_path in updated_code:
                # Apply changes (simplified - real implementation would be more sophisticated)
                updated_code[file_path] = changes
        
        return updated_code


@dataclass
class ErrorPattern:
    """A pattern of errors with associated recovery strategies."""
    pattern_id: str
    category: ErrorCategory
    regex_pattern: str
    common_causes: List[str]
    recovery_suggestions: List[RecoverySuggestion]
    success_rate: float = 0.0
    
    def matches(self, error_message: str) -> bool:
        """Check if error message matches this pattern."""
        return bool(re.search(self.regex_pattern, error_message, re.IGNORECASE))


class ErrorAnalyzer:
    """
    Analyzes errors, categorizes them, and suggests recovery strategies.
    """
    
    def __init__(self):
        self.error_patterns = self._initialize_error_patterns()
        self.error_history: List[ErrorContext] = []
        self.recovery_success_rate: Dict[str, float] = defaultdict(float)
        self.recovery_attempts: Dict[str, int] = defaultdict(int)
    
    def _initialize_error_patterns(self) -> List[ErrorPattern]:
        """Initialize common error patterns with recovery strategies."""
        patterns = [
            # Syntax Errors
            ErrorPattern(
                pattern_id="missing_colon",
                category=ErrorCategory.SYNTAX_ERROR,
                regex_pattern=r"expected ':' at",
                common_causes=["Missing colon after function/class definition", "Missing colon after if/for/while"],
                recovery_suggestions=[
                    RecoverySuggestion(
                        strategy="add_missing_colon",
                        description="Add missing colon at the end of the line",
                        confidence=0.9
                    )
                ]
            ),
            
            # Import Errors
            ErrorPattern(
                pattern_id="module_not_found",
                category=ErrorCategory.IMPORT_ERROR,
                regex_pattern=r"No module named '(\w+)'",
                common_causes=["Module not installed", "Incorrect module name", "Missing __init__.py"],
                recovery_suggestions=[
                    RecoverySuggestion(
                        strategy="check_local_modules",
                        description="Check if module exists in local codebase",
                        confidence=0.7,
                        requires_context=True
                    ),
                    RecoverySuggestion(
                        strategy="fix_import_path",
                        description="Adjust import path to match project structure",
                        confidence=0.6
                    )
                ]
            ),
            
            # Name Errors
            ErrorPattern(
                pattern_id="undefined_name",
                category=ErrorCategory.NAME_ERROR,
                regex_pattern=r"name '(\w+)' is not defined",
                common_causes=["Variable used before definition", "Missing import", "Typo in variable name"],
                recovery_suggestions=[
                    RecoverySuggestion(
                        strategy="find_similar_names",
                        description="Look for similar variable names that might be typos",
                        confidence=0.7,
                        requires_context=True
                    ),
                    RecoverySuggestion(
                        strategy="add_missing_import",
                        description="Add import statement for the undefined name",
                        confidence=0.6
                    )
                ]
            ),
            
            # Type Errors
            ErrorPattern(
                pattern_id="type_mismatch",
                category=ErrorCategory.TYPE_ERROR,
                regex_pattern=r"expected (\w+), got (\w+)",
                common_causes=["Incorrect argument type", "Wrong return type", "Type conversion needed"],
                recovery_suggestions=[
                    RecoverySuggestion(
                        strategy="add_type_conversion",
                        description="Add appropriate type conversion",
                        confidence=0.7
                    ),
                    RecoverySuggestion(
                        strategy="fix_function_signature",
                        description="Update function signature to match usage",
                        confidence=0.5
                    )
                ]
            ),
            
            # Test Failures
            ErrorPattern(
                pattern_id="assertion_failed",
                category=ErrorCategory.ASSERTION_ERROR,
                regex_pattern=r"AssertionError|assert.*failed",
                common_causes=["Incorrect implementation", "Wrong expected value", "Edge case not handled"],
                recovery_suggestions=[
                    RecoverySuggestion(
                        strategy="analyze_assertion",
                        description="Analyze assertion to understand expected behavior",
                        confidence=0.6,
                        requires_context=True
                    ),
                    RecoverySuggestion(
                        strategy="add_edge_case_handling",
                        description="Add handling for edge cases",
                        confidence=0.5
                    )
                ]
            )
        ]
        
        return patterns
    
    def analyze_error(self, error_message: str, code_context: Optional[Dict[str, str]] = None,
                     stack_trace: Optional[str] = None) -> ErrorContext:
        """Analyze an error and create error context."""
        # Categorize error
        category = self._categorize_error(error_message, stack_trace)
        
        # Extract location information
        file_path, line_number = self._extract_location(error_message, stack_trace)
        
        # Get code snippet if possible
        code_snippet = None
        if file_path and line_number and code_context and file_path in code_context:
            code_snippet = self._extract_code_snippet(code_context[file_path], line_number)
        
        # Find related files
        related_files = self._find_related_files(error_message, stack_trace, code_context)
        
        error_context = ErrorContext(
            error_type=category,
            error_message=error_message,
            file_path=file_path,
            line_number=line_number,
            code_snippet=code_snippet,
            stack_trace=stack_trace,
            related_files=related_files
        )
        
        self.error_history.append(error_context)
        return error_context
    
    def _categorize_error(self, error_message: str, stack_trace: Optional[str] = None) -> ErrorCategory:
        """Categorize an error based on message and stack trace."""
        error_lower = error_message.lower()
        
        # Check common error types
        if "syntaxerror" in error_lower or "invalid syntax" in error_lower:
            return ErrorCategory.SYNTAX_ERROR
        elif "importerror" in error_lower or "no module named" in error_lower:
            return ErrorCategory.IMPORT_ERROR
        elif "nameerror" in error_lower or "not defined" in error_lower:
            return ErrorCategory.NAME_ERROR
        elif "typeerror" in error_lower:
            return ErrorCategory.TYPE_ERROR
        elif "attributeerror" in error_lower:
            return ErrorCategory.ATTRIBUTE_ERROR
        elif "valueerror" in error_lower:
            return ErrorCategory.VALUE_ERROR
        elif "indexerror" in error_lower:
            return ErrorCategory.INDEX_ERROR
        elif "keyerror" in error_lower:
            return ErrorCategory.KEY_ERROR
        elif "assertionerror" in error_lower or "assert" in error_lower:
            return ErrorCategory.ASSERTION_ERROR
        elif "test" in error_lower and ("fail" in error_lower or "error" in error_lower):
            return ErrorCategory.TEST_FAILURE
        else:
            return ErrorCategory.UNKNOWN
    
    def _extract_location(self, error_message: str, stack_trace: Optional[str] = None) -> Tuple[Optional[str], Optional[int]]:
        """Extract file path and line number from error message or stack trace."""
        # Try to extract from error message
        location_pattern = re.compile(r'File "([^"]+)", line (\d+)')
        match = location_pattern.search(error_message)
        
        if match:
            return match.group(1), int(match.group(2))
        
        # Try stack trace
        if stack_trace:
            match = location_pattern.search(stack_trace)
            if match:
                return match.group(1), int(match.group(2))
        
        # Try other patterns
        alt_pattern = re.compile(r'(\S+\.py):(\d+)')
        match = alt_pattern.search(error_message)
        if match:
            return match.group(1), int(match.group(2))
        
        return None, None
    
    def _extract_code_snippet(self, code: str, line_number: int, context_lines: int = 3) -> str:
        """Extract code snippet around error line."""
        lines = code.split('\n')
        start = max(0, line_number - context_lines - 1)
        end = min(len(lines), line_number + context_lines)
        
        snippet_lines = []
        for i in range(start, end):
            line_num = i + 1
            prefix = ">>> " if line_num == line_number else "    "
            snippet_lines.append(f"{line_num:4d}{prefix}{lines[i]}")
        
        return '\n'.join(snippet_lines)
    
    def _find_related_files(self, error_message: str, stack_trace: Optional[str], 
                           code_context: Optional[Dict[str, str]]) -> List[str]:
        """Find files related to the error."""
        related = set()
        
        # Extract file names from error message and stack trace
        file_pattern = re.compile(r'(\S+\.py)')
        
        for text in [error_message, stack_trace]:
            if text:
                for match in file_pattern.finditer(text):
                    related.add(match.group(1))
        
        # Look for import references
        if code_context:
            import_pattern = re.compile(r'from\s+(\S+)\s+import|import\s+(\S+)')
            for file_path, code in code_context.items():
                for match in import_pattern.finditer(code):
                    module = match.group(1) or match.group(2)
                    potential_file = f"{module.replace('.', '/')}.py"
                    if potential_file in code_context:
                        related.add(potential_file)
        
        return list(related)
    
    def suggest_recovery(self, error_context: ErrorContext, 
                        code_context: Optional[Dict[str, str]] = None) -> List[RecoverySuggestion]:
        """Suggest recovery strategies for an error."""
        suggestions = []
        
        # Find matching error patterns
        for pattern in self.error_patterns:
            if pattern.category == error_context.error_type and pattern.matches(error_context.error_message):
                # Add pattern suggestions
                for suggestion in pattern.recovery_suggestions:
                    if suggestion.requires_context and not code_context:
                        continue
                    
                    # Adjust confidence based on success rate
                    adjusted_suggestion = RecoverySuggestion(
                        strategy=suggestion.strategy,
                        description=suggestion.description,
                        code_changes=suggestion.code_changes,
                        confidence=suggestion.confidence * (1 + self.recovery_success_rate.get(pattern.pattern_id, 0)),
                        requires_context=suggestion.requires_context
                    )
                    suggestions.append(adjusted_suggestion)
        
        # Add context-specific suggestions
        if code_context:
            context_suggestions = self._generate_context_suggestions(error_context, code_context)
            suggestions.extend(context_suggestions)
        
        # Sort by confidence
        suggestions.sort(key=lambda s: s.confidence, reverse=True)
        
        return suggestions[:5]  # Return top 5 suggestions
    
    def _generate_context_suggestions(self, error_context: ErrorContext, 
                                    code_context: Dict[str, str]) -> List[RecoverySuggestion]:
        """Generate context-specific recovery suggestions."""
        suggestions = []
        
        # For NameError, check for typos
        if error_context.error_type == ErrorCategory.NAME_ERROR:
            match = re.search(r"name '(\w+)' is not defined", error_context.error_message)
            if match:
                undefined_name = match.group(1)
                similar_names = self._find_similar_names(undefined_name, code_context)
                
                if similar_names:
                    suggestions.append(RecoverySuggestion(
                        strategy="fix_typo",
                        description=f"Did you mean '{similar_names[0]}'?",
                        confidence=0.8 if similar_names else 0.3
                    ))
        
        # For ImportError, check local modules
        elif error_context.error_type == ErrorCategory.IMPORT_ERROR:
            match = re.search(r"No module named '(\w+)'", error_context.error_message)
            if match:
                module_name = match.group(1)
                if f"{module_name}.py" in code_context:
                    suggestions.append(RecoverySuggestion(
                        strategy="use_relative_import",
                        description=f"Use relative import: from . import {module_name}",
                        confidence=0.7
                    ))
        
        return suggestions
    
    def _find_similar_names(self, name: str, code_context: Dict[str, str]) -> List[str]:
        """Find similar variable/function names in code."""
        all_names = set()
        
        for code in code_context.values():
            try:
                tree = ast.parse(code)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Name):
                        all_names.add(node.id)
                    elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                        all_names.add(node.name)
            except:
                continue
        
        # Find similar names using string similarity
        similar = []
        for existing_name in all_names:
            # Skip if it's the same name we're looking for
            if existing_name.lower() == name.lower():
                continue
            ratio = difflib.SequenceMatcher(None, name.lower(), existing_name.lower()).ratio()
            if ratio > 0.8:  # 80% similarity threshold
                similar.append(existing_name)
        
        return sorted(similar, key=lambda n: difflib.SequenceMatcher(None, name, n).ratio(), reverse=True)
    
    def build_recovery_context(self, error_context: ErrorContext, 
                             previous_attempts: List[str]) -> str:
        """Build context for the coder agent to help with recovery."""
        context_parts = [
            f"ERROR RECOVERY CONTEXT",
            f"Error Type: {error_context.error_type.value}",
            f"Error Message: {error_context.error_message}",
            f"Location: {error_context.get_location_string()}",
            ""
        ]
        
        if error_context.code_snippet:
            context_parts.extend([
                "Code Context:",
                error_context.code_snippet,
                ""
            ])
        
        # Add previous attempts
        if previous_attempts:
            context_parts.extend([
                "Previous Recovery Attempts:",
                *[f"- {attempt}" for attempt in previous_attempts[-3:]],  # Last 3 attempts
                ""
            ])
        
        # Add specific guidance based on error type
        if error_context.error_type == ErrorCategory.SYNTAX_ERROR:
            context_parts.append("Focus on fixing syntax errors - check indentation, colons, and brackets")
        elif error_context.error_type == ErrorCategory.IMPORT_ERROR:
            context_parts.append("Check import statements and module paths - ensure all dependencies exist")
        elif error_context.error_type == ErrorCategory.NAME_ERROR:
            context_parts.append("Ensure all variables are defined before use - check for typos")
        elif error_context.error_type == ErrorCategory.TEST_FAILURE:
            context_parts.append("Analyze test expectations and ensure implementation matches requirements")
        
        return "\n".join(context_parts)
    
    def record_recovery_outcome(self, pattern_id: str, success: bool):
        """Record the outcome of a recovery attempt."""
        self.recovery_attempts[pattern_id] += 1
        if success:
            # Update success rate using exponential moving average
            current_rate = self.recovery_success_rate[pattern_id]
            self.recovery_success_rate[pattern_id] = 0.7 * current_rate + 0.3 * (1.0 if success else 0.0)
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of error patterns and recovery success."""
        error_counts = defaultdict(int)
        for error in self.error_history:
            error_counts[error.error_type.value] += 1
        
        return {
            "total_errors": len(self.error_history),
            "error_distribution": dict(error_counts),
            "recovery_success_rates": dict(self.recovery_success_rate),
            "most_common_error": max(error_counts.items(), key=lambda x: x[1])[0] if error_counts else None,
            "recovery_attempts": dict(self.recovery_attempts)
        }