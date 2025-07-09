"""
Tests for GREEN Phase Implementation
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock

from workflows.mvp_incremental.green_phase import (
    GreenPhaseOrchestrator,
    GreenPhaseMetrics,
    GreenPhaseContext,
    GreenPhaseError
)
from workflows.mvp_incremental.tdd_phase_tracker import TDDPhase, TDDPhaseTracker
from workflows.mvp_incremental.testable_feature_parser import TestableFeature


@pytest.fixture
def mock_phase_tracker():
    """Create a mock phase tracker with required methods"""
    tracker = Mock(spec=TDDPhaseTracker)
    # Add required methods that are used in the implementation
    tracker.get_current_phase = Mock()
    tracker.transition_to_phase = Mock()
    tracker.get_phase_history = Mock(return_value=[(TDDPhase.RED, datetime.now())])
    return tracker


@pytest.fixture
def sample_feature():
    """Create a sample testable feature"""
    return TestableFeature(
        id="feat-001",
        title="User Authentication",
        description="Implement user login functionality",
        test_criteria=[
            "Test user can login with valid credentials",
            "Test user cannot login with invalid credentials"
        ]
    )


@pytest.fixture
def sample_metrics():
    """Create sample metrics for testing"""
    now = datetime.now()
    return GreenPhaseMetrics(
        feature_id="feat-001",
        feature_title="User Authentication",
        red_phase_start=now - timedelta(minutes=30),
        yellow_phase_start=now - timedelta(minutes=20),
        green_phase_start=now - timedelta(minutes=5),
        implementation_attempts=2,
        review_attempts=1,
        test_execution_count=5
    )


@pytest.fixture
def orchestrator(mock_phase_tracker):
    """Create a GreenPhaseOrchestrator instance"""
    return GreenPhaseOrchestrator(mock_phase_tracker)


class TestGreenPhaseValidation:
    """Test GREEN phase entry validation"""
    
    def test_validate_entry_from_yellow_phase(self, orchestrator, sample_feature, mock_phase_tracker):
        """Test successful validation when in YELLOW phase"""
        mock_phase_tracker.get_current_phase.return_value = TDDPhase.YELLOW
        
        # Should not raise
        orchestrator.validate_green_phase_entry(sample_feature)
        mock_phase_tracker.get_current_phase.assert_called_once_with("feat-001")
        
    def test_validate_entry_from_red_phase_fails(self, orchestrator, sample_feature, mock_phase_tracker):
        """Test validation fails when in RED phase"""
        mock_phase_tracker.get_current_phase.return_value = TDDPhase.RED
        
        with pytest.raises(GreenPhaseError) as exc_info:
            orchestrator.validate_green_phase_entry(sample_feature)
            
        assert "Cannot enter GREEN phase from RED" in str(exc_info.value)
        
    def test_validate_entry_from_green_phase_fails(self, orchestrator, sample_feature, mock_phase_tracker):
        """Test validation fails when already in GREEN phase"""
        mock_phase_tracker.get_current_phase.return_value = TDDPhase.GREEN
        
        with pytest.raises(GreenPhaseError) as exc_info:
            orchestrator.validate_green_phase_entry(sample_feature)
            
        assert "Cannot enter GREEN phase from GREEN" in str(exc_info.value)


class TestGreenPhaseEntry:
    """Test entering GREEN phase"""
    
    def test_successful_green_phase_entry(self, orchestrator, sample_feature, sample_metrics, mock_phase_tracker):
        """Test successful entry into GREEN phase"""
        mock_phase_tracker.get_current_phase.return_value = TDDPhase.YELLOW
        
        context = orchestrator.enter_green_phase(
            feature=sample_feature,
            metrics=sample_metrics,
            review_approved=True,
            review_feedback="LGTM! Well-structured code."
        )
        
        # Verify context
        assert context.feature == sample_feature
        assert context.metrics == sample_metrics
        assert context.review_feedback == "LGTM! Well-structured code."
        assert context.metrics.code_reviewed is True
        assert context.metrics.code_approved is True
        assert context.metrics.all_tests_passed is True
        assert context.metrics.green_phase_start is not None
        
        # Verify phase transition
        mock_phase_tracker.transition_to_phase.assert_called_once_with("feat-001", TDDPhase.GREEN)
        
    def test_green_phase_entry_without_approval_fails(self, orchestrator, sample_feature, sample_metrics, mock_phase_tracker):
        """Test entry fails without review approval"""
        mock_phase_tracker.get_current_phase.return_value = TDDPhase.YELLOW
        
        with pytest.raises(GreenPhaseError) as exc_info:
            orchestrator.enter_green_phase(
                feature=sample_feature,
                metrics=sample_metrics,
                review_approved=False
            )
            
        assert "Cannot enter GREEN phase without review approval" in str(exc_info.value)
        
    def test_green_phase_entry_from_wrong_phase(self, orchestrator, sample_feature, sample_metrics, mock_phase_tracker):
        """Test entry fails from wrong phase"""
        mock_phase_tracker.get_current_phase.return_value = TDDPhase.RED
        
        with pytest.raises(GreenPhaseError) as exc_info:
            orchestrator.enter_green_phase(
                feature=sample_feature,
                metrics=sample_metrics,
                review_approved=True
            )
            
        assert "Cannot enter GREEN phase from RED" in str(exc_info.value)


class TestFeatureCompletion:
    """Test feature completion in GREEN phase"""
    
    def test_successful_feature_completion(self, orchestrator, sample_feature, sample_metrics, mock_phase_tracker):
        """Test successful feature completion"""
        # Setup
        mock_phase_tracker.get_current_phase.return_value = TDDPhase.GREEN
        # Set metrics to approved state
        sample_metrics.code_approved = True
        sample_metrics.code_reviewed = True
        context = GreenPhaseContext(
            feature=sample_feature,
            metrics=sample_metrics,
            review_feedback="Great implementation!"
        )
        
        # Complete feature
        summary = orchestrator.complete_feature(
            context,
            completion_notes=["All tests passing", "Code reviewed and approved"]
        )
        
        # Verify metrics updated
        assert context.metrics.green_phase_end is not None
        assert context.metrics.total_cycle_time is not None
        assert context.metrics.red_phase_duration is not None
        assert context.metrics.yellow_phase_duration is not None
        
        # Verify summary
        assert summary["status"] == "completed"
        assert summary["feature"]["feature_id"] == "feat-001"
        assert summary["success_indicators"]["tdd_cycle_complete"] is True
        assert summary["success_indicators"]["code_approved"] is True
        assert "celebration_message" in summary
        
        # Verify completion notes
        assert "All tests passing" in context.completion_notes
        assert "Code reviewed and approved" in context.completion_notes
        
        # Verify feature added to completed list
        assert len(orchestrator.completed_features) == 1
        assert orchestrator.completed_features[0] == context
        
    def test_completion_from_wrong_phase_fails(self, orchestrator, sample_feature, sample_metrics, mock_phase_tracker):
        """Test completion fails when not in GREEN phase"""
        mock_phase_tracker.get_current_phase.return_value = TDDPhase.YELLOW
        context = GreenPhaseContext(feature=sample_feature, metrics=sample_metrics)
        
        with pytest.raises(GreenPhaseError) as exc_info:
            orchestrator.complete_feature(context)
            
        assert "Cannot complete feature - not in GREEN phase" in str(exc_info.value)


class TestMetricsCalculation:
    """Test metrics calculation"""
    
    def test_duration_calculations(self):
        """Test phase duration calculations"""
        now = datetime.now()
        metrics = GreenPhaseMetrics(
            feature_id="test-001",
            feature_title="Test Feature",
            red_phase_start=now - timedelta(minutes=30),
            yellow_phase_start=now - timedelta(minutes=20),
            green_phase_start=now - timedelta(minutes=5),
            green_phase_end=now
        )
        
        metrics.calculate_durations()
        
        # Check durations (approximately)
        assert 590 < metrics.red_phase_duration < 610  # ~10 minutes
        assert 890 < metrics.yellow_phase_duration < 910  # ~15 minutes
        assert 1790 < metrics.total_cycle_time < 1810  # ~30 minutes


class TestCompletionReport:
    """Test completion report generation"""
    
    def test_empty_completion_report(self, orchestrator):
        """Test report when no features completed"""
        report = orchestrator.get_completion_report()
        
        assert report["total_features"] == 0
        assert report["message"] == "No features completed yet"
        
    def test_completion_report_with_features(self, orchestrator, sample_feature, mock_phase_tracker):
        """Test report with completed features"""
        # Setup completed features
        now = datetime.now()
        
        # Feature 1
        metrics1 = GreenPhaseMetrics(
            feature_id="feat-001",
            feature_title="Feature 1",
            red_phase_start=now - timedelta(minutes=30),
            yellow_phase_start=now - timedelta(minutes=20),
            green_phase_start=now - timedelta(minutes=5),
            green_phase_end=now,
            implementation_attempts=2,
            review_attempts=1
        )
        metrics1.calculate_durations()
        
        context1 = GreenPhaseContext(
            feature=sample_feature,
            metrics=metrics1
        )
        orchestrator.completed_features.append(context1)
        
        # Feature 2 (faster)
        feature2 = TestableFeature(
            id="feat-002",
            title="Feature 2",
            description="Another feature",
            test_criteria=["Test 1"]
        )
        
        metrics2 = GreenPhaseMetrics(
            feature_id="feat-002",
            feature_title="Feature 2",
            red_phase_start=now - timedelta(minutes=10),
            yellow_phase_start=now - timedelta(minutes=7),
            green_phase_start=now - timedelta(minutes=2),
            green_phase_end=now,
            implementation_attempts=5,  # More attempts
            review_attempts=2
        )
        metrics2.calculate_durations()
        
        context2 = GreenPhaseContext(
            feature=feature2,
            metrics=metrics2
        )
        orchestrator.completed_features.append(context2)
        
        # Get report
        report = orchestrator.get_completion_report()
        
        # Verify report
        assert report["total_features"] == 2
        assert report["total_cycle_time_seconds"] > 0
        assert report["average_cycle_time_seconds"] > 0
        assert len(report["features"]) == 2
        assert report["summary"]["fastest_feature"] == "Feature 2"
        assert report["summary"]["most_attempts"] == "Feature 2"


class TestCelebrationMessages:
    """Test celebration message generation"""
    
    def test_fast_completion_message(self, orchestrator):
        """Test message for fast completion"""
        metrics = GreenPhaseMetrics(
            feature_id="test",
            feature_title="Test",
            red_phase_start=datetime.now() - timedelta(minutes=4),
            yellow_phase_start=datetime.now() - timedelta(minutes=3),
            green_phase_start=datetime.now() - timedelta(minutes=1),
            green_phase_end=datetime.now(),
            implementation_attempts=1
        )
        metrics.calculate_durations()
        
        context = GreenPhaseContext(
            feature=TestableFeature(id="test", title="Test", description="", test_criteria=[]),
            metrics=metrics
        )
        
        message = orchestrator._get_celebration_message(context)
        assert "First try success!" in message
        assert "Lightning fast!" in message
        
    def test_moderate_completion_message(self, orchestrator):
        """Test message for moderate completion time"""
        metrics = GreenPhaseMetrics(
            feature_id="test",
            feature_title="Test",
            red_phase_start=datetime.now() - timedelta(minutes=12),
            yellow_phase_start=datetime.now() - timedelta(minutes=8),
            green_phase_start=datetime.now() - timedelta(minutes=2),
            green_phase_end=datetime.now(),
            implementation_attempts=3
        )
        metrics.calculate_durations()
        
        context = GreenPhaseContext(
            feature=TestableFeature(id="test", title="Test", description="", test_criteria=[]),
            metrics=metrics
        )
        
        message = orchestrator._get_celebration_message(context)
        assert "Good iteration!" in message
        assert "Great pace!" in message
        
    def test_persistent_completion_message(self, orchestrator):
        """Test message for many attempts"""
        metrics = GreenPhaseMetrics(
            feature_id="test",
            feature_title="Test",
            red_phase_start=datetime.now() - timedelta(minutes=20),
            yellow_phase_start=datetime.now() - timedelta(minutes=15),
            green_phase_start=datetime.now() - timedelta(minutes=5),
            green_phase_end=datetime.now(),
            implementation_attempts=5
        )
        metrics.calculate_durations()
        
        context = GreenPhaseContext(
            feature=TestableFeature(id="test", title="Test", description="", test_criteria=[]),
            metrics=metrics
        )
        
        message = orchestrator._get_celebration_message(context)
        assert "Persistence pays off!" in message


class TestGreenPhaseContext:
    """Test GreenPhaseContext dataclass"""
    
    def test_context_to_dict(self, sample_feature):
        """Test context serialization to dict"""
        metrics = GreenPhaseMetrics(
            feature_id="feat-001",
            feature_title="Test Feature",
            red_phase_start=datetime.now() - timedelta(minutes=30),
            yellow_phase_start=datetime.now() - timedelta(minutes=20),
            green_phase_start=datetime.now() - timedelta(minutes=5),
            green_phase_end=datetime.now(),
            implementation_attempts=2,
            review_attempts=1,
            test_execution_count=5
        )
        metrics.calculate_durations()
        
        context = GreenPhaseContext(
            feature=sample_feature,
            metrics=metrics,
            review_feedback="Approved",
            completion_notes=["Note 1", "Note 2"]
        )
        
        result = context.to_dict()
        
        assert result["feature_id"] == "feat-001"
        assert result["feature_title"] == "User Authentication"
        assert result["metrics"]["implementation_attempts"] == 2
        assert result["metrics"]["review_attempts"] == 1
        assert result["review_feedback"] == "Approved"
        assert result["completion_notes"] == ["Note 1", "Note 2"]
        assert result["completed_at"] is not None


class TestResetFunctionality:
    """Test reset functionality"""
    
    def test_reset_metrics(self, orchestrator, sample_feature):
        """Test resetting completed features"""
        # Add some completed features
        context = GreenPhaseContext(
            feature=sample_feature,
            metrics=GreenPhaseMetrics(
                feature_id="test",
                feature_title="Test",
                red_phase_start=datetime.now(),
                yellow_phase_start=datetime.now(),
                green_phase_start=datetime.now()
            )
        )
        orchestrator.completed_features.append(context)
        
        assert len(orchestrator.completed_features) == 1
        
        # Reset
        orchestrator.reset_metrics()
        
        assert len(orchestrator.completed_features) == 0