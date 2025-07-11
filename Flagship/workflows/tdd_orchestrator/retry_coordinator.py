"""Retry Coordinator - implements intelligent retry logic with stagnation detection"""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict

from .models import TDDPhase, RetryDecision


class RetryCoordinator:
    """Coordinates retry decisions with intelligent pattern detection"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.retry_history: Dict[str, List[Dict]] = defaultdict(list)
        self.error_patterns = self._init_error_patterns()
        
        # Default retry limits
        self.max_retries = self.config.get("max_retries", 3)
        self.max_stagnation_retries = self.config.get("max_stagnation_retries", 2)
        
    def _init_error_patterns(self) -> Dict[str, Dict]:
        """Initialize known error patterns and their solutions"""
        return {
            "syntax_error": {
                "pattern": r"(SyntaxError|IndentationError|invalid syntax)",
                "suggestions": [
                    "Check for missing colons, parentheses, or quotes",
                    "Verify proper indentation (use 4 spaces)",
                    "Look for unclosed brackets or strings"
                ],
                "max_retries": 2,
                "delay": 1
            },
            "import_error": {
                "pattern": r"(ImportError|ModuleNotFoundError|cannot import)",
                "suggestions": [
                    "Verify module names and import paths",
                    "Check if required packages are installed",
                    "Use relative imports for local modules"
                ],
                "max_retries": 2,
                "delay": 1
            },
            "assertion_error": {
                "pattern": r"(AssertionError|assert.*failed)",
                "suggestions": [
                    "Review test expectations vs actual implementation",
                    "Check for off-by-one errors",
                    "Verify data types match expectations"
                ],
                "max_retries": 3,
                "delay": 2
            },
            "type_error": {
                "pattern": r"(TypeError|type.*expected)",
                "suggestions": [
                    "Check argument types passed to functions",
                    "Verify return types match expectations",
                    "Add type validation where needed"
                ],
                "max_retries": 2,
                "delay": 1
            },
            "name_error": {
                "pattern": r"(NameError|name.*not defined)",
                "suggestions": [
                    "Check variable and function names for typos",
                    "Ensure variables are defined before use",
                    "Verify class and method names match"
                ],
                "max_retries": 2,
                "delay": 1
            }
        }
    
    def should_retry(self, feature_id: str, phase: TDDPhase, attempt_number: int,
                    error: str, context: Dict[str, Any]) -> Tuple[bool, Optional[List[str]]]:
        """
        Determine if a phase should be retried
        Returns: (should_retry, suggestions)
        """
        # Record attempt
        attempt_record = {
            "phase": phase.value,
            "attempt": attempt_number,
            "error": error,
            "timestamp": datetime.now().isoformat(),
            "context": context
        }
        self.retry_history[feature_id].append(attempt_record)
        
        # Check basic retry limit
        if attempt_number >= self.max_retries:
            return False, ["Maximum retry limit reached"]
        
        # Detect stagnation
        if self._detect_stagnation(feature_id, phase):
            if attempt_number >= self.max_stagnation_retries:
                return False, ["Detected stagnation - same errors repeating"]
            
        # Analyze error and get suggestions
        error_type, suggestions = self._analyze_error(error)
        
        # Check error-specific retry limit
        if error_type and error_type in self.error_patterns:
            error_config = self.error_patterns[error_type]
            if attempt_number >= error_config.get("max_retries", self.max_retries):
                return False, [f"Maximum retries for {error_type} reached"]
        
        # Phase-specific retry logic
        additional_suggestions = self._get_phase_specific_suggestions(phase, error, context)
        if additional_suggestions:
            suggestions.extend(additional_suggestions)
        
        return True, suggestions
    
    def _detect_stagnation(self, feature_id: str, phase: TDDPhase) -> bool:
        """Detect if retry attempts are stagnating (same errors repeating)"""
        history = self.retry_history[feature_id]
        
        # Need at least 3 attempts to detect pattern
        if len(history) < 3:
            return False
        
        # Get last 3 attempts for this phase
        phase_attempts = [h for h in history if h["phase"] == phase.value][-3:]
        
        if len(phase_attempts) < 3:
            return False
        
        # Check if errors are similar
        errors = [attempt["error"] for attempt in phase_attempts]
        
        # Simple similarity check - if all errors contain same key phrases
        common_phrases = set(errors[0].lower().split())
        for error in errors[1:]:
            common_phrases &= set(error.lower().split())
        
        # If significant overlap in error messages, likely stagnating
        return len(common_phrases) > 5
    
    def _analyze_error(self, error: str) -> Tuple[Optional[str], List[str]]:
        """Analyze error message and return type and suggestions"""
        error_lower = error.lower()
        
        for error_type, config in self.error_patterns.items():
            if re.search(config["pattern"], error, re.IGNORECASE):
                return error_type, config["suggestions"].copy()
        
        # Generic suggestions if no pattern matches
        return None, ["Review the error message carefully", "Check recent changes"]
    
    def _get_phase_specific_suggestions(self, phase: TDDPhase, error: str, 
                                      context: Dict[str, Any]) -> List[str]:
        """Get suggestions specific to the current TDD phase"""
        suggestions = []
        
        if phase == TDDPhase.RED:
            suggestions.extend([
                "Ensure tests are properly structured",
                "Verify test function names start with 'test_'",
                "Check that tests actually fail without implementation"
            ])
            
        elif phase == TDDPhase.YELLOW:
            # Check if specific tests are failing
            test_results = context.get("test_results", {})
            failed_tests = test_results.get("failed_tests", [])
            
            if failed_tests:
                suggestions.append(f"Focus on fixing these tests: {', '.join(failed_tests[:3])}")
            
            suggestions.extend([
                "Implement minimal code to pass tests",
                "Don't over-engineer the solution",
                "Address one test failure at a time"
            ])
            
        elif phase == TDDPhase.GREEN:
            suggestions.extend([
                "Ensure all test dependencies are available",
                "Check test execution environment",
                "Verify test runner configuration"
            ])
        
        return suggestions
    
    def get_retry_decision(self, feature_id: str, phase: TDDPhase, 
                          attempt_number: int, error: str, 
                          context: Dict[str, Any]) -> RetryDecision:
        """Get a complete retry decision with all details"""
        should_retry, suggestions = self.should_retry(
            feature_id, phase, attempt_number, error, context
        )
        
        # Determine delay
        delay = self._calculate_retry_delay(error, attempt_number)
        
        # Build reason
        if should_retry:
            reason = f"Retry attempt {attempt_number + 1} for {phase.value} phase"
        else:
            reason = f"Retry limit reached for {phase.value} phase"
        
        return RetryDecision(
            should_retry=should_retry,
            reason=reason,
            suggestions=suggestions or [],
            delay_seconds=delay
        )
    
    def _calculate_retry_delay(self, error: str, attempt_number: int) -> int:
        """Calculate delay before retry based on error type and attempt number"""
        # Check if error matches known pattern
        for error_type, config in self.error_patterns.items():
            if re.search(config["pattern"], error, re.IGNORECASE):
                base_delay = config.get("delay", 1)
                # Exponential backoff
                return min(base_delay * (2 ** (attempt_number - 1)), 10)
        
        # Default delay with exponential backoff
        return min(2 ** (attempt_number - 1), 10)
    
    def get_retry_summary(self, feature_id: str) -> Dict[str, Any]:
        """Get summary of retry attempts for a feature"""
        if feature_id not in self.retry_history:
            return {"total_retries": 0}
        
        history = self.retry_history[feature_id]
        
        summary = {
            "total_retries": len(history),
            "by_phase": defaultdict(int),
            "error_types": defaultdict(int),
            "stagnation_detected": False
        }
        
        # Count by phase and error type
        for attempt in history:
            phase = attempt["phase"]
            summary["by_phase"][phase] += 1
            
            # Identify error type
            error_type, _ = self._analyze_error(attempt["error"])
            if error_type:
                summary["error_types"][error_type] += 1
        
        # Check for stagnation in any phase
        for phase in TDDPhase:
            if self._detect_stagnation(feature_id, phase):
                summary["stagnation_detected"] = True
                break
        
        return dict(summary)
    
    def clear_history(self, feature_id: str):
        """Clear retry history for a feature"""
        if feature_id in self.retry_history:
            del self.retry_history[feature_id]
    
    def get_adaptive_suggestions(self, feature_id: str) -> List[str]:
        """Get adaptive suggestions based on retry history"""
        if feature_id not in self.retry_history:
            return []
        
        history = self.retry_history[feature_id]
        if len(history) < 2:
            return []
        
        suggestions = []
        
        # Analyze patterns across attempts
        error_types = defaultdict(int)
        for attempt in history:
            error_type, _ = self._analyze_error(attempt["error"])
            if error_type:
                error_types[error_type] += 1
        
        # Suggest based on most common error type
        if error_types:
            most_common = max(error_types.items(), key=lambda x: x[1])[0]
            if most_common == "syntax_error" and error_types[most_common] > 2:
                suggestions.append("Consider using a linter or syntax checker before execution")
            elif most_common == "assertion_error" and error_types[most_common] > 2:
                suggestions.append("Review the requirements - tests may not match intended behavior")
        
        # Check if switching between different error types
        if len(set(error_types.keys())) > 3:
            suggestions.append("Multiple different errors - consider breaking down the feature into smaller parts")
        
        return suggestions