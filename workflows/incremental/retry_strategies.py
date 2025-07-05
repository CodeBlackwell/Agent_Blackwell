"""
Advanced retry strategies with adaptive approaches for incremental development.
"""
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import math
from abc import ABC, abstractmethod


class RetryStrategy(Enum):
    """Types of retry strategies."""
    IMMEDIATE = "immediate"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    ADAPTIVE = "adaptive"
    DECOMPOSITION = "decomposition"
    ALTERNATIVE_APPROACH = "alternative_approach"
    SKIP_AND_CONTINUE = "skip_and_continue"


@dataclass
class RetryContext:
    """Context information for retry decisions."""
    feature_id: str
    attempt_number: int
    total_attempts: int
    error_history: List[str]
    error_categories: List[str]
    time_spent: float
    code_changes_size: List[int]
    test_progress: List[Tuple[int, int]]  # (passed, failed) per attempt
    complexity_level: str
    dependencies: List[str] = field(default_factory=list)
    
    def get_error_pattern(self) -> str:
        """Identify error pattern from history."""
        if not self.error_categories:
            return "unknown"
        
        # Check for repeating errors
        if len(set(self.error_categories)) == 1:
            return "repeated_same_error"
        
        # Check for cycling errors
        if len(self.error_categories) > 2:
            if self.error_categories[-1] == self.error_categories[-3]:
                return "cycling_errors"
        
        # Check for progress
        if self.test_progress and len(self.test_progress) > 1:
            initial_passed = self.test_progress[0][0] if self.test_progress[0] else 0
            latest_passed = self.test_progress[-1][0] if self.test_progress[-1] else 0
            if latest_passed > initial_passed:
                return "making_progress"
            elif latest_passed == initial_passed:
                return "no_test_progress"
        
        return "varied_errors"


@dataclass
class RetryDecision:
    """Decision about how to retry."""
    should_retry: bool
    strategy: RetryStrategy
    delay_seconds: float = 0.0
    modifications: Dict[str, Any] = field(default_factory=dict)
    reason: str = ""
    
    def get_modified_context(self, original_context: str) -> str:
        """Apply modifications to the original context."""
        modified = original_context
        
        if "additional_hints" in self.modifications:
            modified += f"\n\nADDITIONAL HINTS:\n{self.modifications['additional_hints']}"
        
        if "focus_areas" in self.modifications:
            modified += f"\n\nFOCUS ON:\n"
            for area in self.modifications['focus_areas']:
                modified += f"- {area}\n"
        
        if "skip_components" in self.modifications:
            modified += f"\n\nSKIP FOR NOW:\n"
            for component in self.modifications['skip_components']:
                modified += f"- {component}\n"
        
        return modified


class BaseRetryStrategy(ABC):
    """Base class for retry strategies."""
    
    @abstractmethod
    def should_retry(self, context: RetryContext) -> bool:
        """Determine if we should retry."""
        pass
    
    @abstractmethod
    def get_delay(self, context: RetryContext) -> float:
        """Get delay before retry in seconds."""
        pass
    
    @abstractmethod
    def get_modifications(self, context: RetryContext) -> Dict[str, Any]:
        """Get modifications to apply for retry."""
        pass


class ExponentialBackoffStrategy(BaseRetryStrategy):
    """Exponential backoff with jitter."""
    
    def __init__(self, base_delay: float = 1.0, max_delay: float = 30.0):
        self.base_delay = base_delay
        self.max_delay = max_delay
    
    def should_retry(self, context: RetryContext) -> bool:
        return context.attempt_number < context.total_attempts
    
    def get_delay(self, context: RetryContext) -> float:
        delay = min(
            self.base_delay * (2 ** (context.attempt_number - 1)),
            self.max_delay
        )
        # Add jitter
        import random
        jitter = random.uniform(0, delay * 0.1)
        return delay + jitter
    
    def get_modifications(self, context: RetryContext) -> Dict[str, Any]:
        return {}


class AdaptiveStrategy(BaseRetryStrategy):
    """Adaptive strategy that changes approach based on error patterns."""
    
    def should_retry(self, context: RetryContext) -> bool:
        # Don't retry if we're making no progress after many attempts
        if context.attempt_number >= 5:
            pattern = context.get_error_pattern()
            if pattern in ["repeated_same_error", "no_test_progress"]:
                return False
        
        return context.attempt_number < context.total_attempts
    
    def get_delay(self, context: RetryContext) -> float:
        # Adaptive delay based on error pattern
        pattern = context.get_error_pattern()
        
        if pattern == "repeated_same_error":
            # Longer delay for repeated errors
            return min(5.0 * context.attempt_number, 30.0)
        elif pattern == "making_progress":
            # Shorter delay when making progress
            return 1.0
        else:
            # Standard exponential backoff
            return min(2.0 ** (context.attempt_number - 1), 15.0)
    
    def get_modifications(self, context: RetryContext) -> Dict[str, Any]:
        pattern = context.get_error_pattern()
        modifications = {}
        
        if pattern == "repeated_same_error":
            # Suggest alternative approach
            modifications["additional_hints"] = (
                "The same error keeps occurring. Try a different approach:\n"
                "- Simplify the implementation\n"
                "- Break down complex logic\n"
                "- Check assumptions about the requirements"
            )
        
        elif pattern == "cycling_errors":
            # Focus on one issue at a time
            modifications["focus_areas"] = [
                "Fix one error type completely before moving to the next",
                "Ensure changes don't reintroduce previous errors"
            ]
        
        elif pattern == "no_test_progress":
            # Provide test-specific guidance
            if context.test_progress:
                _, failed = context.test_progress[-1]
                modifications["additional_hints"] = (
                    f"No test progress after {context.attempt_number} attempts. "
                    f"Still {failed} failing tests.\n"
                    "- Run tests locally to see exact failures\n"
                    "- Focus on making one test pass at a time\n"
                    "- Check test expectations vs implementation"
                )
        
        return modifications


class DecompositionStrategy(BaseRetryStrategy):
    """Strategy that decomposes complex features into smaller parts."""
    
    def should_retry(self, context: RetryContext) -> bool:
        # Only use decomposition for complex features after initial failures
        return (context.complexity_level == "high" and 
                context.attempt_number >= 3 and 
                context.attempt_number < context.total_attempts)
    
    def get_delay(self, context: RetryContext) -> float:
        return 2.0  # Fixed delay for decomposition
    
    def get_modifications(self, context: RetryContext) -> Dict[str, Any]:
        return {
            "decompose": True,
            "additional_hints": (
                "This feature is complex. Let's break it down:\n"
                "1. Implement core functionality first\n"
                "2. Add error handling\n"
                "3. Implement edge cases\n"
                "4. Add optimizations last"
            ),
            "focus_areas": [
                "Start with the simplest working version",
                "Ensure basic functionality works before adding complexity"
            ]
        }


class AlternativeApproachStrategy(BaseRetryStrategy):
    """Strategy that suggests alternative implementations."""
    
    def __init__(self):
        self.approach_suggestions = {
            "syntax_error": [
                "Rewrite the problematic section from scratch",
                "Use simpler Python constructs",
                "Break complex expressions into multiple lines"
            ],
            "import_error": [
                "Use relative imports instead of absolute",
                "Check if all dependencies are in the codebase",
                "Consider implementing missing dependencies inline"
            ],
            "test_failure": [
                "Study the test requirements more carefully",
                "Implement the exact behavior the test expects",
                "Add debug prints to understand test failures"
            ]
        }
    
    def should_retry(self, context: RetryContext) -> bool:
        # Use alternative approach after multiple failures
        return (context.attempt_number >= 2 and 
                context.attempt_number < context.total_attempts and
                context.get_error_pattern() in ["repeated_same_error", "cycling_errors"])
    
    def get_delay(self, context: RetryContext) -> float:
        return 3.0  # Give time to process alternative approach
    
    def get_modifications(self, context: RetryContext) -> Dict[str, Any]:
        # Get the most common error category
        if context.error_categories:
            most_common = max(set(context.error_categories), key=context.error_categories.count)
            suggestions = self.approach_suggestions.get(most_common, [])
            
            return {
                "alternative_approach": True,
                "additional_hints": (
                    f"Alternative approaches for {most_common}:\n" + 
                    "\n".join(f"- {s}" for s in suggestions)
                )
            }
        
        return {}


class RetryOrchestrator:
    """Orchestrates retry decisions using multiple strategies."""
    
    def __init__(self):
        self.strategies = {
            RetryStrategy.EXPONENTIAL_BACKOFF: ExponentialBackoffStrategy(),
            RetryStrategy.ADAPTIVE: AdaptiveStrategy(),
            RetryStrategy.DECOMPOSITION: DecompositionStrategy(),
            RetryStrategy.ALTERNATIVE_APPROACH: AlternativeApproachStrategy()
        }
        
        # Track retry effectiveness
        self.strategy_success_rate: Dict[RetryStrategy, float] = {}
        self.strategy_usage_count: Dict[RetryStrategy, int] = {}
    
    def decide_retry(self, context: RetryContext) -> RetryDecision:
        """Make a retry decision based on context."""
        # First, check if we've exhausted retries
        if context.attempt_number >= context.total_attempts:
            return RetryDecision(
                should_retry=False,
                strategy=RetryStrategy.SKIP_AND_CONTINUE,
                reason="Maximum retry attempts reached"
            )
        
        # Evaluate each strategy
        strategy_scores = {}
        
        for strategy_type, strategy in self.strategies.items():
            if strategy.should_retry(context):
                # Base score
                score = 1.0
                
                # Adjust based on historical success
                if strategy_type in self.strategy_success_rate:
                    score *= (1 + self.strategy_success_rate[strategy_type])
                
                # Adjust based on context
                if strategy_type == RetryStrategy.ADAPTIVE:
                    score *= 1.5  # Prefer adaptive by default
                elif strategy_type == RetryStrategy.DECOMPOSITION:
                    if context.complexity_level == "high":
                        score *= 2.0
                elif strategy_type == RetryStrategy.ALTERNATIVE_APPROACH:
                    if context.get_error_pattern() == "repeated_same_error":
                        score *= 1.8
                
                strategy_scores[strategy_type] = score
        
        if not strategy_scores:
            return RetryDecision(
                should_retry=False,
                strategy=RetryStrategy.SKIP_AND_CONTINUE,
                reason="No suitable retry strategy found"
            )
        
        # Select best strategy
        best_strategy = max(strategy_scores.items(), key=lambda x: x[1])[0]
        selected = self.strategies[best_strategy]
        
        # Track usage
        self.strategy_usage_count[best_strategy] = self.strategy_usage_count.get(best_strategy, 0) + 1
        
        return RetryDecision(
            should_retry=True,
            strategy=best_strategy,
            delay_seconds=selected.get_delay(context),
            modifications=selected.get_modifications(context),
            reason=f"Using {best_strategy.value} strategy"
        )
    
    def record_outcome(self, strategy: RetryStrategy, success: bool):
        """Record the outcome of a retry strategy."""
        # Update success rate using exponential moving average
        current_rate = self.strategy_success_rate.get(strategy, 0.5)
        self.strategy_success_rate[strategy] = 0.7 * current_rate + 0.3 * (1.0 if success else 0.0)
    
    def get_strategy_report(self) -> Dict[str, Any]:
        """Get report on strategy effectiveness."""
        report = {}
        
        for strategy in RetryStrategy:
            usage = self.strategy_usage_count.get(strategy, 0)
            success_rate = self.strategy_success_rate.get(strategy, 0.0)
            
            report[strategy.value] = {
                "usage_count": usage,
                "success_rate": success_rate,
                "effectiveness": success_rate * usage if usage > 0 else 0
            }
        
        return report