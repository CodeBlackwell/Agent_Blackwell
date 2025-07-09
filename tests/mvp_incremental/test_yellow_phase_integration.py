"""
Integration tests for YELLOW phase workflow transitions

Tests the complete workflow from RED → YELLOW → GREEN/RED transitions
with full integration of all components.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from workflows.mvp_incremental.tdd_phase_tracker import TDDPhase, TDDPhaseTracker
from workflows.mvp_incremental.yellow_phase import YellowPhaseOrchestrator
from workflows.mvp_incremental.tdd_feature_implementer import TDDFeatureImplementer
from workflows.mvp_incremental.testable_feature_parser import TestableFeature
from workflows.mvp_incremental.progress_monitor import ProgressMonitor, StepStatus
from workflows.mvp_incremental.review_integration import ReviewIntegration, ReviewResult, ReviewPhase
from workflows.mvp_incremental.retry_strategy import RetryStrategy, RetryConfig
from workflows.monitoring import WorkflowExecutionTracer


class TestYellowPhaseIntegration:
    """Integration tests for YELLOW phase workflow"""
    
    @pytest.fixture
    def setup_components(self):
        """Setup all required components for integration testing"""
        # Create real components
        phase_tracker = TDDPhaseTracker()
        yellow_orchestrator = YellowPhaseOrchestrator(phase_tracker)
        progress_monitor = ProgressMonitor()
        
        # Create mock components
        tracer = Mock(spec=WorkflowExecutionTracer)
        tracer.start_step = Mock(return_value="step_1")
        tracer.complete_step = Mock()
        tracer.error_count = 0
        
        review_integration = Mock(spec=ReviewIntegration)
        retry_strategy = Mock(spec=RetryStrategy)
        retry_config = RetryConfig()
        
        # Create TDD implementer with real yellow orchestrator
        implementer = TDDFeatureImplementer(
            tracer=tracer,
            progress_monitor=progress_monitor,
            review_integration=review_integration,
            retry_strategy=retry_strategy,
            retry_config=retry_config,
            phase_tracker=phase_tracker
        )
        
        # Manually inject yellow orchestrator (since constructor creates its own)
        implementer.yellow_phase_orchestrator = yellow_orchestrator
        
        return {
            'implementer': implementer,
            'phase_tracker': phase_tracker,
            'yellow_orchestrator': yellow_orchestrator,
            'progress_monitor': progress_monitor,
            'review_integration': review_integration,
            'tracer': tracer
        }
        
    @pytest.fixture
    def test_feature(self):
        """Create a test feature"""
        return TestableFeature(
            id="auth_feature",
            title="User Authentication",
            description="Implement secure user authentication",
            test_criteria=["User can login", "Invalid credentials rejected", "Session management"]
        )
        
    @pytest.mark.asyncio
    async def test_red_to_yellow_transition(self, setup_components, test_feature):
        """Test transition from RED phase to YELLOW phase when tests pass"""
        components = setup_components
        implementer = components['implementer']
        phase_tracker = components['phase_tracker']
        yellow_orchestrator = components['yellow_orchestrator']
        
        # Setup initial RED phase
        phase_tracker.start_feature(test_feature.id, {"title": test_feature.title})
        
        # Mock successful test execution
        passing_test_result = Mock()
        passing_test_result.success = True
        passing_test_result.passed = 3
        passing_test_result.failed = 0
        passing_test_result.logs = ["test_login", "test_invalid_creds", "test_session"]
        passing_test_result.stdout = "All tests passed!"
        
        # Enter YELLOW phase
        context = await yellow_orchestrator.enter_yellow_phase(
            feature=test_feature,
            test_results=passing_test_result,
            implementation_path="src/auth.py",
            implementation_summary="Implemented authentication with JWT tokens"
        )
        
        # Verify transition
        assert phase_tracker.get_current_phase(test_feature.id) == TDDPhase.YELLOW
        assert test_feature.id in yellow_orchestrator.yellow_contexts
        assert context.review_attempts == 0
        assert context.implementation_summary == "Implemented authentication with JWT tokens"
        
    @pytest.mark.asyncio
    async def test_yellow_to_green_transition(self, setup_components, test_feature):
        """Test transition from YELLOW to GREEN when review is approved"""
        components = setup_components
        phase_tracker = components['phase_tracker']
        yellow_orchestrator = components['yellow_orchestrator']
        review_integration = components['review_integration']
        
        # Setup YELLOW phase
        phase_tracker.start_feature(test_feature.id, {"title": test_feature.title})
        passing_test_result = Mock(success=True, passed=3, failed=0, logs=["test1", "test2", "test3"])
        
        await yellow_orchestrator.enter_yellow_phase(
            feature=test_feature,
            test_results=passing_test_result,
            implementation_path="src/auth.py"
        )
        
        # Mock approved review
        review_result = ReviewResult(
            approved=True,
            feedback="Great implementation! Code is clean and well-tested.",
            suggestions=[],
            must_fix=[],
            phase=ReviewPhase.IMPLEMENTATION,
            feature_id=test_feature.id
        )
        review_integration.review_implementation = AsyncMock(return_value=review_result)
        
        # Handle review approval
        next_phase = await yellow_orchestrator.handle_review_result(
            feature_id=test_feature.id,
            approved=True,
            feedback=review_result.feedback
        )
        
        # Verify transition to GREEN
        assert next_phase == TDDPhase.GREEN.value
        assert phase_tracker.get_current_phase(test_feature.id) == TDDPhase.GREEN
        assert test_feature.id not in yellow_orchestrator.yellow_contexts  # Context cleaned up
        
    @pytest.mark.asyncio
    async def test_yellow_to_red_transition(self, setup_components, test_feature):
        """Test transition from YELLOW back to RED when review is rejected"""
        components = setup_components
        phase_tracker = components['phase_tracker']
        yellow_orchestrator = components['yellow_orchestrator']
        
        # Setup YELLOW phase
        phase_tracker.start_feature(test_feature.id, {"title": test_feature.title})
        passing_test_result = Mock(success=True, passed=3, failed=0, logs=["test1", "test2", "test3"])
        
        await yellow_orchestrator.enter_yellow_phase(
            feature=test_feature,
            test_results=passing_test_result,
            implementation_path="src/auth.py"
        )
        
        # Handle review rejection
        next_phase = await yellow_orchestrator.handle_review_result(
            feature_id=test_feature.id,
            approved=False,
            feedback="Need better error handling and input validation"
        )
        
        # Verify transition back to RED
        assert next_phase == TDDPhase.RED.value
        assert phase_tracker.get_current_phase(test_feature.id) == TDDPhase.RED
        assert test_feature.id in yellow_orchestrator.yellow_contexts  # Context preserved for retry
        
        # Verify feedback stored
        context = yellow_orchestrator.yellow_contexts[test_feature.id]
        assert context.review_attempts == 1
        assert "Need better error handling" in context.previous_feedback[0]
        
    @pytest.mark.asyncio
    async def test_multiple_review_attempts(self, setup_components, test_feature):
        """Test multiple review attempts in YELLOW phase"""
        components = setup_components
        phase_tracker = components['phase_tracker']
        yellow_orchestrator = components['yellow_orchestrator']
        
        # Setup YELLOW phase
        phase_tracker.start_feature(test_feature.id, {"title": test_feature.title})
        passing_test_result = Mock(success=True, passed=3, failed=0, logs=["test1", "test2", "test3"])
        
        await yellow_orchestrator.enter_yellow_phase(
            feature=test_feature,
            test_results=passing_test_result,
            implementation_path="src/auth.py"
        )
        
        # First rejection
        await yellow_orchestrator.handle_review_result(
            feature_id=test_feature.id,
            approved=False,
            feedback="Add error handling"
        )
        
        # Re-enter YELLOW after fixes
        phase_tracker.transition_to(test_feature.id, TDDPhase.YELLOW, "Tests passing again")
        
        # Second rejection
        await yellow_orchestrator.handle_review_result(
            feature_id=test_feature.id,
            approved=False,
            feedback="Improve logging"
        )
        
        # Verify multiple attempts tracked
        context = yellow_orchestrator.yellow_contexts[test_feature.id]
        assert context.review_attempts == 2
        assert len(context.previous_feedback) == 2
        assert "Add error handling" in context.previous_feedback[0]
        assert "Improve logging" in context.previous_feedback[1]
        
    @pytest.mark.asyncio
    async def test_progress_monitor_integration(self, setup_components, test_feature):
        """Test progress monitor updates during YELLOW phase"""
        components = setup_components
        progress_monitor = components['progress_monitor']
        yellow_orchestrator = components['yellow_orchestrator']
        phase_tracker = components['phase_tracker']
        
        # Initialize progress monitor
        progress_monitor.start_workflow(total_features=1)
        progress_monitor.start_feature(test_feature.id, test_feature.title, feature_num=1)
        
        # Setup and enter YELLOW phase
        phase_tracker.start_feature(test_feature.id, {"title": test_feature.title})
        passing_test_result = Mock(success=True, passed=3, failed=0, logs=["test1", "test2", "test3"])
        
        await yellow_orchestrator.enter_yellow_phase(
            feature=test_feature,
            test_results=passing_test_result,
            implementation_path="src/auth.py"
        )
        
        # Update progress monitor
        progress_monitor.update_tdd_phase(test_feature.id, "YELLOW", StepStatus.AWAITING_REVIEW)
        
        # Verify progress monitor state
        feature_progress = progress_monitor.features[test_feature.id]
        assert feature_progress.tdd_phase == "YELLOW"
        assert feature_progress.current_status == StepStatus.AWAITING_REVIEW
        assert feature_progress.time_entered_yellow is not None
        
    @pytest.mark.asyncio
    async def test_review_context_preparation(self, setup_components, test_feature):
        """Test review context preparation with all details"""
        components = setup_components
        yellow_orchestrator = components['yellow_orchestrator']
        phase_tracker = components['phase_tracker']
        
        # Setup YELLOW phase with context
        phase_tracker.start_feature(test_feature.id, {"title": test_feature.title})
        passing_test_result = Mock(
            success=True, 
            passed=5, 
            failed=0, 
            logs=["test1", "test2", "test3", "test4", "test5"],
            execution_time=2.5
        )
        
        await yellow_orchestrator.enter_yellow_phase(
            feature=test_feature,
            test_results=passing_test_result,
            implementation_path="src/auth.py",
            implementation_summary="JWT-based authentication with refresh tokens"
        )
        
        # Add some review history
        await yellow_orchestrator.handle_review_result(
            feature_id=test_feature.id,
            approved=False,
            feedback="Add rate limiting"
        )
        
        # Prepare review context
        review_context = yellow_orchestrator.prepare_review_context(test_feature.id)
        
        # Verify context contains all necessary information
        assert review_context['feature']['id'] == test_feature.id
        assert review_context['feature']['title'] == "User Authentication"
        assert len(review_context['feature']['test_criteria']) == 3
        
        assert review_context['implementation']['path'] == "src/auth.py"
        assert "JWT-based authentication" in review_context['implementation']['summary']
        
        assert review_context['test_status']['all_passing'] is True
        assert review_context['test_status']['test_count'] == 5
        
        assert review_context['yellow_phase_info']['review_attempts'] == 1
        assert review_context['yellow_phase_info']['has_previous_feedback'] is True
        assert len(review_context['previous_feedback']) == 1
        
    @pytest.mark.asyncio
    async def test_yellow_phase_metrics(self, setup_components, test_feature):
        """Test YELLOW phase metrics collection"""
        components = setup_components
        yellow_orchestrator = components['yellow_orchestrator']
        phase_tracker = components['phase_tracker']
        
        # Setup YELLOW phase
        phase_tracker.start_feature(test_feature.id, {"title": test_feature.title})
        passing_test_result = Mock(success=True, passed=3, failed=0, logs=["test1", "test2", "test3"])
        
        await yellow_orchestrator.enter_yellow_phase(
            feature=test_feature,
            test_results=passing_test_result,
            implementation_path="src/auth.py"
        )
        
        # Wait a bit to accumulate time
        await asyncio.sleep(0.1)
        
        # Get metrics
        metrics = yellow_orchestrator.get_phase_metrics(test_feature.id)
        
        # Verify metrics
        assert metrics['feature_id'] == test_feature.id
        assert metrics['phase'] == TDDPhase.YELLOW.value
        assert metrics['time_in_phase_seconds'] >= 0.1
        assert metrics['review_attempts'] == 0
        assert metrics['has_feedback'] is False
        assert metrics['feedback_count'] == 0
        
    def test_get_all_yellow_features(self, setup_components):
        """Test getting all features currently in YELLOW phase"""
        components = setup_components
        yellow_orchestrator = components['yellow_orchestrator']
        
        # Create multiple features in YELLOW
        features = []
        for i in range(3):
            feature = TestableFeature(
                id=f"feature_{i}",
                title=f"Feature {i}",
                description=f"Description {i}",
                test_criteria=[f"Criteria {i}"]
            )
            features.append(feature)
            
            # Add to YELLOW contexts
            yellow_orchestrator.yellow_contexts[feature.id] = Mock()
            
        # Get all YELLOW features
        yellow_features = yellow_orchestrator.get_all_yellow_features()
        
        # Verify
        assert len(yellow_features) == 3
        assert all(f"feature_{i}" in yellow_features for i in range(3))