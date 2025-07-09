"""
Unit tests for YELLOW Phase Orchestrator

Tests the YELLOW phase logic where tests pass and implementation
awaits review approval before transitioning to GREEN.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch, AsyncMock

from workflows.mvp_incremental.yellow_phase import (
    YellowPhaseOrchestrator, 
    YellowPhaseContext, 
    YellowPhaseError
)
from workflows.mvp_incremental.tdd_phase_tracker import TDDPhase, TDDPhaseTracker
from workflows.mvp_incremental.testable_feature_parser import TestableFeature
from workflows.mvp_incremental.test_execution import TestResult


class TestYellowPhaseOrchestrator:
    """Test suite for YellowPhaseOrchestrator"""
    
    @pytest.fixture
    def phase_tracker(self):
        """Create a mock phase tracker"""
        tracker = Mock(spec=TDDPhaseTracker)
        tracker.get_current_phase = Mock(return_value=TDDPhase.RED)
        tracker.transition_to = Mock()
        tracker.get_visual_status = Mock(return_value="🟡 YELLOW: Tests passing - awaiting review")
        return tracker
        
    @pytest.fixture
    def orchestrator(self, phase_tracker):
        """Create a YellowPhaseOrchestrator instance"""
        return YellowPhaseOrchestrator(phase_tracker)
        
    @pytest.fixture
    def test_feature(self):
        """Create a test feature"""
        return TestableFeature(
            id="feature_1",
            title="User Authentication",
            description="Implement user authentication with login and logout functionality",
            test_criteria=["User can login", "Invalid credentials rejected"]
        )
        
    @pytest.fixture
    def passing_test_result(self):
        """Create a passing test result"""
        result = Mock(spec=TestResult)
        result.success = True
        result.passed = 5
        result.failed = 0
        result.stdout = "All tests passed!"
        result.logs = ["test_login", "test_invalid_creds", "test_logout", "test_session", "test_timeout"]
        return result
        
    @pytest.fixture
    def failing_test_result(self):
        """Create a failing test result"""
        result = Mock(spec=TestResult)
        result.success = False
        result.passed = 3
        result.failed = 2
        result.stdout = "Some tests failed"
        result.logs = ["test_login", "test_invalid_creds", "test_logout"]
        return result
        
    @pytest.mark.asyncio
    async def test_enter_yellow_phase_from_red(self, orchestrator, test_feature, passing_test_result, phase_tracker):
        """Test entering YELLOW phase from RED with passing tests"""
        # Setup
        phase_tracker.get_current_phase.return_value = TDDPhase.RED
        
        # Execute
        context = await orchestrator.enter_yellow_phase(
            feature=test_feature,
            test_results=passing_test_result,
            implementation_path="src/auth.py",
            implementation_summary="Implemented authentication with JWT"
        )
        
        # Assert
        assert context.feature == test_feature
        assert context.test_results == passing_test_result
        assert context.implementation_path == "src/auth.py"
        assert context.implementation_summary == "Implemented authentication with JWT"
        assert context.review_attempts == 0
        assert len(context.previous_feedback) == 0
        assert isinstance(context.time_entered_yellow, datetime)
        
        # Verify phase transition
        phase_tracker.transition_to.assert_called_once()
        call_args = phase_tracker.transition_to.call_args
        assert call_args[0][0] == "feature_1"
        assert call_args[0][1] == TDDPhase.YELLOW
        assert "Tests passing - awaiting review" in call_args[0][2]
        
        # Verify context stored
        assert "feature_1" in orchestrator.yellow_contexts
        
    @pytest.mark.asyncio
    async def test_enter_yellow_phase_already_in_yellow(self, orchestrator, test_feature, passing_test_result, phase_tracker):
        """Test re-entering YELLOW phase when already in YELLOW (retry scenario)"""
        # Setup
        phase_tracker.get_current_phase.return_value = TDDPhase.YELLOW
        
        # Execute
        context = await orchestrator.enter_yellow_phase(
            feature=test_feature,
            test_results=passing_test_result,
            implementation_path="src/auth.py"
        )
        
        # Should succeed (allows re-entry for retries)
        assert context is not None
        phase_tracker.transition_to.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_enter_yellow_phase_from_green_fails(self, orchestrator, test_feature, passing_test_result, phase_tracker):
        """Test that entering YELLOW from GREEN phase fails"""
        # Setup
        phase_tracker.get_current_phase.return_value = TDDPhase.GREEN
        
        # Execute & Assert
        with pytest.raises(YellowPhaseError) as exc_info:
            await orchestrator.enter_yellow_phase(
                feature=test_feature,
                test_results=passing_test_result,
                implementation_path="src/auth.py"
            )
            
        assert "Cannot enter YELLOW phase from GREEN" in str(exc_info.value)
        phase_tracker.transition_to.assert_not_called()
        
    @pytest.mark.asyncio
    async def test_enter_yellow_phase_with_failing_tests(self, orchestrator, test_feature, failing_test_result, phase_tracker):
        """Test that entering YELLOW with failing tests raises error"""
        # Setup
        phase_tracker.get_current_phase.return_value = TDDPhase.RED
        
        # Execute & Assert
        with pytest.raises(YellowPhaseError) as exc_info:
            await orchestrator.enter_yellow_phase(
                feature=test_feature,
                test_results=failing_test_result,
                implementation_path="src/auth.py"
            )
            
        assert "Cannot enter YELLOW phase with failing tests" in str(exc_info.value)
        phase_tracker.transition_to.assert_not_called()
        
    def test_prepare_review_context(self, orchestrator, test_feature, passing_test_result):
        """Test preparing review context for a feature in YELLOW phase"""
        # Setup - manually add a context
        context = YellowPhaseContext(
            feature=test_feature,
            test_results=passing_test_result,
            implementation_path="src/auth.py",
            time_entered_yellow=datetime.now() - timedelta(minutes=5),
            review_attempts=1,
            previous_feedback=["Consider adding input validation", "Good test coverage"],
            implementation_summary="JWT-based authentication"
        )
        orchestrator.yellow_contexts["feature_1"] = context
        
        # Execute
        review_context = orchestrator.prepare_review_context("feature_1")
        
        # Assert
        assert review_context["feature"]["id"] == "feature_1"
        assert review_context["feature"]["title"] == "User Authentication"
        assert review_context["implementation"]["path"] == "src/auth.py"
        assert review_context["implementation"]["summary"] == "JWT-based authentication"
        assert review_context["test_status"]["all_passing"] is True
        assert review_context["test_status"]["test_count"] == 5
        assert review_context["yellow_phase_info"]["review_attempts"] == 1
        assert review_context["yellow_phase_info"]["has_previous_feedback"] is True
        assert len(review_context["previous_feedback"]) == 2
        assert review_context["yellow_phase_info"]["time_in_phase_seconds"] >= 300  # 5 minutes
        
    def test_prepare_review_context_no_context(self, orchestrator):
        """Test preparing review context when feature not in YELLOW"""
        with pytest.raises(YellowPhaseError) as exc_info:
            orchestrator.prepare_review_context("unknown_feature")
            
        assert "No YELLOW phase context found" in str(exc_info.value)
        
    @pytest.mark.asyncio
    async def test_handle_review_approved(self, orchestrator, test_feature, passing_test_result, phase_tracker):
        """Test handling approved review - transition to GREEN"""
        # Setup
        context = YellowPhaseContext(
            feature=test_feature,
            test_results=passing_test_result,
            implementation_path="src/auth.py",
            time_entered_yellow=datetime.now(),
            review_attempts=0
        )
        orchestrator.yellow_contexts["feature_1"] = context
        
        # Execute
        next_phase = await orchestrator.handle_review_result(
            feature_id="feature_1",
            approved=True,
            feedback="Looks good! Well-structured code."
        )
        
        # Assert
        assert next_phase == TDDPhase.GREEN.value
        assert context.review_attempts == 1
        assert "Looks good! Well-structured code." in context.previous_feedback
        
        # Verify phase transition
        phase_tracker.transition_to.assert_called_once()
        call_args = phase_tracker.transition_to.call_args
        assert call_args[0][0] == "feature_1"
        assert call_args[0][1] == TDDPhase.GREEN
        assert "Implementation approved after 1 review(s)" in call_args[0][2]
        
        # Verify context cleaned up
        assert "feature_1" not in orchestrator.yellow_contexts
        
    @pytest.mark.asyncio
    async def test_handle_review_rejected(self, orchestrator, test_feature, passing_test_result, phase_tracker):
        """Test handling rejected review - transition back to RED"""
        # Setup
        context = YellowPhaseContext(
            feature=test_feature,
            test_results=passing_test_result,
            implementation_path="src/auth.py",
            time_entered_yellow=datetime.now(),
            review_attempts=1,
            previous_feedback=["Add error handling"]
        )
        orchestrator.yellow_contexts["feature_1"] = context
        
        # Execute
        next_phase = await orchestrator.handle_review_result(
            feature_id="feature_1",
            approved=False,
            feedback="Need better error handling and logging"
        )
        
        # Assert
        assert next_phase == TDDPhase.RED.value
        assert context.review_attempts == 2
        assert "Need better error handling and logging" in context.previous_feedback
        assert len(context.previous_feedback) == 2
        
        # Verify phase transition
        phase_tracker.transition_to.assert_called_once()
        call_args = phase_tracker.transition_to.call_args
        assert call_args[0][0] == "feature_1"
        assert call_args[0][1] == TDDPhase.RED
        assert "Implementation needs revision - review attempt 2" in call_args[0][2]
        
        # Context should still exist (for retry)
        assert "feature_1" in orchestrator.yellow_contexts
        
    @pytest.mark.asyncio
    async def test_handle_review_no_context(self, orchestrator, phase_tracker):
        """Test handling review when no YELLOW context exists"""
        with pytest.raises(YellowPhaseError) as exc_info:
            await orchestrator.handle_review_result(
                feature_id="unknown_feature",
                approved=True
            )
            
        assert "No YELLOW phase context found" in str(exc_info.value)
        phase_tracker.transition_to.assert_not_called()
        
    def test_get_phase_metrics(self, orchestrator, test_feature, passing_test_result):
        """Test getting metrics for YELLOW phase"""
        # Setup
        context = YellowPhaseContext(
            feature=test_feature,
            test_results=passing_test_result,
            implementation_path="src/auth.py",
            time_entered_yellow=datetime.now() - timedelta(minutes=10),
            review_attempts=2,
            previous_feedback=["Fix imports", "Add docstrings", "Improve variable names"]
        )
        orchestrator.yellow_contexts["feature_1"] = context
        
        # Execute
        metrics = orchestrator.get_phase_metrics("feature_1")
        
        # Assert
        assert metrics["feature_id"] == "feature_1"
        assert metrics["phase"] == TDDPhase.YELLOW.value
        assert metrics["time_in_phase_seconds"] >= 600  # 10 minutes
        assert "10." in metrics["time_in_phase_formatted"]  # ~10 minutes
        assert metrics["review_attempts"] == 2
        assert metrics["has_feedback"] is True
        assert metrics["feedback_count"] == 3
        
    def test_get_phase_metrics_no_context(self, orchestrator):
        """Test getting metrics when no context exists"""
        metrics = orchestrator.get_phase_metrics("unknown_feature")
        assert metrics == {"error": "No YELLOW phase context found"}
        
    def test_format_duration(self, orchestrator):
        """Test duration formatting"""
        assert orchestrator._format_duration(45) == "45s"
        assert orchestrator._format_duration(90) == "1.5m"
        assert orchestrator._format_duration(3900) == "1.1h"
        
    def test_get_all_yellow_features(self, orchestrator, test_feature, passing_test_result):
        """Test getting all features in YELLOW phase"""
        # Setup multiple contexts
        context1 = YellowPhaseContext(
            feature=test_feature,
            test_results=passing_test_result,
            implementation_path="src/auth.py",
            time_entered_yellow=datetime.now()
        )
        
        feature2 = TestableFeature(
            id="feature_2",
            title="Data Validation",
            description="Implement data validation with error handling",
            test_criteria=["Validate input", "Handle errors"]
        )
        context2 = YellowPhaseContext(
            feature=feature2,
            test_results=passing_test_result,
            implementation_path="src/validation.py",
            time_entered_yellow=datetime.now()
        )
        
        orchestrator.yellow_contexts["feature_1"] = context1
        orchestrator.yellow_contexts["feature_2"] = context2
        
        # Execute
        yellow_features = orchestrator.get_all_yellow_features()
        
        # Assert
        assert len(yellow_features) == 2
        assert "feature_1" in yellow_features
        assert "feature_2" in yellow_features
        
    def test_clear_context(self, orchestrator, test_feature, passing_test_result):
        """Test clearing YELLOW phase context"""
        # Setup
        context = YellowPhaseContext(
            feature=test_feature,
            test_results=passing_test_result,
            implementation_path="src/auth.py",
            time_entered_yellow=datetime.now()
        )
        orchestrator.yellow_contexts["feature_1"] = context
        
        # Execute
        orchestrator.clear_context("feature_1")
        
        # Assert
        assert "feature_1" not in orchestrator.yellow_contexts
        
        # Clear non-existent should not raise
        orchestrator.clear_context("non_existent")  # Should not raise
        
    def test_yellow_phase_context_to_dict(self, test_feature, passing_test_result):
        """Test YellowPhaseContext serialization"""
        # Setup
        context = YellowPhaseContext(
            feature=test_feature,
            test_results=passing_test_result,
            implementation_path="src/auth.py",
            time_entered_yellow=datetime.now() - timedelta(minutes=3),
            review_attempts=1,
            previous_feedback=["Add tests"],
            implementation_summary="Basic auth implementation",
            test_coverage_info={"lines": 85, "branches": 70}
        )
        
        # Execute
        context_dict = context.to_dict()
        
        # Assert
        assert context_dict["feature_id"] == "feature_1"
        assert context_dict["feature_title"] == "User Authentication"
        assert context_dict["test_results"]["success"] is True
        assert context_dict["test_results"]["test_count"] == 5
        assert context_dict["implementation_path"] == "src/auth.py"
        assert context_dict["review_attempts"] == 1
        assert context_dict["previous_feedback"] == ["Add tests"]
        assert context_dict["implementation_summary"] == "Basic auth implementation"
        assert context_dict["phase_duration_seconds"] >= 180  # 3 minutes
        assert "T" in context_dict["time_entered_yellow"]  # ISO format