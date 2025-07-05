"""
Unit tests for the retry strategies system
"""
import pytest
from workflows.incremental.retry_strategies import (
    RetryStrategy, RetryContext, RetryDecision,
    ExponentialBackoffStrategy, AdaptiveStrategy,
    DecompositionStrategy, AlternativeApproachStrategy,
    RetryOrchestrator
)


class TestRetryContext:
    """Test RetryContext functionality"""
    
    def test_retry_context_initialization(self):
        """Test RetryContext initialization"""
        context = RetryContext(
            feature_id="f1",
            attempt_number=3,
            total_attempts=5,
            error_history=["Error 1", "Error 2"],
            error_categories=["syntax", "import"],
            time_spent=10.5,
            code_changes_size=[100, 50],
            test_progress=[(2, 8), (5, 5)],
            complexity_level="medium"
        )
        
        assert context.feature_id == "f1"
        assert context.attempt_number == 3
        assert context.total_attempts == 5
        assert len(context.error_history) == 2
        assert len(context.error_categories) == 2
        assert context.time_spent == 10.5
        assert context.code_changes_size == [100, 50]
        assert context.test_progress == [(2, 8), (5, 5)]
        assert context.complexity_level == "medium"
        assert context.dependencies == []
    
    def test_get_error_pattern_repeated_same(self):
        """Test error pattern detection for repeated same error"""
        context = RetryContext(
            feature_id="f1",
            attempt_number=3,
            total_attempts=5,
            error_history=[],
            error_categories=["syntax", "syntax", "syntax"],
            time_spent=0,
            code_changes_size=[],
            test_progress=[],
            complexity_level="low"
        )
        
        assert context.get_error_pattern() == "repeated_same_error"
    
    def test_get_error_pattern_cycling(self):
        """Test error pattern detection for cycling errors"""
        context = RetryContext(
            feature_id="f1",
            attempt_number=5,
            total_attempts=10,
            error_history=[],
            error_categories=["syntax", "import", "syntax", "import", "syntax"],
            time_spent=0,
            code_changes_size=[],
            test_progress=[],
            complexity_level="low"
        )
        
        assert context.get_error_pattern() == "cycling_errors"
    
    def test_get_error_pattern_making_progress(self):
        """Test error pattern detection when making progress"""
        context = RetryContext(
            feature_id="f1",
            attempt_number=3,
            total_attempts=5,
            error_history=[],
            error_categories=["test"],
            time_spent=0,
            code_changes_size=[],
            test_progress=[(2, 8), (5, 5), (7, 3)],
            complexity_level="low"
        )
        
        assert context.get_error_pattern() == "making_progress"
    
    def test_get_error_pattern_no_test_progress(self):
        """Test error pattern detection with no test progress"""
        context = RetryContext(
            feature_id="f1",
            attempt_number=3,
            total_attempts=5,
            error_history=[],
            error_categories=["test"],
            time_spent=0,
            code_changes_size=[],
            test_progress=[(2, 8), (2, 8), (2, 8)],
            complexity_level="low"
        )
        
        assert context.get_error_pattern() == "no_test_progress"
    
    def test_get_error_pattern_varied(self):
        """Test error pattern detection for varied errors"""
        context = RetryContext(
            feature_id="f1",
            attempt_number=3,
            total_attempts=5,
            error_history=[],
            error_categories=["syntax", "import", "test"],
            time_spent=0,
            code_changes_size=[],
            test_progress=[],
            complexity_level="low"
        )
        
        assert context.get_error_pattern() == "varied_errors"


class TestRetryDecision:
    """Test RetryDecision functionality"""
    
    def test_retry_decision_initialization(self):
        """Test RetryDecision initialization"""
        decision = RetryDecision(
            should_retry=True,
            strategy=RetryStrategy.ADAPTIVE,
            delay_seconds=5.0,
            modifications={"focus_areas": ["Fix imports"]},
            reason="Using adaptive strategy"
        )
        
        assert decision.should_retry is True
        assert decision.strategy == RetryStrategy.ADAPTIVE
        assert decision.delay_seconds == 5.0
        assert decision.modifications == {"focus_areas": ["Fix imports"]}
        assert decision.reason == "Using adaptive strategy"
    
    def test_get_modified_context_with_hints(self):
        """Test context modification with additional hints"""
        decision = RetryDecision(
            should_retry=True,
            strategy=RetryStrategy.ADAPTIVE,
            modifications={"additional_hints": "Try a simpler approach"}
        )
        
        original = "Original context"
        modified = decision.get_modified_context(original)
        
        assert "Original context" in modified
        assert "ADDITIONAL HINTS:" in modified
        assert "Try a simpler approach" in modified
    
    def test_get_modified_context_with_focus_areas(self):
        """Test context modification with focus areas"""
        decision = RetryDecision(
            should_retry=True,
            strategy=RetryStrategy.ADAPTIVE,
            modifications={"focus_areas": ["Fix syntax errors", "Simplify logic"]}
        )
        
        original = "Original context"
        modified = decision.get_modified_context(original)
        
        assert "FOCUS ON:" in modified
        assert "- Fix syntax errors" in modified
        assert "- Simplify logic" in modified
    
    def test_get_modified_context_with_skip_components(self):
        """Test context modification with skip components"""
        decision = RetryDecision(
            should_retry=True,
            strategy=RetryStrategy.ADAPTIVE,
            modifications={"skip_components": ["Advanced features", "Optimizations"]}
        )
        
        original = "Original context"
        modified = decision.get_modified_context(original)
        
        assert "SKIP FOR NOW:" in modified
        assert "- Advanced features" in modified
        assert "- Optimizations" in modified


class TestExponentialBackoffStrategy:
    """Test ExponentialBackoffStrategy"""
    
    def test_should_retry(self):
        """Test retry decision logic"""
        strategy = ExponentialBackoffStrategy()
        
        context = RetryContext(
            feature_id="f1",
            attempt_number=3,
            total_attempts=5,
            error_history=[],
            error_categories=[],
            time_spent=0,
            code_changes_size=[],
            test_progress=[],
            complexity_level="low"
        )
        
        assert strategy.should_retry(context) is True
        
        # At max attempts
        context.attempt_number = 5
        assert strategy.should_retry(context) is False
    
    def test_get_delay(self):
        """Test delay calculation"""
        strategy = ExponentialBackoffStrategy(base_delay=2.0, max_delay=20.0)
        
        context = RetryContext(
            feature_id="f1",
            attempt_number=1,
            total_attempts=5,
            error_history=[],
            error_categories=[],
            time_spent=0,
            code_changes_size=[],
            test_progress=[],
            complexity_level="low"
        )
        
        # First attempt: base_delay * 2^0 = 2.0 (plus jitter)
        delay = strategy.get_delay(context)
        assert 2.0 <= delay <= 2.2  # With jitter
        
        # Third attempt: base_delay * 2^2 = 8.0 (plus jitter)
        context.attempt_number = 3
        delay = strategy.get_delay(context)
        assert 8.0 <= delay <= 8.8
        
        # Should cap at max_delay
        context.attempt_number = 10
        delay = strategy.get_delay(context)
        assert delay <= 20.0 * 1.1  # Max delay plus jitter
    
    def test_get_modifications(self):
        """Test that exponential backoff has no modifications"""
        strategy = ExponentialBackoffStrategy()
        context = RetryContext(
            feature_id="f1",
            attempt_number=1,
            total_attempts=5,
            error_history=[],
            error_categories=[],
            time_spent=0,
            code_changes_size=[],
            test_progress=[],
            complexity_level="low"
        )
        
        assert strategy.get_modifications(context) == {}


class TestAdaptiveStrategy:
    """Test AdaptiveStrategy"""
    
    def test_should_retry_with_progress(self):
        """Test retry decision when making progress"""
        strategy = AdaptiveStrategy()
        
        context = RetryContext(
            feature_id="f1",
            attempt_number=3,
            total_attempts=5,
            error_history=[],
            error_categories=["test"],
            time_spent=0,
            code_changes_size=[],
            test_progress=[(2, 8), (5, 5)],
            complexity_level="medium"
        )
        
        assert strategy.should_retry(context) is True
    
    def test_should_not_retry_repeated_errors(self):
        """Test retry decision with repeated errors after many attempts"""
        strategy = AdaptiveStrategy()
        
        context = RetryContext(
            feature_id="f1",
            attempt_number=6,
            total_attempts=10,
            error_history=[],
            error_categories=["syntax"] * 6,
            time_spent=0,
            code_changes_size=[],
            test_progress=[],
            complexity_level="medium"
        )
        
        assert strategy.should_retry(context) is False
    
    def test_get_delay_based_on_pattern(self):
        """Test adaptive delay based on error patterns"""
        strategy = AdaptiveStrategy()
        
        # Repeated same error - longer delay
        context = RetryContext(
            feature_id="f1",
            attempt_number=3,
            total_attempts=5,
            error_history=[],
            error_categories=["syntax", "syntax", "syntax"],
            time_spent=0,
            code_changes_size=[],
            test_progress=[],
            complexity_level="medium"
        )
        
        delay = strategy.get_delay(context)
        assert delay == 15.0  # 5.0 * attempt_number
        
        # Making progress - shorter delay
        context.test_progress = [(2, 8), (5, 5), (7, 3)]
        delay = strategy.get_delay(context)
        assert delay == 1.0
    
    def test_get_modifications_for_patterns(self):
        """Test modifications based on error patterns"""
        strategy = AdaptiveStrategy()
        
        # Repeated same error
        context = RetryContext(
            feature_id="f1",
            attempt_number=3,
            total_attempts=5,
            error_history=[],
            error_categories=["syntax", "syntax", "syntax"],
            time_spent=0,
            code_changes_size=[],
            test_progress=[],
            complexity_level="medium"
        )
        
        mods = strategy.get_modifications(context)
        assert "additional_hints" in mods
        assert "different approach" in mods["additional_hints"]
        
        # Cycling errors
        context.error_categories = ["syntax", "import", "syntax", "import"]
        mods = strategy.get_modifications(context)
        assert "focus_areas" in mods
        assert any("one error type" in area for area in mods["focus_areas"])


class TestDecompositionStrategy:
    """Test DecompositionStrategy"""
    
    def test_should_retry_for_complex_features(self):
        """Test retry decision for complex features"""
        strategy = DecompositionStrategy()
        
        # Should not retry for simple features
        context = RetryContext(
            feature_id="f1",
            attempt_number=3,
            total_attempts=5,
            error_history=[],
            error_categories=[],
            time_spent=0,
            code_changes_size=[],
            test_progress=[],
            complexity_level="low"
        )
        
        assert strategy.should_retry(context) is False
        
        # Should retry for complex features after initial failures
        context.complexity_level = "high"
        assert strategy.should_retry(context) is True
        
        # Not before 3 attempts
        context.attempt_number = 2
        assert strategy.should_retry(context) is False
    
    def test_get_delay(self):
        """Test fixed delay for decomposition"""
        strategy = DecompositionStrategy()
        context = RetryContext(
            feature_id="f1",
            attempt_number=3,
            total_attempts=5,
            error_history=[],
            error_categories=[],
            time_spent=0,
            code_changes_size=[],
            test_progress=[],
            complexity_level="high"
        )
        
        assert strategy.get_delay(context) == 2.0
    
    def test_get_modifications(self):
        """Test decomposition modifications"""
        strategy = DecompositionStrategy()
        context = RetryContext(
            feature_id="f1",
            attempt_number=3,
            total_attempts=5,
            error_history=[],
            error_categories=[],
            time_spent=0,
            code_changes_size=[],
            test_progress=[],
            complexity_level="high"
        )
        
        mods = strategy.get_modifications(context)
        assert mods["decompose"] is True
        assert "additional_hints" in mods
        assert "break it down" in mods["additional_hints"]
        assert "focus_areas" in mods
        assert any("simplest working version" in area for area in mods["focus_areas"])


class TestAlternativeApproachStrategy:
    """Test AlternativeApproachStrategy"""
    
    def test_should_retry_conditions(self):
        """Test retry conditions for alternative approach"""
        strategy = AlternativeApproachStrategy()
        
        # Should not retry on first attempt
        context = RetryContext(
            feature_id="f1",
            attempt_number=1,
            total_attempts=5,
            error_history=[],
            error_categories=["syntax"],
            time_spent=0,
            code_changes_size=[],
            test_progress=[],
            complexity_level="medium"
        )
        
        assert strategy.should_retry(context) is False
        
        # Should retry after multiple failures with repeated errors
        context.attempt_number = 3
        context.error_categories = ["syntax", "syntax", "syntax"]
        assert strategy.should_retry(context) is True
    
    def test_get_modifications_for_error_types(self):
        """Test modifications based on error types"""
        strategy = AlternativeApproachStrategy()
        
        # Syntax errors
        context = RetryContext(
            feature_id="f1",
            attempt_number=3,
            total_attempts=5,
            error_history=[],
            error_categories=["syntax_error", "syntax_error"],
            time_spent=0,
            code_changes_size=[],
            test_progress=[],
            complexity_level="medium"
        )
        
        mods = strategy.get_modifications(context)
        assert "alternative_approach" in mods
        assert mods["alternative_approach"] is True
        assert "additional_hints" in mods
        assert "syntax_error" in mods["additional_hints"]
        
        # Import errors
        context.error_categories = ["import_error", "import_error"]
        mods = strategy.get_modifications(context)
        assert "import_error" in mods["additional_hints"]
        assert "relative imports" in mods["additional_hints"]


class TestRetryOrchestrator:
    """Test RetryOrchestrator"""
    
    @pytest.fixture
    def orchestrator(self):
        """Create a RetryOrchestrator instance"""
        return RetryOrchestrator()
    
    def test_orchestrator_initialization(self, orchestrator):
        """Test orchestrator initialization"""
        assert len(orchestrator.strategies) == 4
        assert RetryStrategy.EXPONENTIAL_BACKOFF in orchestrator.strategies
        assert RetryStrategy.ADAPTIVE in orchestrator.strategies
        assert RetryStrategy.DECOMPOSITION in orchestrator.strategies
        assert RetryStrategy.ALTERNATIVE_APPROACH in orchestrator.strategies
        assert orchestrator.strategy_success_rate == {}
        assert orchestrator.strategy_usage_count == {}
    
    def test_decide_retry_max_attempts_reached(self, orchestrator):
        """Test decision when max attempts reached"""
        context = RetryContext(
            feature_id="f1",
            attempt_number=5,
            total_attempts=5,
            error_history=[],
            error_categories=[],
            time_spent=0,
            code_changes_size=[],
            test_progress=[],
            complexity_level="medium"
        )
        
        decision = orchestrator.decide_retry(context)
        assert decision.should_retry is False
        assert decision.strategy == RetryStrategy.SKIP_AND_CONTINUE
        assert "Maximum retry attempts reached" in decision.reason
    
    def test_decide_retry_selects_best_strategy(self, orchestrator):
        """Test selection of best strategy"""
        # Context favoring adaptive strategy
        context = RetryContext(
            feature_id="f1",
            attempt_number=3,
            total_attempts=5,
            error_history=[],
            error_categories=["syntax", "import", "syntax"],
            time_spent=0,
            code_changes_size=[],
            test_progress=[],
            complexity_level="medium"
        )
        
        decision = orchestrator.decide_retry(context)
        assert decision.should_retry is True
        assert decision.strategy in [RetryStrategy.ADAPTIVE, RetryStrategy.ALTERNATIVE_APPROACH]
        assert decision.delay_seconds > 0
        assert decision.reason != ""
    
    def test_decide_retry_complex_feature(self, orchestrator):
        """Test retry decision for complex features"""
        context = RetryContext(
            feature_id="f1",
            attempt_number=3,
            total_attempts=5,
            error_history=[],
            error_categories=["test"],
            time_spent=0,
            code_changes_size=[],
            test_progress=[],
            complexity_level="high"
        )
        
        decision = orchestrator.decide_retry(context)
        assert decision.should_retry is True
        # Decomposition should be preferred for complex features
        assert decision.strategy in [RetryStrategy.DECOMPOSITION, RetryStrategy.ADAPTIVE]
    
    def test_record_outcome(self, orchestrator):
        """Test recording strategy outcomes"""
        # Record some outcomes
        orchestrator.record_outcome(RetryStrategy.ADAPTIVE, True)
        orchestrator.record_outcome(RetryStrategy.ADAPTIVE, True)
        orchestrator.record_outcome(RetryStrategy.ADAPTIVE, False)
        
        # Check success rate calculation
        # Should be: 0.7 * 0.5 + 0.3 * 1.0 = 0.65 (first)
        # Then: 0.7 * 0.65 + 0.3 * 1.0 = 0.755 (second)
        # Then: 0.7 * 0.755 + 0.3 * 0.0 = 0.5285 (third)
        assert orchestrator.strategy_success_rate[RetryStrategy.ADAPTIVE] > 0.5
        assert orchestrator.strategy_success_rate[RetryStrategy.ADAPTIVE] < 0.6
    
    def test_get_strategy_report(self, orchestrator):
        """Test getting strategy report"""
        # Use some strategies
        context = RetryContext(
            feature_id="f1",
            attempt_number=1,
            total_attempts=5,
            error_history=[],
            error_categories=[],
            time_spent=0,
            code_changes_size=[],
            test_progress=[],
            complexity_level="medium"
        )
        
        orchestrator.decide_retry(context)
        orchestrator.record_outcome(RetryStrategy.ADAPTIVE, True)
        
        report = orchestrator.get_strategy_report()
        
        assert isinstance(report, dict)
        assert RetryStrategy.ADAPTIVE.value in report
        
        adaptive_report = report[RetryStrategy.ADAPTIVE.value]
        assert "usage_count" in adaptive_report
        assert "success_rate" in adaptive_report
        assert "effectiveness" in adaptive_report
    
    def test_strategy_selection_with_history(self, orchestrator):
        """Test strategy selection influenced by success history"""
        # Set up success history
        orchestrator.strategy_success_rate[RetryStrategy.EXPONENTIAL_BACKOFF] = 0.2
        orchestrator.strategy_success_rate[RetryStrategy.ADAPTIVE] = 0.8
        
        context = RetryContext(
            feature_id="f1",
            attempt_number=2,
            total_attempts=5,
            error_history=[],
            error_categories=["syntax"],
            time_spent=0,
            code_changes_size=[],
            test_progress=[],
            complexity_level="medium"
        )
        
        # Should prefer adaptive due to higher success rate
        decision = orchestrator.decide_retry(context)
        assert decision.strategy == RetryStrategy.ADAPTIVE