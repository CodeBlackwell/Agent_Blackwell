"""
Comprehensive tests for TDD Phase Tracker

Tests all aspects of the RED-YELLOW-GREEN phase tracking system
including transitions, validation, history, and visual output.
"""

import pytest
from datetime import datetime, timedelta
import time
from workflows.mvp_incremental.tdd_phase_tracker import (
    TDDPhase, TDDPhaseTracker, PhaseTransition, InvalidPhaseTransition
)


class TestTDDPhaseEnum:
    """Test the TDDPhase enum functionality"""
    
    def test_phase_values(self):
        """Test that phases have correct values"""
        assert TDDPhase.RED.value == "RED"
        assert TDDPhase.YELLOW.value == "YELLOW"
        assert TDDPhase.GREEN.value == "GREEN"
    
    def test_phase_emojis(self):
        """Test visual indicators"""
        assert TDDPhase.RED.get_emoji() == "🔴"
        assert TDDPhase.YELLOW.get_emoji() == "🟡"
        assert TDDPhase.GREEN.get_emoji() == "🟢"
    
    def test_phase_descriptions(self):
        """Test phase descriptions"""
        assert "failing" in TDDPhase.RED.get_description()
        assert "awaiting review" in TDDPhase.YELLOW.get_description()
        assert "approved" in TDDPhase.GREEN.get_description()


class TestPhaseTransition:
    """Test the PhaseTransition data class"""
    
    def test_transition_creation(self):
        """Test creating a phase transition"""
        transition = PhaseTransition(
            from_phase=TDDPhase.RED,
            to_phase=TDDPhase.YELLOW,
            reason="Tests now passing"
        )
        
        assert transition.from_phase == TDDPhase.RED
        assert transition.to_phase == TDDPhase.YELLOW
        assert transition.reason == "Tests now passing"
        assert isinstance(transition.timestamp, datetime)
    
    def test_transition_with_metadata(self):
        """Test transition with metadata"""
        metadata = {"test_count": 5, "passed": 5}
        transition = PhaseTransition(
            from_phase=None,
            to_phase=TDDPhase.RED,
            metadata=metadata
        )
        
        assert transition.metadata == metadata


class TestTDDPhaseTracker:
    """Test the main TDDPhaseTracker class"""
    
    @pytest.fixture
    def tracker(self):
        """Create a fresh tracker instance"""
        return TDDPhaseTracker()
    
    def test_initialization(self, tracker):
        """Test tracker initialization"""
        assert len(tracker.get_all_features()) == 0
        assert tracker.get_summary_report() == "No features being tracked"
    
    def test_start_feature(self, tracker):
        """Test starting a new feature"""
        tracker.start_feature("feature_1", {"name": "Test Feature"})
        
        assert tracker.get_current_phase("feature_1") == TDDPhase.RED
        assert len(tracker.get_phase_history("feature_1")) == 1
        
        # Verify initial transition
        history = tracker.get_phase_history("feature_1")
        assert history[0].from_phase is None
        assert history[0].to_phase == TDDPhase.RED
    
    def test_cannot_start_duplicate_feature(self, tracker):
        """Test that duplicate features cannot be started"""
        tracker.start_feature("feature_1")
        
        with pytest.raises(ValueError, match="already being tracked"):
            tracker.start_feature("feature_1")
    
    def test_valid_transitions(self, tracker):
        """Test all valid phase transitions"""
        tracker.start_feature("feature_1")
        
        # RED → YELLOW
        tracker.transition_to("feature_1", TDDPhase.YELLOW, "Tests passing")
        assert tracker.get_current_phase("feature_1") == TDDPhase.YELLOW
        
        # YELLOW → GREEN
        tracker.transition_to("feature_1", TDDPhase.GREEN, "Code reviewed")
        assert tracker.get_current_phase("feature_1") == TDDPhase.GREEN
    
    def test_yellow_to_red_transition(self, tracker):
        """Test that YELLOW can go back to RED (review rejection)"""
        tracker.start_feature("feature_1")
        tracker.transition_to("feature_1", TDDPhase.YELLOW)
        
        # Review rejection sends back to RED
        tracker.transition_to("feature_1", TDDPhase.RED, "Review rejected")
        assert tracker.get_current_phase("feature_1") == TDDPhase.RED
    
    def test_invalid_transitions(self, tracker):
        """Test that invalid transitions are prevented"""
        tracker.start_feature("feature_1")
        
        # Cannot go directly from RED to GREEN
        with pytest.raises(InvalidPhaseTransition, match="Cannot transition from RED to GREEN"):
            tracker.transition_to("feature_1", TDDPhase.GREEN)
        
        # Cannot go from GREEN to any phase
        tracker.transition_to("feature_1", TDDPhase.YELLOW)
        tracker.transition_to("feature_1", TDDPhase.GREEN)
        
        with pytest.raises(InvalidPhaseTransition):
            tracker.transition_to("feature_1", TDDPhase.YELLOW)
    
    def test_transition_validation(self, tracker):
        """Test the validate_transition method"""
        # Valid transitions
        assert tracker.validate_transition(None, TDDPhase.RED) is True
        assert tracker.validate_transition(TDDPhase.RED, TDDPhase.YELLOW) is True
        assert tracker.validate_transition(TDDPhase.YELLOW, TDDPhase.GREEN) is True
        assert tracker.validate_transition(TDDPhase.YELLOW, TDDPhase.RED) is True
        
        # Invalid transitions
        assert tracker.validate_transition(None, TDDPhase.YELLOW) is False
        assert tracker.validate_transition(None, TDDPhase.GREEN) is False
        assert tracker.validate_transition(TDDPhase.RED, TDDPhase.GREEN) is False
        assert tracker.validate_transition(TDDPhase.GREEN, TDDPhase.RED) is False
    
    def test_untracked_feature_operations(self, tracker):
        """Test operations on untracked features"""
        assert tracker.get_current_phase("unknown") is None
        assert tracker.get_phase_history("unknown") == []
        
        with pytest.raises(ValueError, match="not being tracked"):
            tracker.transition_to("unknown", TDDPhase.YELLOW)
    
    def test_phase_history_tracking(self, tracker):
        """Test that phase history is accurately tracked"""
        tracker.start_feature("feature_1")
        
        # Make several transitions
        tracker.transition_to("feature_1", TDDPhase.YELLOW, "Tests pass")
        tracker.transition_to("feature_1", TDDPhase.RED, "Review failed")
        tracker.transition_to("feature_1", TDDPhase.YELLOW, "Fixed issues")
        tracker.transition_to("feature_1", TDDPhase.GREEN, "Approved")
        
        history = tracker.get_phase_history("feature_1")
        assert len(history) == 5  # Initial + 4 transitions
        
        # Verify transition sequence
        assert history[0].to_phase == TDDPhase.RED
        assert history[1].to_phase == TDDPhase.YELLOW
        assert history[2].to_phase == TDDPhase.RED
        assert history[3].to_phase == TDDPhase.YELLOW
        assert history[4].to_phase == TDDPhase.GREEN
    
    def test_is_feature_complete(self, tracker):
        """Test feature completion detection"""
        tracker.start_feature("feature_1")
        assert not tracker.is_feature_complete("feature_1")
        
        tracker.transition_to("feature_1", TDDPhase.YELLOW)
        assert not tracker.is_feature_complete("feature_1")
        
        tracker.transition_to("feature_1", TDDPhase.GREEN)
        assert tracker.is_feature_complete("feature_1")
    
    def test_get_features_in_phase(self, tracker):
        """Test getting features by phase"""
        # Start multiple features
        tracker.start_feature("feature_1")
        tracker.start_feature("feature_2")
        tracker.start_feature("feature_3")
        
        # All should be in RED
        assert len(tracker.get_features_in_phase(TDDPhase.RED)) == 3
        assert len(tracker.get_features_in_phase(TDDPhase.YELLOW)) == 0
        
        # Move some features
        tracker.transition_to("feature_1", TDDPhase.YELLOW)
        tracker.transition_to("feature_2", TDDPhase.YELLOW)
        
        assert len(tracker.get_features_in_phase(TDDPhase.RED)) == 1
        assert len(tracker.get_features_in_phase(TDDPhase.YELLOW)) == 2
        
        # Complete one
        tracker.transition_to("feature_1", TDDPhase.GREEN)
        
        assert len(tracker.get_features_in_phase(TDDPhase.GREEN)) == 1
        assert "feature_1" in tracker.get_features_in_phase(TDDPhase.GREEN)
    
    def test_visual_status(self, tracker):
        """Test visual status output"""
        # Untracked feature
        assert "Not tracked" in tracker.get_visual_status("unknown")
        
        # Tracked features
        tracker.start_feature("feature_1")
        status = tracker.get_visual_status("feature_1")
        assert "🔴" in status
        assert "RED" in status
        assert "failing" in status
        
        tracker.transition_to("feature_1", TDDPhase.YELLOW)
        status = tracker.get_visual_status("feature_1")
        assert "🟡" in status
        assert "YELLOW" in status
    
    def test_summary_report(self, tracker):
        """Test summary report generation"""
        # Add some features
        tracker.start_feature("auth_feature")
        tracker.start_feature("api_feature")
        tracker.start_feature("ui_feature")
        
        # Move them to different phases
        tracker.transition_to("auth_feature", TDDPhase.YELLOW, "Tests passing")
        tracker.transition_to("api_feature", TDDPhase.YELLOW)
        tracker.transition_to("api_feature", TDDPhase.GREEN, "Approved")
        
        report = tracker.get_summary_report()
        
        # Check report contents
        assert "TDD Phase Tracker Summary" in report
        assert "🔴 RED: 1 features" in report
        assert "🟡 YELLOW: 1 features" in report
        assert "🟢 GREEN: 1 features" in report
        assert "auth_feature" in report
        assert "api_feature" in report
        assert "ui_feature" in report
        assert "Last transition" in report
    
    def test_phase_duration(self, tracker):
        """Test phase duration calculation"""
        tracker.start_feature("feature_1")
        
        # Small delay to ensure measurable duration
        time.sleep(0.1)
        
        tracker.transition_to("feature_1", TDDPhase.YELLOW)
        
        # Check RED phase duration
        red_duration = tracker.get_phase_duration("feature_1", TDDPhase.RED)
        assert red_duration is not None
        assert red_duration >= 0.1
        
        # Check current phase duration (still in YELLOW)
        yellow_duration = tracker.get_phase_duration("feature_1", TDDPhase.YELLOW)
        assert yellow_duration is not None
        assert yellow_duration >= 0
        
        # Check phase never entered
        green_duration = tracker.get_phase_duration("feature_1", TDDPhase.GREEN)
        assert green_duration is None
    
    def test_enforce_red_phase_start(self, tracker):
        """Test RED phase enforcement for TDD compliance"""
        # Feature not tracked
        with pytest.raises(InvalidPhaseTransition, match="must start with RED phase"):
            tracker.enforce_red_phase_start("feature_1")
        
        # Feature in RED phase (valid)
        tracker.start_feature("feature_1")
        tracker.enforce_red_phase_start("feature_1")  # Should not raise
        
        # Feature in other phase
        tracker.transition_to("feature_1", TDDPhase.YELLOW)
        with pytest.raises(InvalidPhaseTransition, match="Cannot start implementation"):
            tracker.enforce_red_phase_start("feature_1")
    
    def test_multiple_features_workflow(self, tracker):
        """Test tracking multiple features through complete workflow"""
        features = ["feature_1", "feature_2", "feature_3"]
        
        # Start all features
        for f in features:
            tracker.start_feature(f)
        
        # Simulate different progress
        tracker.transition_to("feature_1", TDDPhase.YELLOW)
        tracker.transition_to("feature_1", TDDPhase.GREEN)
        
        tracker.transition_to("feature_2", TDDPhase.YELLOW)
        tracker.transition_to("feature_2", TDDPhase.RED, "Review failed")
        
        # feature_3 stays in RED
        
        # Verify final states
        assert tracker.is_feature_complete("feature_1")
        assert not tracker.is_feature_complete("feature_2")
        assert not tracker.is_feature_complete("feature_3")
        
        assert tracker.get_current_phase("feature_1") == TDDPhase.GREEN
        assert tracker.get_current_phase("feature_2") == TDDPhase.RED
        assert tracker.get_current_phase("feature_3") == TDDPhase.RED
    
    def test_transition_metadata(self, tracker):
        """Test that transition metadata is stored correctly"""
        tracker.start_feature("feature_1")
        
        metadata = {
            "tests_failed": 3,
            "tests_passed": 0,
            "error_messages": ["Test X failed", "Test Y failed"]
        }
        
        tracker.transition_to("feature_1", TDDPhase.YELLOW, "Tests fixed", metadata)
        
        history = tracker.get_phase_history("feature_1")
        last_transition = history[-1]
        
        assert last_transition.metadata == metadata
        assert last_transition.reason == "Tests fixed"


class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_empty_tracker_operations(self):
        """Test operations on empty tracker"""
        tracker = TDDPhaseTracker()
        
        assert tracker.get_all_features() == {}
        assert tracker.get_features_in_phase(TDDPhase.RED) == []
        assert tracker.get_summary_report() == "No features being tracked"
    
    def test_concurrent_features(self):
        """Test handling many concurrent features"""
        tracker = TDDPhaseTracker()
        
        # Create many features
        for i in range(100):
            tracker.start_feature(f"feature_{i}")
        
        assert len(tracker.get_all_features()) == 100
        assert len(tracker.get_features_in_phase(TDDPhase.RED)) == 100
        
        # Transition half of them
        for i in range(50):
            tracker.transition_to(f"feature_{i}", TDDPhase.YELLOW)
        
        assert len(tracker.get_features_in_phase(TDDPhase.RED)) == 50
        assert len(tracker.get_features_in_phase(TDDPhase.YELLOW)) == 50


if __name__ == "__main__":
    pytest.main([__file__, "-v"])