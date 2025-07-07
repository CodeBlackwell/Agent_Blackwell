"""
Unit tests for the error analyzer system
"""
import pytest
from datetime import datetime
from workflows.incremental.error_analyzer import (
    ErrorCategory, ErrorContext, RecoverySuggestion, ErrorPattern, ErrorAnalyzer
)


class TestErrorContext:
    """Test ErrorContext functionality"""
    
    def test_error_context_initialization(self):
        """Test ErrorContext initialization"""
        context = ErrorContext(
            error_type=ErrorCategory.SYNTAX_ERROR,
            error_message="SyntaxError: invalid syntax",
            file_path="main.py",
            line_number=42,
            code_snippet="def foo()\n    pass",
            stack_trace="Traceback...",
            related_files=["utils.py", "config.py"]
        )
        
        assert context.error_type == ErrorCategory.SYNTAX_ERROR
        assert context.error_message == "SyntaxError: invalid syntax"
        assert context.file_path == "main.py"
        assert context.line_number == 42
        assert context.code_snippet == "def foo()\n    pass"
        assert context.stack_trace == "Traceback..."
        assert context.related_files == ["utils.py", "config.py"]
        assert isinstance(context.timestamp, datetime)
    
    def test_get_location_string(self):
        """Test location string formatting"""
        # With file and line number
        context = ErrorContext(
            error_type=ErrorCategory.SYNTAX_ERROR,
            error_message="Error",
            file_path="main.py",
            line_number=42
        )
        assert context.get_location_string() == "main.py:42"
        
        # With only file path
        context.line_number = None
        assert context.get_location_string() == "main.py"
        
        # With neither
        context.file_path = None
        assert context.get_location_string() == "unknown location"


class TestRecoverySuggestion:
    """Test RecoverySuggestion functionality"""
    
    def test_recovery_suggestion_initialization(self):
        """Test RecoverySuggestion initialization"""
        suggestion = RecoverySuggestion(
            strategy="add_import",
            description="Add missing import statement",
            code_changes={"main.py": "import os\n"},
            confidence=0.8,
            requires_context=True
        )
        
        assert suggestion.strategy == "add_import"
        assert suggestion.description == "Add missing import statement"
        assert suggestion.code_changes == {"main.py": "import os\n"}
        assert suggestion.confidence == 0.8
        assert suggestion.requires_context is True
    
    def test_apply_changes_with_changes(self):
        """Test applying code changes"""
        suggestion = RecoverySuggestion(
            strategy="fix_code",
            description="Fix syntax",
            code_changes={
                "main.py": "def foo():\n    pass",
                "utils.py": "import math"
            }
        )
        
        current_code = {
            "main.py": "def foo()\n    pass",
            "utils.py": "",
            "config.py": "DEBUG = True"
        }
        
        updated = suggestion.apply_changes(current_code)
        
        assert updated["main.py"] == "def foo():\n    pass"
        assert updated["utils.py"] == "import math"
        assert updated["config.py"] == "DEBUG = True"  # Unchanged
        assert current_code["main.py"] == "def foo()\n    pass"  # Original unchanged
    
    def test_apply_changes_without_changes(self):
        """Test applying when no changes specified"""
        suggestion = RecoverySuggestion(
            strategy="analyze",
            description="Analyze code"
        )
        
        current_code = {"main.py": "code"}
        updated = suggestion.apply_changes(current_code)
        
        assert updated == current_code


class TestErrorPattern:
    """Test ErrorPattern functionality"""
    
    def test_error_pattern_initialization(self):
        """Test ErrorPattern initialization"""
        pattern = ErrorPattern(
            pattern_id="missing_colon",
            category=ErrorCategory.SYNTAX_ERROR,
            regex_pattern=r"expected ':' at",
            common_causes=["Missing colon"],
            recovery_suggestions=[
                RecoverySuggestion("add_colon", "Add colon")
            ],
            success_rate=0.75
        )
        
        assert pattern.pattern_id == "missing_colon"
        assert pattern.category == ErrorCategory.SYNTAX_ERROR
        assert pattern.regex_pattern == r"expected ':' at"
        assert pattern.common_causes == ["Missing colon"]
        assert len(pattern.recovery_suggestions) == 1
        assert pattern.success_rate == 0.75
    
    def test_matches(self):
        """Test pattern matching"""
        pattern = ErrorPattern(
            pattern_id="test",
            category=ErrorCategory.SYNTAX_ERROR,
            regex_pattern=r"expected ':' at line \d+",
            common_causes=[],
            recovery_suggestions=[]
        )
        
        assert pattern.matches("SyntaxError: expected ':' at line 42") is True
        assert pattern.matches("EXPECTED ':' AT LINE 10") is True  # Case insensitive
        assert pattern.matches("TypeError: wrong type") is False


class TestErrorAnalyzer:
    """Test ErrorAnalyzer functionality"""
    
    @pytest.fixture
    def analyzer(self):
        """Create an ErrorAnalyzer instance"""
        return ErrorAnalyzer()
    
    def test_analyzer_initialization(self, analyzer):
        """Test analyzer initialization"""
        assert len(analyzer.error_patterns) > 0
        assert analyzer.error_history == []
        assert len(analyzer.recovery_success_rate) == 0
        assert len(analyzer.recovery_attempts) == 0
    
    def test_categorize_error(self, analyzer):
        """Test error categorization"""
        test_cases = [
            ("SyntaxError: invalid syntax", ErrorCategory.SYNTAX_ERROR),
            ("ImportError: No module named 'foo'", ErrorCategory.IMPORT_ERROR),
            ("NameError: name 'x' is not defined", ErrorCategory.NAME_ERROR),
            ("TypeError: unsupported operand", ErrorCategory.TYPE_ERROR),
            ("AttributeError: no attribute 'bar'", ErrorCategory.ATTRIBUTE_ERROR),
            ("ValueError: invalid value", ErrorCategory.VALUE_ERROR),
            ("IndexError: list index out of range", ErrorCategory.INDEX_ERROR),
            ("KeyError: 'missing_key'", ErrorCategory.KEY_ERROR),
            ("AssertionError: assertion failed", ErrorCategory.ASSERTION_ERROR),
            ("Test test_foo failed", ErrorCategory.TEST_FAILURE),
            ("Random unknown error", ErrorCategory.UNKNOWN)
        ]
        
        for error_msg, expected_category in test_cases:
            category = analyzer._categorize_error(error_msg)
            assert category == expected_category
    
    def test_extract_location(self, analyzer):
        """Test location extraction"""
        # Standard Python error format
        error_msg = 'File "main.py", line 42, in function'
        file_path, line_num = analyzer._extract_location(error_msg)
        assert file_path == "main.py"
        assert line_num == 42
        
        # From stack trace
        stack_trace = 'Traceback:\n  File "utils.py", line 10\n    code here'
        file_path, line_num = analyzer._extract_location("Error", stack_trace)
        assert file_path == "utils.py"
        assert line_num == 10
        
        # Alternative format
        error_msg = "Error in test.py:25"
        file_path, line_num = analyzer._extract_location(error_msg)
        assert file_path == "test.py"
        assert line_num == 25
        
        # No location found
        file_path, line_num = analyzer._extract_location("Random error")
        assert file_path is None
        assert line_num is None
    
    def test_extract_code_snippet(self, analyzer):
        """Test code snippet extraction"""
        code = """def hello():
    print("Hello")
    
def foo():
    x = 1
    y = 2
    return x + y
    
def bar():
    pass"""
        
        # Extract around line 5 (y = 2)
        snippet = analyzer._extract_code_snippet(code, 5, context_lines=2)
        
        assert ">>> " in snippet  # Error line marker
        assert "   5>>> " in snippet  # Line 5 marked
        assert "x = 1" in snippet
        assert "y = 2" in snippet
        assert "return x + y" in snippet
    
    def test_find_related_files(self, analyzer):
        """Test finding related files"""
        error_msg = "Error in main.py importing utils.py"
        stack_trace = "File 'config.py', line 10"
        code_context = {
            "main.py": "from utils import helper\nimport config",
            "utils.py": "def helper(): pass",
            "config.py": "DEBUG = True",
            "db/models.py": "class Model: pass"
        }
        
        related = analyzer._find_related_files(error_msg, stack_trace, code_context)
        
        assert "main.py" in related
        assert "utils.py" in related
        assert "config.py" in related
    
    def test_analyze_error_complete(self, analyzer):
        """Test complete error analysis"""
        error_msg = 'File "main.py", line 5: SyntaxError: invalid syntax'
        code_context = {
            "main.py": "def hello():\n    print('hi')\n\ndef foo()\n    pass"
        }
        stack_trace = "Traceback (most recent call last):\n  File 'main.py', line 5"
        
        context = analyzer.analyze_error(error_msg, code_context, stack_trace)
        
        assert context.error_type == ErrorCategory.SYNTAX_ERROR
        assert context.error_message == error_msg
        assert context.file_path == "main.py"
        assert context.line_number == 5
        assert context.code_snippet is not None
        assert "def foo()" in context.code_snippet
        assert context.stack_trace == stack_trace
        assert len(analyzer.error_history) == 1
    
    def test_suggest_recovery_with_pattern_match(self, analyzer):
        """Test recovery suggestions with pattern matching"""
        context = ErrorContext(
            error_type=ErrorCategory.SYNTAX_ERROR,
            error_message="SyntaxError: expected ':' at line 5"
        )
        
        suggestions = analyzer.suggest_recovery(context)
        
        assert len(suggestions) > 0
        assert suggestions[0].strategy == "add_missing_colon"
        assert suggestions[0].confidence > 0.5
    
    def test_suggest_recovery_with_context(self, analyzer):
        """Test context-aware recovery suggestions"""
        context = ErrorContext(
            error_type=ErrorCategory.NAME_ERROR,
            error_message="NameError: name 'math' is not defined"
        )
        
        code_context = {
            "main.py": "import os\n\nresult = math.sqrt(16)"
        }
        
        suggestions = analyzer.suggest_recovery(context, code_context)
        
        assert len(suggestions) > 0
        # Should suggest adding import
        import_suggestions = [s for s in suggestions if "import" in s.strategy]
        assert len(import_suggestions) > 0
    
    def test_find_similar_names(self, analyzer):
        """Test finding similar variable names"""
        code_context = {
            "main.py": """
def calculate_total():
    subtotal = 100
    tax_rate = 0.08
    total_amount = subtotal * (1 + tax_rate)
    return total_amount

result = calculate_totl()  # Typo
"""
        }
        
        similar = analyzer._find_similar_names("calculate_totl", code_context)
        
        assert "calculate_total" in similar
    
    def test_generate_context_suggestions_name_error(self, analyzer):
        """Test context suggestions for name errors"""
        context = ErrorContext(
            error_type=ErrorCategory.NAME_ERROR,
            error_message="NameError: name 'calculte' is not defined"
        )
        
        code_context = {
            "main.py": "def calculate(): pass\n\nresult = calculte()"
        }
        
        suggestions = analyzer._generate_context_suggestions(context, code_context)
        
        assert len(suggestions) > 0
        assert suggestions[0].strategy == "fix_typo"
        assert "calculate" in suggestions[0].description
    
    def test_generate_context_suggestions_import_error(self, analyzer):
        """Test context suggestions for import errors"""
        context = ErrorContext(
            error_type=ErrorCategory.IMPORT_ERROR,
            error_message="ImportError: No module named 'utils'"
        )
        
        code_context = {
            "main.py": "import utils",
            "utils.py": "def helper(): pass"
        }
        
        suggestions = analyzer._generate_context_suggestions(context, code_context)
        
        assert len(suggestions) > 0
        assert suggestions[0].strategy == "use_relative_import"
        assert "from . import utils" in suggestions[0].description
    
    def test_build_recovery_context(self, analyzer):
        """Test building recovery context"""
        context = ErrorContext(
            error_type=ErrorCategory.SYNTAX_ERROR,
            error_message="SyntaxError: invalid syntax",
            file_path="main.py",
            line_number=5,
            code_snippet="   4    def foo()\n   5>>>     pass"
        )
        
        previous_attempts = [
            "Added missing colon",
            "Fixed indentation"
        ]
        
        recovery_context = analyzer.build_recovery_context(context, previous_attempts)
        
        assert "ERROR RECOVERY CONTEXT" in recovery_context
        assert "Error Type: syntax_error" in recovery_context
        assert "Location: main.py:5" in recovery_context
        assert "Code Context:" in recovery_context
        assert "def foo()" in recovery_context
        assert "Previous Recovery Attempts:" in recovery_context
        assert "- Added missing colon" in recovery_context
        assert "Focus on fixing syntax errors" in recovery_context
    
    def test_record_recovery_outcome(self, analyzer):
        """Test recording recovery outcomes"""
        pattern_id = "missing_colon"
        
        # Record some successes and failures
        analyzer.record_recovery_outcome(pattern_id, True)
        analyzer.record_recovery_outcome(pattern_id, True)
        analyzer.record_recovery_outcome(pattern_id, False)
        
        assert analyzer.recovery_attempts[pattern_id] == 3
        assert analyzer.recovery_success_rate[pattern_id] > 0.5
        assert analyzer.recovery_success_rate[pattern_id] < 1.0
    
    def test_get_error_summary(self, analyzer):
        """Test getting error summary"""
        # Analyze some errors
        analyzer.analyze_error("SyntaxError: invalid syntax")
        analyzer.analyze_error("ImportError: No module")
        analyzer.analyze_error("SyntaxError: missing colon")
        
        # Record some recovery attempts
        analyzer.record_recovery_outcome("pattern1", True)
        analyzer.record_recovery_outcome("pattern1", False)
        
        summary = analyzer.get_error_summary()
        
        assert summary["total_errors"] == 3
        assert summary["error_distribution"]["syntax_error"] == 2
        assert summary["error_distribution"]["import_error"] == 1
        assert summary["most_common_error"] == "syntax_error"
        assert "pattern1" in summary["recovery_attempts"]
        assert summary["recovery_attempts"]["pattern1"] == 2
    
    def test_error_patterns_initialization(self, analyzer):
        """Test that error patterns are properly initialized"""
        # Check that we have patterns for major error types
        pattern_categories = {p.category for p in analyzer.error_patterns}
        
        assert ErrorCategory.SYNTAX_ERROR in pattern_categories
        assert ErrorCategory.IMPORT_ERROR in pattern_categories
        assert ErrorCategory.NAME_ERROR in pattern_categories
        assert ErrorCategory.TYPE_ERROR in pattern_categories
        assert ErrorCategory.ASSERTION_ERROR in pattern_categories
        
        # Check pattern structure
        for pattern in analyzer.error_patterns:
            assert pattern.pattern_id
            assert pattern.regex_pattern
            assert len(pattern.common_causes) > 0
            assert len(pattern.recovery_suggestions) > 0
    
    def test_recovery_suggestion_confidence_adjustment(self, analyzer):
        """Test that suggestion confidence is adjusted based on success rate"""
        # Set up a success rate for a pattern
        analyzer.recovery_success_rate["module_not_found"] = 0.5
        
        context = ErrorContext(
            error_type=ErrorCategory.IMPORT_ERROR,
            error_message="ImportError: No module named 'test'"
        )
        
        suggestions = analyzer.suggest_recovery(context)
        
        # Find suggestions from the module_not_found pattern
        module_suggestions = [s for s in suggestions if s.requires_context or "module" in s.description.lower()]
        
        # Confidence should be adjusted by success rate
        if module_suggestions:
            # The confidence should be higher than base due to success rate
            assert any(s.confidence > 0.5 for s in module_suggestions)