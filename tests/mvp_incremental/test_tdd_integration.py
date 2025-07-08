"""
Comprehensive Integration Tests for TDD Components (Phase 3b)

Tests the full integration of TDD phase tracking with the MVP incremental workflow,
including RED-YELLOW-GREEN transitions across all components.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

from workflows.mvp_incremental.tdd_phase_tracker import TDDPhase, TDDPhaseTracker
from workflows.mvp_incremental.testable_feature_parser import TestableFeatureParser, TestableFeature
from workflows.mvp_incremental.tdd_feature_implementer import TDDFeatureImplementer, TDDFeatureResult
from workflows.mvp_incremental.review_integration import ReviewIntegration, ReviewPhase, ReviewRequest, ReviewResult
from workflows.mvp_incremental.integration_verification import IntegrationVerifier, perform_integration_verification
from workflows.mvp_incremental.test_execution import TestExecutor, TestExecutionConfig, TestResult
from workflows.mvp_incremental.validator import CodeValidator
from workflows.monitoring import WorkflowExecutionTracer
from workflows.mvp_incremental.progress_monitor import ProgressMonitor
from workflows.mvp_incremental.retry_strategy import RetryStrategy, RetryConfig


class TestFullTDDWorkflow:
    """Test complete TDD workflow from feature parsing to integration verification."""
    
    @pytest.fixture
    def phase_tracker(self):
        """Create a TDD phase tracker."""
        return TDDPhaseTracker()
    
    @pytest.fixture
    def mock_components(self):
        """Create mock components for testing."""
        return {
            'tracer': Mock(spec=WorkflowExecutionTracer),
            'progress_monitor': Mock(spec=ProgressMonitor),
            'review_integration': Mock(spec=ReviewIntegration),
            'validator': Mock(spec=CodeValidator)
        }
    
    @pytest.fixture
    def sample_design_output(self):
        """Sample design output with features."""
        return """
FEATURE[1]: User Authentication
Description: Implement user login and registration
Input/Output: 
- Input: username, password
- Output: auth token or error
Edge Cases: 
- Empty credentials
- Invalid credentials
- Duplicate username
Dependencies: None

FEATURE[2]: Task Management
Description: CRUD operations for tasks
Dependencies: FEATURE[1]
Error Conditions:
- Unauthorized access
- Invalid task data
"""
    
    @pytest.mark.asyncio
    async def test_feature_parsing_with_tdd_fields(self, sample_design_output):
        """Test that features are parsed with TDD-related fields."""
        features = TestableFeatureParser.parse_features_with_criteria(sample_design_output)
        
        assert len(features) == 2
        
        # Check first feature
        auth_feature = features[0]
        assert auth_feature.id == "feature_1"
        assert auth_feature.title == "User Authentication"
        assert hasattr(auth_feature, 'test_files')
        assert hasattr(auth_feature, 'tdd_phase')
        assert auth_feature.tdd_phase is None  # Not set during parsing
        
        # Check test criteria
        assert len(auth_feature.test_criteria.edge_cases) > 0
        assert "Empty credentials" in auth_feature.test_criteria.edge_cases
    
    @pytest.mark.asyncio
    async def test_tdd_feature_implementation_flow(self, phase_tracker, mock_components):
        """Test the TDD implementation flow with phase transitions."""
        # Setup
        mock_components['tracer'].start_step.return_value = "step_1"
        mock_components['review_integration'].request_review = AsyncMock(
            return_value=ReviewResult(
                approved=True,
                feedback="Good implementation",
                suggestions=[],
                must_fix=[],
                phase=ReviewPhase.IMPLEMENTATION
            )
        )
        
        # Create implementer
        implementer = TDDFeatureImplementer(
            tracer=mock_components['tracer'],
            progress_monitor=mock_components['progress_monitor'],
            review_integration=mock_components['review_integration'],
            retry_strategy=RetryStrategy(),
            retry_config=RetryConfig(),
            phase_tracker=phase_tracker
        )
        
        # Mock the agent execution
        with patch('workflows.mvp_incremental.tdd_feature_implementer.run_team_member_with_tracking') as mock_run:
            # Mock test writer response
            mock_test_result = Mock()
            mock_test_result.parts = [Mock(content="test code here")]
            
            # Mock coder response
            mock_coder_result = Mock()
            mock_coder_result.parts = [Mock(content="implementation code here")]
            
            mock_run.side_effect = [mock_test_result, mock_coder_result]
            
            # Mock test execution
            with patch.object(implementer, '_run_tests') as mock_run_tests:
                # First call: tests fail (RED phase)
                mock_run_tests.side_effect = [
                    TestResult(
                        success=False,  # Tests fail without implementation
                        passed=0,
                        failed=3,
                        errors=["No implementation found"],
                        output="Tests failed as expected",
                        test_files=["test_auth.py"],
                        expected_failure=True
                    ),
                    # Second call: tests pass (after implementation)
                    TestResult(
                        success=True,
                        passed=3,
                        failed=0,
                        errors=[],
                        output="All tests passed",
                        test_files=["test_auth.py"],
                        expected_failure=False
                    )
                ]
                
                # Execute feature implementation
                feature = {
                    'id': 'feature_1',
                    'title': 'User Authentication',
                    'description': 'Implement login'
                }
                
                result = await implementer.implement_feature_tdd(
                    feature=feature,
                    existing_code={},
                    requirements="Build auth system",
                    design_output="Design details",
                    feature_index=0
                )
        
        # Verify phase transitions
        assert phase_tracker.get_current_phase('feature_1') == TDDPhase.GREEN
        
        # Verify result
        assert result.success is True
        assert result.final_phase == TDDPhase.GREEN
        assert result.initial_test_result.expected_failure is True
        assert result.final_test_result.success is True
    
    @pytest.mark.asyncio
    async def test_review_integration_with_tdd_phases(self, mock_components):
        """Test review integration for different TDD phases."""
        review_integration = ReviewIntegration(lambda msgs: AsyncMock()())
        
        # Test specification review (RED phase)
        test_review_request = ReviewRequest(
            phase=ReviewPhase.TEST_SPECIFICATION,
            content="def test_login(): assert False",
            context={
                'feature': {'title': 'Login', 'description': 'User login'},
                'purpose': 'TDD test review'
            }
        )
        
        with patch.object(review_integration, 'feature_reviewer_agent') as mock_agent:
            mock_agent.return_value = self._create_async_generator([
                "REVIEW: APPROVED\nFEEDBACK: Tests are comprehensive\nSUGGESTIONS:\n- Add edge case for locked accounts"
            ])
            
            result = await review_integration.request_review(test_review_request)
            
            assert result.approved is True
            assert "comprehensive" in result.feedback
            assert len(result.suggestions) == 1
    
    @pytest.mark.asyncio
    async def test_integration_verification_with_tdd(self, phase_tracker):
        """Test integration verification includes TDD compliance check."""
        # Setup phase tracker with features
        phase_tracker.start_feature("feature_1")
        phase_tracker.transition_to("feature_1", TDDPhase.YELLOW)
        phase_tracker.transition_to("feature_1", TDDPhase.GREEN)
        
        phase_tracker.start_feature("feature_2")
        phase_tracker.transition_to("feature_2", TDDPhase.YELLOW)
        # feature_2 stays in YELLOW (not reviewed)
        
        phase_tracker.start_feature("feature_3")
        # feature_3 stays in RED (no implementation)
        
        # Create verifier
        validator = Mock(spec=CodeValidator)
        verifier = IntegrationVerifier(validator, phase_tracker)
        
        # Mock test execution
        with patch.object(verifier, '_run_all_unit_tests') as mock_unit_tests:
            mock_unit_tests.return_value = TestResult(
                success=True, passed=10, failed=0, errors=[], 
                output="All tests passed", test_files=[]
            )
            
            with patch.object(verifier, '_run_integration_tests') as mock_int_tests:
                mock_int_tests.return_value = None
                
                with patch.object(verifier, '_run_smoke_test') as mock_smoke:
                    mock_smoke.return_value = (True, "App started successfully")
                    
                    with patch.object(verifier, '_verify_build') as mock_build:
                        mock_build.return_value = (True, "Build successful")
                        
                        with patch.object(verifier, '_check_feature_interactions') as mock_interactions:
                            mock_interactions.return_value = {}
                            
                            # Run verification
                            features = [
                                {'id': 'feature_1', 'name': 'Auth', 'status': 'completed'},
                                {'id': 'feature_2', 'name': 'Tasks', 'status': 'completed'},
                                {'id': 'feature_3', 'name': 'Reports', 'status': 'failed'}
                            ]
                            
                            result = await verifier.verify_integration(
                                Path("/tmp/generated"),
                                features,
                                Mock()
                            )
        
        # Check TDD compliance in result
        assert result.tdd_compliance == {
            'feature_1': '🟢 GREEN',
            'feature_2': '🟡 YELLOW',
            'feature_3': '🔴 RED'
        }
    
    @pytest.mark.asyncio
    async def test_completion_report_with_tdd_summary(self, phase_tracker):
        """Test that completion report includes TDD summary."""
        # Setup
        phase_tracker.start_feature("feature_1")
        phase_tracker.transition_to("feature_1", TDDPhase.YELLOW)
        phase_tracker.transition_to("feature_1", TDDPhase.GREEN)
        
        phase_tracker.start_feature("feature_2")
        # Stays in RED
        
        # Create integration result with TDD compliance
        from workflows.mvp_incremental.integration_verification import IntegrationTestResult, CompletionReport
        
        integration_result = IntegrationTestResult(
            all_tests_pass=True,
            unit_test_results=TestResult(
                success=True, passed=5, failed=0, errors=[], output="", test_files=[]
            ),
            integration_test_results=None,
            smoke_test_passed=True,
            smoke_test_output="OK",
            build_successful=True,
            build_output="Build OK",
            feature_interactions={},
            issues_found=[],
            tdd_compliance={
                'feature_1': '🟢 GREEN',
                'feature_2': '🔴 RED'
            }
        )
        
        # Generate report
        validator = Mock(spec=CodeValidator)
        verifier = IntegrationVerifier(validator, phase_tracker)
        
        report = await verifier.generate_completion_report(
            project_name="Test Project",
            features=[
                {'id': 'feature_1', 'name': 'Feature 1', 'status': 'completed'},
                {'id': 'feature_2', 'name': 'Feature 2', 'status': 'failed'}
            ],
            integration_result=integration_result,
            workflow_report=Mock(output_path="/tmp"),
            generated_path=Path("/tmp")
        )
        
        # Verify TDD summary in report
        assert hasattr(report, 'tdd_summary')
        assert report.tdd_summary['total_features'] == 2
        assert report.tdd_summary['phases']['GREEN'] == 1
        assert report.tdd_summary['phases']['RED'] == 1
        assert report.tdd_summary['compliance_rate'] == 50.0
    
    @pytest.mark.asyncio
    async def test_phase_violation_prevention(self, phase_tracker):
        """Test that implementation is prevented without RED phase."""
        implementer = TDDFeatureImplementer(
            tracer=Mock(),
            progress_monitor=Mock(),
            review_integration=Mock(),
            retry_strategy=RetryStrategy(),
            retry_config=RetryConfig(),
            phase_tracker=phase_tracker
        )
        
        # Try to enforce RED phase for untracked feature
        with pytest.raises(Exception) as exc_info:
            phase_tracker.enforce_red_phase_start("feature_x")
        
        assert "must start with RED phase" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_multi_feature_parallel_development(self, phase_tracker):
        """Test multiple features in different TDD phases."""
        # Simulate parallel feature development
        features = ["auth", "database", "api", "ui"]
        
        # Start all features
        for feature in features:
            phase_tracker.start_feature(feature)
        
        # Simulate different progress
        phase_tracker.transition_to("auth", TDDPhase.YELLOW)
        phase_tracker.transition_to("auth", TDDPhase.GREEN)
        
        phase_tracker.transition_to("database", TDDPhase.YELLOW)
        
        phase_tracker.transition_to("api", TDDPhase.YELLOW)
        phase_tracker.transition_to("api", TDDPhase.RED, "Review rejected")
        
        # ui stays in RED
        
        # Get summary
        summary = phase_tracker.get_summary_report()
        
        assert "auth" in summary
        assert "GREEN" in summary
        assert "database" in summary
        assert "YELLOW" in summary
        assert "2 features" in summary  # 2 in RED
    
    @pytest.mark.asyncio
    async def test_review_rejection_phase_regression(self, phase_tracker, mock_components):
        """Test that review rejection sends feature back to RED phase."""
        # Setup review to reject
        mock_components['review_integration'].request_review = AsyncMock(
            side_effect=[
                # First review: approve tests
                ReviewResult(
                    approved=True,
                    feedback="Tests look good",
                    suggestions=[],
                    must_fix=[],
                    phase=ReviewPhase.TEST_SPECIFICATION
                ),
                # Second review: reject implementation
                ReviewResult(
                    approved=False,
                    feedback="Implementation has issues",
                    suggestions=["Refactor the auth logic"],
                    must_fix=["Security vulnerability"],
                    phase=ReviewPhase.IMPLEMENTATION
                )
            ]
        )
        
        implementer = TDDFeatureImplementer(
            tracer=mock_components['tracer'],
            progress_monitor=mock_components['progress_monitor'],
            review_integration=mock_components['review_integration'],
            retry_strategy=RetryStrategy(),
            retry_config=RetryConfig(max_retries=0),  # No retries for this test
            phase_tracker=phase_tracker
        )
        
        # Mock agent responses
        with patch('workflows.mvp_incremental.tdd_feature_implementer.run_team_member_with_tracking') as mock_run:
            mock_run.side_effect = [
                Mock(parts=[Mock(content="test code")]),
                Mock(parts=[Mock(content="implementation code")])
            ]
            
            # Mock test execution
            with patch.object(implementer, '_run_tests') as mock_run_tests:
                mock_run_tests.side_effect = [
                    TestResult(success=False, passed=0, failed=1, errors=["No impl"], 
                              output="", test_files=[], expected_failure=True),
                    TestResult(success=True, passed=1, failed=0, errors=[], 
                              output="", test_files=[], expected_failure=False)
                ]
                
                feature = {'id': 'feature_1', 'title': 'Auth', 'description': 'Login'}
                result = await implementer.implement_feature_tdd(
                    feature, {}, "requirements", "design", 0
                )
        
        # Feature should be back in RED due to review rejection
        current_phase = phase_tracker.get_current_phase('feature_1')
        assert current_phase == TDDPhase.RED
        assert not result.success
    
    def _create_async_generator(self, items):
        """Helper to create async generator for testing."""
        async def gen():
            for item in items:
                yield Mock(content=item)
        return gen()


class TestTDDPhaseEnforcement:
    """Test strict TDD phase enforcement across components."""
    
    @pytest.mark.asyncio
    async def test_cannot_skip_test_writing(self):
        """Test that implementation cannot proceed without tests."""
        phase_tracker = TDDPhaseTracker()
        
        # Try to transition directly to YELLOW without starting in RED
        phase_tracker.start_feature("feature_1")
        
        # This should work (RED -> YELLOW is valid)
        phase_tracker.transition_to("feature_1", TDDPhase.YELLOW)
        
        # But we can verify the feature started in RED
        history = phase_tracker.get_phase_history("feature_1")
        assert history[0].to_phase == TDDPhase.RED
        assert history[1].to_phase == TDDPhase.YELLOW
    
    @pytest.mark.asyncio
    async def test_integration_with_incomplete_features(self):
        """Test integration verification with features in non-GREEN phases."""
        phase_tracker = TDDPhaseTracker()
        phase_tracker.start_feature("incomplete_feature")
        # Leave in RED
        
        result = await perform_integration_verification(
            generated_path=Path("/tmp/test"),
            features=[{'id': 'incomplete_feature', 'name': 'Incomplete', 'status': 'in_progress'}],
            workflow_report=Mock(),
            project_name="Test Project",
            phase_tracker=phase_tracker
        )
        
        # Verify warnings about incomplete features
        assert result[1].tdd_summary['phases']['RED'] > 0
        assert result[1].tdd_summary['compliance_rate'] < 100
    
    @pytest.mark.asyncio
    async def test_phase_duration_tracking(self):
        """Test that phase durations are tracked correctly."""
        phase_tracker = TDDPhaseTracker()
        phase_tracker.start_feature("timed_feature")
        
        # Small delay
        await asyncio.sleep(0.1)
        
        phase_tracker.transition_to("timed_feature", TDDPhase.YELLOW)
        
        # Check RED phase duration
        red_duration = phase_tracker.get_phase_duration("timed_feature", TDDPhase.RED)
        assert red_duration is not None
        assert red_duration >= 0.1
        
        # YELLOW phase is still active
        yellow_duration = phase_tracker.get_phase_duration("timed_feature", TDDPhase.YELLOW)
        assert yellow_duration is not None
        assert yellow_duration >= 0


class TestReportingAndVisualization:
    """Test TDD reporting and visualization features."""
    
    def test_visual_phase_indicators(self):
        """Test visual indicators for phases."""
        phase_tracker = TDDPhaseTracker()
        phase_tracker.start_feature("visual_test")
        
        # RED phase
        status = phase_tracker.get_visual_status("visual_test")
        assert "🔴" in status
        assert "RED" in status
        
        # YELLOW phase
        phase_tracker.transition_to("visual_test", TDDPhase.YELLOW)
        status = phase_tracker.get_visual_status("visual_test")
        assert "🟡" in status
        assert "YELLOW" in status
        
        # GREEN phase
        phase_tracker.transition_to("visual_test", TDDPhase.GREEN)
        status = phase_tracker.get_visual_status("visual_test")
        assert "🟢" in status
        assert "GREEN" in status
    
    def test_comprehensive_summary_report(self):
        """Test comprehensive summary report generation."""
        phase_tracker = TDDPhaseTracker()
        
        # Create diverse feature states
        features = [
            ("login", [TDDPhase.YELLOW, TDDPhase.GREEN]),
            ("signup", [TDDPhase.YELLOW, TDDPhase.RED]),  # Rejected
            ("profile", [TDDPhase.YELLOW]),  # In progress
            ("settings", []),  # Just started
            ("logout", [TDDPhase.YELLOW, TDDPhase.GREEN])  # Complete
        ]
        
        for feature, transitions in features:
            phase_tracker.start_feature(feature)
            for phase in transitions:
                phase_tracker.transition_to(feature, phase, f"Transition to {phase.value}")
        
        report = phase_tracker.get_summary_report()
        
        # Verify report contents
        assert "TDD Phase Tracker Summary" in report
        assert "🔴 RED: 2 features" in report  # signup (rejected) and settings
        assert "🟡 YELLOW: 1 features" in report  # profile
        assert "🟢 GREEN: 2 features" in report  # login and logout
        assert "Last transition" in report
        
        # Check all features are listed
        for feature, _ in features:
            assert feature in report


if __name__ == "__main__":
    pytest.main([__file__, "-v"])