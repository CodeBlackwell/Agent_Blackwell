"""
Stagnation detection system for incremental development workflow.
Tracks progress patterns and identifies when development is stuck.
"""
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import re
from collections import defaultdict


class StagnationType(Enum):
    """Types of stagnation patterns."""
    REPEATED_ERROR = "repeated_error"
    NO_PROGRESS = "no_progress"
    CYCLIC_FAILURE = "cyclic_failure"
    DIMINISHING_RETURNS = "diminishing_returns"
    PERSISTENT_TEST_FAILURE = "persistent_test_failure"


@dataclass
class ErrorPattern:
    """Represents a pattern of errors."""
    error_type: str
    error_message: str
    occurrences: int = 1
    first_seen: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)
    affected_files: Set[str] = field(default_factory=set)
    
    def is_similar(self, error_message: str, threshold: float = 0.8) -> bool:
        """Check if an error message is similar to this pattern."""
        # Simple similarity check - can be enhanced with fuzzy matching
        if self.error_message == error_message:
            return True
        
        # Check for common patterns
        if self.error_type in error_message:
            return True
        
        # Check for similar structure (e.g., same error on different line numbers)
        pattern1 = re.sub(r'\d+', 'NUM', self.error_message)
        pattern2 = re.sub(r'\d+', 'NUM', error_message)
        
        return pattern1 == pattern2


@dataclass
class ProgressMetrics:
    """Tracks progress metrics for a feature."""
    feature_id: str
    total_attempts: int = 0
    successful_validations: List[str] = field(default_factory=list)
    failed_validations: List[Dict[str, str]] = field(default_factory=list)
    error_patterns: List[ErrorPattern] = field(default_factory=list)
    code_changes: List[int] = field(default_factory=list)  # Lines changed per attempt
    test_results: List[Tuple[int, int]] = field(default_factory=list)  # (passed, failed) per attempt
    time_spent: List[float] = field(default_factory=list)  # Time per attempt
    
    def get_progress_rate(self) -> float:
        """Calculate rate of progress (0-1)."""
        # If we have test results, track improvement in passing tests
        if self.test_results and len(self.test_results) >= 2:
            initial_passed = self.test_results[0][0] if self.test_results[0] else 0
            latest_passed = self.test_results[-1][0] if self.test_results[-1] else 0
            total_tests = self.test_results[-1][0] + self.test_results[-1][1]
            
            if total_tests > 0:
                progress = (latest_passed - initial_passed) / total_tests
                return max(0.0, min(1.0, progress))
        
        # Fallback: ratio of successful validations
        if self.total_attempts > 0:
            return len(self.successful_validations) / self.total_attempts
        
        return 0.0
    
    def get_stagnation_score(self) -> float:
        """Calculate stagnation score (0-1, higher means more stagnant)."""
        score = 0.0
        
        # Check for repeated errors
        if self.error_patterns:
            max_occurrences = max(p.occurrences for p in self.error_patterns)
            if max_occurrences > 2:
                score += 0.3 * min(1.0, max_occurrences / 5)
        
        # Check for lack of progress
        progress_rate = self.get_progress_rate()
        if self.total_attempts > 3 and progress_rate < 0.2:
            score += 0.3
        
        # Check for diminishing code changes
        if len(self.code_changes) >= 3:
            recent_changes = self.code_changes[-3:]
            if all(c < 10 for c in recent_changes):
                score += 0.2
        
        # Check for consistent test failures
        if len(self.test_results) >= 3:
            recent_failures = [failed for _, failed in self.test_results[-3:]]
            if all(f > 0 and f == recent_failures[0] for f in recent_failures):
                score += 0.2
        
        return min(1.0, score)


class StagnationDetector:
    """
    Detects stagnation patterns in incremental development.
    """
    
    def __init__(self, 
                 stagnation_threshold: float = 0.7,
                 min_attempts_before_detection: int = 3):
        self.stagnation_threshold = stagnation_threshold
        self.min_attempts_before_detection = min_attempts_before_detection
        self.feature_metrics: Dict[str, ProgressMetrics] = {}
        self.global_patterns: List[ErrorPattern] = []
    
    def record_attempt(self, 
                      feature_id: str,
                      success: bool,
                      error_message: Optional[str] = None,
                      files_changed: Optional[List[str]] = None,
                      code_diff_size: Optional[int] = None,
                      test_results: Optional[Tuple[int, int]] = None,
                      duration: Optional[float] = None):
        """Record an attempt for a feature."""
        if feature_id not in self.feature_metrics:
            self.feature_metrics[feature_id] = ProgressMetrics(feature_id=feature_id)
        
        metrics = self.feature_metrics[feature_id]
        metrics.total_attempts += 1
        
        if success:
            metrics.successful_validations.append(datetime.now().isoformat())
        else:
            metrics.failed_validations.append({
                "timestamp": datetime.now().isoformat(),
                "error": error_message or "Unknown error"
            })
            
            if error_message:
                self._record_error_pattern(metrics, error_message, files_changed)
        
        if code_diff_size is not None:
            metrics.code_changes.append(code_diff_size)
        
        if test_results is not None:
            metrics.test_results.append(test_results)
        
        if duration is not None:
            metrics.time_spent.append(duration)
    
    def _record_error_pattern(self, 
                             metrics: ProgressMetrics, 
                             error_message: str,
                             files_changed: Optional[List[str]] = None):
        """Record and categorize error patterns."""
        # Extract error type
        error_type = "generic"
        if "SyntaxError" in error_message:
            error_type = "syntax"
        elif "ImportError" in error_message or "ModuleNotFoundError" in error_message:
            error_type = "import"
        elif "AttributeError" in error_message:
            error_type = "attribute"
        elif "TypeError" in error_message:
            error_type = "type"
        elif "test" in error_message.lower() and "fail" in error_message.lower():
            error_type = "test_failure"
        
        # Check if this matches an existing pattern
        for pattern in metrics.error_patterns:
            if pattern.error_type == error_type and pattern.is_similar(error_message):
                pattern.occurrences += 1
                pattern.last_seen = datetime.now()
                if files_changed:
                    pattern.affected_files.update(files_changed)
                return
        
        # Create new pattern
        new_pattern = ErrorPattern(
            error_type=error_type,
            error_message=error_message,
            affected_files=set(files_changed) if files_changed else set()
        )
        metrics.error_patterns.append(new_pattern)
    
    def detect_stagnation(self, feature_id: str) -> Optional[Dict[str, any]]:
        """
        Detect if a feature is stagnating.
        
        Returns:
            Dictionary with stagnation details if detected, None otherwise
        """
        if feature_id not in self.feature_metrics:
            return None
        
        metrics = self.feature_metrics[feature_id]
        
        # Don't detect stagnation too early
        if metrics.total_attempts < self.min_attempts_before_detection:
            return None
        
        stagnation_score = metrics.get_stagnation_score()
        
        if stagnation_score >= self.stagnation_threshold:
            # Determine stagnation type
            stagnation_types = []
            
            # Check for repeated errors
            max_error_occurrences = max(
                (p.occurrences for p in metrics.error_patterns), 
                default=0
            )
            if max_error_occurrences >= 3:
                stagnation_types.append(StagnationType.REPEATED_ERROR)
            
            # Check for no progress
            if metrics.get_progress_rate() < 0.1:
                stagnation_types.append(StagnationType.NO_PROGRESS)
            
            # Check for cyclic failures
            if len(metrics.error_patterns) >= 3:
                unique_errors = len(set(p.error_type for p in metrics.error_patterns))
                if unique_errors <= 2 and sum(p.occurrences for p in metrics.error_patterns) > 6:
                    stagnation_types.append(StagnationType.CYCLIC_FAILURE)
            
            # Check for diminishing returns
            if len(metrics.code_changes) >= 3:
                recent_avg = sum(metrics.code_changes[-3:]) / 3
                if recent_avg < 5:
                    stagnation_types.append(StagnationType.DIMINISHING_RETURNS)
            
            # Get most common error pattern
            most_common_error = max(
                metrics.error_patterns,
                key=lambda p: p.occurrences,
                default=None
            )
            
            return {
                "stagnation_score": stagnation_score,
                "stagnation_types": [t.value for t in stagnation_types],
                "total_attempts": metrics.total_attempts,
                "progress_rate": metrics.get_progress_rate(),
                "most_common_error": {
                    "type": most_common_error.error_type,
                    "message": most_common_error.error_message,
                    "occurrences": most_common_error.occurrences,
                    "affected_files": list(most_common_error.affected_files)
                } if most_common_error else None,
                "recommendation": self._get_recommendation(stagnation_types, metrics)
            }
        
        return None
    
    def _get_recommendation(self, 
                           stagnation_types: List[StagnationType], 
                           metrics: ProgressMetrics) -> str:
        """Get recommendation based on stagnation type."""
        if StagnationType.REPEATED_ERROR in stagnation_types:
            return "Consider a different approach - the same error keeps occurring"
        elif StagnationType.CYCLIC_FAILURE in stagnation_types:
            return "Break the cycle by addressing root cause or simplifying the feature"
        elif StagnationType.DIMINISHING_RETURNS in stagnation_types:
            return "Current approach may be exhausted - try a fresh perspective"
        elif StagnationType.NO_PROGRESS in stagnation_types:
            if metrics.total_attempts > 5:
                return "Feature may be too complex - consider breaking it down"
            else:
                return "Review the requirements and validation criteria"
        else:
            return "Consider alternative implementation strategies"
    
    def get_feature_summary(self, feature_id: str) -> Optional[Dict[str, any]]:
        """Get a summary of progress for a feature."""
        if feature_id not in self.feature_metrics:
            return None
        
        metrics = self.feature_metrics[feature_id]
        
        return {
            "feature_id": feature_id,
            "total_attempts": metrics.total_attempts,
            "successful_validations": len(metrics.successful_validations),
            "progress_rate": metrics.get_progress_rate(),
            "stagnation_score": metrics.get_stagnation_score(),
            "unique_error_types": len(set(p.error_type for p in metrics.error_patterns)),
            "most_recent_errors": [
                {"type": p.error_type, "message": p.error_message[:100]}
                for p in sorted(metrics.error_patterns, 
                              key=lambda x: x.last_seen, 
                              reverse=True)[:3]
            ],
            "average_time_per_attempt": (
                sum(metrics.time_spent) / len(metrics.time_spent)
                if metrics.time_spent else None
            )
        }
    
    def should_skip_feature(self, feature_id: str) -> bool:
        """Determine if a feature should be skipped due to stagnation."""
        stagnation = self.detect_stagnation(feature_id)
        
        if not stagnation:
            return False
        
        # Skip if stagnation is severe and we've tried many times
        metrics = self.feature_metrics[feature_id]
        if (stagnation["stagnation_score"] >= 0.8 and 
            metrics.total_attempts >= 5):
            return True
        
        # Skip if we've made absolutely no progress after many attempts
        if (metrics.get_progress_rate() == 0 and 
            metrics.total_attempts >= 7):
            return True
        
        return False
    
    def suggest_alternative_approach(self, feature_id: str) -> Optional[str]:
        """Suggest an alternative approach based on failure patterns."""
        if feature_id not in self.feature_metrics:
            return None
        
        metrics = self.feature_metrics[feature_id]
        
        if not metrics.error_patterns:
            return None
        
        # Analyze error patterns to suggest alternatives
        error_types = defaultdict(int)
        for pattern in metrics.error_patterns:
            error_types[pattern.error_type] += pattern.occurrences
        
        most_common_type = max(error_types.items(), key=lambda x: x[1])[0]
        
        suggestions = {
            "syntax": "Simplify the code structure and validate syntax before execution",
            "import": "Review dependencies and ensure all required modules are available",
            "attribute": "Check object initialization and method availability",
            "type": "Review data types and ensure type consistency",
            "test_failure": "Focus on making one test pass at a time rather than all at once",
            "generic": "Try breaking down the feature into smaller, more manageable parts"
        }
        
        return suggestions.get(most_common_type, suggestions["generic"])