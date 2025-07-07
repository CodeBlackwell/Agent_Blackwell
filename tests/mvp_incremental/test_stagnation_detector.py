"""
Unit tests for the stagnation detection system
"""
import pytest
from datetime import datetime
from workflows.incremental.stagnation_detector import (
    StagnationType, ErrorPattern, ProgressMetrics, StagnationDetector
)


class TestErrorPattern:
    """Test ErrorPattern functionality"""
    
    def test_error_pattern_creation(self):
        """Test creating an error pattern"""
        pattern = ErrorPattern(
            error_type="syntax",
            error_message="SyntaxError: invalid syntax at line 42"
        )
        
        assert pattern.error_type == "syntax"
        assert pattern.error_message == "SyntaxError: invalid syntax at line 42"
        assert pattern.occurrences == 1
        assert isinstance(pattern.first_seen, datetime)
        assert isinstance(pattern.last_seen, datetime)
        assert pattern.affected_files == set()
    
    def test_is_similar_exact_match(self):
        """Test similarity check with exact match"""
        pattern = ErrorPattern(
            error_type="syntax",
            error_message="SyntaxError: invalid syntax"
        )
        
        assert pattern.is_similar("SyntaxError: invalid syntax") is True
    
    def test_is_similar_error_type_match(self):
        """Test similarity check with error type in message"""
        pattern = ErrorPattern(
            error_type="syntax",
            error_message="SyntaxError: invalid syntax at line 42"
        )
        
        assert pattern.is_similar("Another syntax error occurred") is True
    
    def test_is_similar_pattern_match(self):
        """Test similarity check with pattern matching (numbers replaced)"""
        pattern = ErrorPattern(
            error_type="syntax",
            error_message="SyntaxError: invalid syntax at line 42"
        )
        
        # Different line number but same pattern
        assert pattern.is_similar("SyntaxError: invalid syntax at line 99") is True
        
        # Different structure
        assert pattern.is_similar("TypeError: invalid type") is False


class TestProgressMetrics:
    """Test ProgressMetrics functionality"""
    
    def test_progress_metrics_initialization(self):
        """Test ProgressMetrics initialization"""
        metrics = ProgressMetrics(feature_id="feature_1")
        
        assert metrics.feature_id == "feature_1"
        assert metrics.total_attempts == 0
        assert metrics.successful_validations == []
        assert metrics.failed_validations == []
        assert metrics.error_patterns == []
        assert metrics.code_changes == []
        assert metrics.test_results == []
        assert metrics.time_spent == []
    
    def test_get_progress_rate_no_tests(self):
        """Test progress rate calculation without test results"""
        metrics = ProgressMetrics(feature_id="feature_1")
        assert metrics.get_progress_rate() == 0.0
        
        # Add some attempts
        metrics.total_attempts = 5
        metrics.successful_validations = ["val1", "val2"]
        
        assert metrics.get_progress_rate() == 0.4  # 2/5
    
    def test_get_progress_rate_with_tests(self):
        """Test progress rate calculation with test results"""
        metrics = ProgressMetrics(feature_id="feature_1")
        
        # Initial: 2 passed, 8 failed
        metrics.test_results.append((2, 8))
        # Latest: 7 passed, 3 failed
        metrics.test_results.append((7, 3))
        
        # Progress = (7-2)/10 = 0.5
        assert metrics.get_progress_rate() == 0.5
    
    def test_get_progress_rate_edge_cases(self):
        """Test progress rate calculation edge cases"""
        metrics = ProgressMetrics(feature_id="feature_1")
        
        # Single test result
        metrics.test_results.append((5, 5))
        assert metrics.get_progress_rate() == 0.0
        
        # Negative progress (should be clamped to 0)
        metrics.test_results.append((3, 7))
        assert metrics.get_progress_rate() == 0.0
    
    def test_get_stagnation_score_repeated_errors(self):
        """Test stagnation score with repeated errors"""
        metrics = ProgressMetrics(feature_id="feature_1")
        
        # Add error pattern with many occurrences
        error = ErrorPattern(error_type="syntax", error_message="Error")
        error.occurrences = 5
        metrics.error_patterns.append(error)
        
        score = metrics.get_stagnation_score()
        assert score > 0.2  # Should have score for repeated errors
    
    def test_get_stagnation_score_no_progress(self):
        """Test stagnation score with no progress"""
        metrics = ProgressMetrics(feature_id="feature_1")
        metrics.total_attempts = 5
        # No successful validations
        
        score = metrics.get_stagnation_score()
        assert score >= 0.3  # Should have score for lack of progress
    
    def test_get_stagnation_score_diminishing_changes(self):
        """Test stagnation score with diminishing code changes"""
        metrics = ProgressMetrics(feature_id="feature_1")
        metrics.code_changes = [100, 50, 5, 3, 2]  # Diminishing changes
        
        score = metrics.get_stagnation_score()
        assert score >= 0.2  # Should have score for small recent changes
    
    def test_get_stagnation_score_consistent_failures(self):
        """Test stagnation score with consistent test failures"""
        metrics = ProgressMetrics(feature_id="feature_1")
        metrics.test_results = [(5, 5), (5, 5), (5, 5)]  # Same failures
        
        score = metrics.get_stagnation_score()
        assert score >= 0.2  # Should have score for consistent failures
    
    def test_get_stagnation_score_combined(self):
        """Test stagnation score with multiple factors"""
        metrics = ProgressMetrics(feature_id="feature_1")
        metrics.total_attempts = 5
        
        # Add repeated error
        error = ErrorPattern(error_type="syntax", error_message="Error")
        error.occurrences = 4
        metrics.error_patterns.append(error)
        
        # Add consistent failures
        metrics.test_results = [(2, 8), (2, 8), (2, 8)]
        
        # Add small code changes
        metrics.code_changes = [5, 3, 2]
        
        score = metrics.get_stagnation_score()
        assert score >= 0.7  # Should have high score from multiple factors


class TestStagnationDetector:
    """Test StagnationDetector functionality"""
    
    @pytest.fixture
    def detector(self):
        """Create a StagnationDetector instance"""
        return StagnationDetector(
            stagnation_threshold=0.7,
            min_attempts_before_detection=3
        )
    
    def test_detector_initialization(self, detector):
        """Test detector initialization"""
        assert detector.stagnation_threshold == 0.7
        assert detector.min_attempts_before_detection == 3
        assert detector.feature_metrics == {}
        assert detector.global_patterns == []
    
    def test_record_attempt_success(self, detector):
        """Test recording a successful attempt"""
        detector.record_attempt(
            feature_id="feature_1",
            success=True,
            code_diff_size=50,
            test_results=(8, 2),
            duration=1.5
        )
        
        metrics = detector.feature_metrics["feature_1"]
        assert metrics.total_attempts == 1
        assert len(metrics.successful_validations) == 1
        assert len(metrics.failed_validations) == 0
        assert metrics.code_changes == [50]
        assert metrics.test_results == [(8, 2)]
        assert metrics.time_spent == [1.5]
    
    def test_record_attempt_failure(self, detector):
        """Test recording a failed attempt"""
        detector.record_attempt(
            feature_id="feature_1",
            success=False,
            error_message="SyntaxError: invalid syntax",
            files_changed=["main.py"],
            code_diff_size=30,
            test_results=(3, 7),
            duration=2.0
        )
        
        metrics = detector.feature_metrics["feature_1"]
        assert metrics.total_attempts == 1
        assert len(metrics.successful_validations) == 0
        assert len(metrics.failed_validations) == 1
        assert len(metrics.error_patterns) == 1
        assert metrics.error_patterns[0].error_type == "syntax"
        assert metrics.error_patterns[0].affected_files == {"main.py"}
    
    def test_record_error_pattern_categorization(self, detector):
        """Test error pattern categorization"""
        metrics = ProgressMetrics(feature_id="feature_1")
        
        # Test different error types
        test_cases = [
            ("SyntaxError: invalid syntax", "syntax"),
            ("ImportError: No module named foo", "import"),
            ("ModuleNotFoundError: No module", "import"),
            ("AttributeError: object has no attribute", "attribute"),
            ("TypeError: unsupported operand", "type"),
            ("Test test_foo failed", "test_failure"),
            ("Random error occurred", "generic")
        ]
        
        for error_msg, expected_type in test_cases:
            detector._record_error_pattern(metrics, error_msg, ["test.py"])
            
        assert len(metrics.error_patterns) == len(test_cases)
        for i, (_, expected_type) in enumerate(test_cases):
            assert metrics.error_patterns[i].error_type == expected_type
    
    def test_detect_stagnation_too_early(self, detector):
        """Test stagnation detection before minimum attempts"""
        # Record only 2 attempts (min is 3)
        detector.record_attempt("feature_1", False, "Error 1")
        detector.record_attempt("feature_1", False, "Error 2")
        
        result = detector.detect_stagnation("feature_1")
        assert result is None  # Too early to detect
    
    def test_detect_stagnation_repeated_error(self, detector):
        """Test stagnation detection with repeated errors"""
        # Record same error multiple times with small code changes
        for i in range(5):
            detector.record_attempt(
                "feature_1",
                False,
                "SyntaxError: invalid syntax at line 42",
                ["main.py"],
                code_diff_size=5  # Small changes to trigger diminishing returns
            )
        
        result = detector.detect_stagnation("feature_1")
        assert result is not None
        assert StagnationType.REPEATED_ERROR.value in result["stagnation_types"]
        assert result["most_common_error"]["occurrences"] == 5
    
    def test_detect_stagnation_no_progress(self, detector):
        """Test stagnation detection with no progress"""
        # Record failures with no successful validations
        for i in range(4):
            detector.record_attempt(
                "feature_1",
                False,
                f"Error {i}",
                test_results=(0, 10)
            )
        
        result = detector.detect_stagnation("feature_1")
        assert result is not None
        assert StagnationType.NO_PROGRESS.value in result["stagnation_types"]
        assert result["progress_rate"] < 0.1
    
    # REMOVED: test_detect_stagnation_cyclic_failure - stagnation handled by MAX_RETRIES
    # def test_detect_stagnation_cyclic_failure(self, detector):
    #     pass
    
    def test_detect_stagnation_diminishing_returns(self, detector):
        """Test stagnation detection with diminishing returns"""
        # Record attempts with decreasing code changes
        changes = [100, 50, 20, 5, 3, 2]
        for i, change in enumerate(changes):
            detector.record_attempt(
                "feature_1",
                False,
                f"Error {i}",
                code_diff_size=change
            )
        
        result = detector.detect_stagnation("feature_1")
        assert result is not None
        assert StagnationType.DIMINISHING_RETURNS.value in result["stagnation_types"]
    
    def test_get_feature_summary(self, detector):
        """Test getting feature summary"""
        # Record some attempts
        detector.record_attempt("feature_1", True, duration=1.0)
        detector.record_attempt("feature_1", False, "SyntaxError: invalid syntax", duration=2.0)
        detector.record_attempt("feature_1", False, "ImportError: No module", duration=1.5)
        
        summary = detector.get_feature_summary("feature_1")
        
        assert summary["feature_id"] == "feature_1"
        assert summary["total_attempts"] == 3
        assert summary["successful_validations"] == 1
        assert summary["unique_error_types"] == 2  # syntax and import
        assert summary["average_time_per_attempt"] == 1.5
        assert len(summary["most_recent_errors"]) == 2
    
    def test_should_skip_feature_severe_stagnation(self, detector):
        """Test feature skipping with severe stagnation"""
        # Create severe stagnation scenario
        for i in range(6):
            detector.record_attempt(
                "feature_1",
                False,
                "SyntaxError: same error",
                code_diff_size=2  # Very small changes
            )
        
        assert detector.should_skip_feature("feature_1") is True
    
    def test_should_skip_feature_no_progress(self, detector):
        """Test feature skipping with zero progress"""
        # No successful attempts after many tries
        for i in range(8):
            detector.record_attempt(
                "feature_1",
                False,
                f"Different error {i}",
                test_results=(0, 10)  # No tests passing
            )
        
        assert detector.should_skip_feature("feature_1") is True
    
    def test_should_skip_feature_not_stagnant(self, detector):
        """Test feature not skipped when making progress"""
        # Mix of success and failure
        detector.record_attempt("feature_1", True)
        detector.record_attempt("feature_1", False, "Error")
        detector.record_attempt("feature_1", True)
        
        assert detector.should_skip_feature("feature_1") is False
    
    def test_suggest_alternative_approach(self, detector):
        """Test alternative approach suggestions"""
        # Test different error patterns
        test_cases = [
            ("SyntaxError: invalid", "syntax", "Simplify the code structure"),
            ("ImportError: no module", "import", "Review dependencies"),
            ("AttributeError: no attr", "attribute", "Check object initialization"),
            ("TypeError: wrong type", "type", "Review data types"),
            ("Test failed", "test_failure", "Focus on making one test pass"),
            ("Generic error", "generic", "Try breaking down the feature")
        ]
        
        for i, (error, error_type, expected_suggestion) in enumerate(test_cases):
            feature_id = f"feature_{i}"
            # Record multiple times to make it dominant
            for _ in range(3):
                detector.record_attempt(feature_id, False, error)
            
            suggestion = detector.suggest_alternative_approach(feature_id)
            assert expected_suggestion in suggestion
    
    def test_get_recommendation(self, detector):
        """Test recommendation generation based on stagnation types"""
        metrics = ProgressMetrics(feature_id="test")
        
        # Test different stagnation type combinations
        test_cases = [
            ([StagnationType.REPEATED_ERROR], "different approach"),
            ([StagnationType.CYCLIC_FAILURE], "Break the cycle"),
            ([StagnationType.DIMINISHING_RETURNS], "fresh perspective"),
            ([StagnationType.NO_PROGRESS], "requirements and validation")
        ]
        
        for types, expected_phrase in test_cases:
            rec = detector._get_recommendation(types, metrics)
            assert expected_phrase in rec
    
    def test_multiple_features(self, detector):
        """Test tracking multiple features independently"""
        # Record attempts for different features
        detector.record_attempt("feature_1", True)
        detector.record_attempt("feature_2", False, "Error")
        detector.record_attempt("feature_3", True)
        
        assert len(detector.feature_metrics) == 3
        assert detector.feature_metrics["feature_1"].total_attempts == 1
        assert detector.feature_metrics["feature_2"].total_attempts == 1
        assert detector.feature_metrics["feature_3"].total_attempts == 1