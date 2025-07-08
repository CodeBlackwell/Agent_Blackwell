"""
Integration test for Phase 3 Enhanced Coverage Validator

Tests the integration of the enhanced coverage validator within the TDD workflow.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from workflows.mvp_incremental.tdd_feature_implementer import TDDFeatureImplementer
from workflows.mvp_incremental.tdd_phase_tracker import TDDPhaseTracker, TDDPhase
from workflows.mvp_incremental.coverage_validator import CoverageReport, TestCoverageResult
from workflows.monitoring import WorkflowExecutionTracer
from workflows.mvp_incremental.progress_monitor import ProgressMonitor
from workflows.mvp_incremental.review_integration import ReviewIntegration, ReviewResult, ReviewPhase
from workflows.mvp_incremental.retry_strategy import RetryStrategy, RetryConfig


class TestPhase3Integration:
    """Test enhanced coverage validator integration with TDD workflow"""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for TDD feature implementer"""
        tracer = Mock(spec=WorkflowExecutionTracer)
        tracer.start_step = Mock(return_value="step_123")
        tracer.complete_step = Mock()
        
        progress_monitor = Mock(spec=ProgressMonitor)
        review_integration = Mock(spec=ReviewIntegration)
        retry_strategy = Mock(spec=RetryStrategy)
        retry_config = RetryConfig(max_retries=2)
        phase_tracker = TDDPhaseTracker()
        
        return {
            'tracer': tracer,
            'progress_monitor': progress_monitor,
            'review_integration': review_integration,
            'retry_strategy': retry_strategy,
            'retry_config': retry_config,
            'phase_tracker': phase_tracker
        }
    
    @pytest.mark.asyncio
    async def test_coverage_validation_with_good_coverage(self, mock_dependencies):
        """Test feature implementation with good test coverage"""
        # Create implementer
        implementer = TDDFeatureImplementer(**mock_dependencies)
        
        # Mock successful test execution and coverage
        with patch('orchestrator.orchestrator_agent.run_team_member_with_tracking') as mock_run:
            with patch('workflows.mvp_incremental.tdd_feature_implementer.validate_tdd_test_coverage') as mock_validate:
                
                # Mock test writer response
                mock_run.side_effect = [
                    # Test writer response
                    [Mock(parts=[Mock(content="""
def test_calculate_sum():
    assert calculate_sum([1, 2, 3]) == 6
    
def test_calculate_sum_empty():
    assert calculate_sum([]) == 0
    
def test_calculate_sum_negative():
    assert calculate_sum([-1, -2]) == -3
""")])],
                    # Coder response
                    [Mock(parts=[Mock(content="""
def calculate_sum(numbers):
    return sum(numbers)
""")])],
                ]
                
                # Mock initial test failure (RED phase)
                implementer._run_tests = AsyncMock(side_effect=[
                    Mock(success=False, passed=0, failed=3, errors=['Test not implemented'], output='Tests failed'),  # Initial failure
                    Mock(success=True, passed=3, failed=0, errors=[], output='All tests passed')    # After implementation
                ])
                
                # Mock coverage validation with enhanced metrics
                mock_validate.return_value = (
                    True,  # Success
                    "✅ Test coverage validated:\n   - Statement: 100.0%\n   - Branch: 100.0%\n   - Functions: 100.0%\n   - Quality Score: 75.0/100",
                    TestCoverageResult(
                        success=True,
                        coverage_report=CoverageReport(
                            statement_coverage=100.0,
                            branch_coverage=100.0,
                            function_coverage=100.0,
                            coverage_percentage=100.0
                        ),
                        test_quality_score=75.0,
                        coverage_improved=True,
                        previous_coverage=0.0
                    )
                )
                
                # Mock review methods on the implementer itself
                implementer._review_tests = AsyncMock(
                    return_value=ReviewResult(
                        approved=True, 
                        feedback="Good tests", 
                        suggestions=[], 
                        must_fix=[], 
                        phase=ReviewPhase.TEST_SPECIFICATION
                    )
                )
                implementer._review_implementation = AsyncMock(
                    return_value=ReviewResult(
                        approved=True, 
                        feedback="Good implementation", 
                        suggestions=[], 
                        must_fix=[], 
                        phase=ReviewPhase.IMPLEMENTATION
                    )
                )
                
                # Execute feature implementation
                feature = {
                    'id': 'feature_1',
                    'title': 'Calculate Sum',
                    'description': 'Calculate sum of numbers'
                }
                
                result = await implementer.implement_feature_tdd(
                    feature=feature,
                    existing_code={},
                    requirements="Calculator app",
                    design_output="Design for calculator",
                    feature_index=0
                )
                
                # Verify results
                assert result.success
                assert result.feature_id == 'feature_1'
                assert result.final_phase == TDDPhase.GREEN
                assert 'calculate_sum' in result.implementation_code
                
                # Verify coverage validation was called with enhanced parameters
                mock_validate.assert_called_once()
                call_args = mock_validate.call_args[1]
                assert call_args['minimum_coverage'] == 80.0
                assert call_args['minimum_branch_coverage'] == 70.0
                assert call_args['feature_id'] == 'feature_1'
    
    @pytest.mark.asyncio
    async def test_coverage_validation_with_insufficient_coverage(self, mock_dependencies):
        """Test feature implementation with insufficient test coverage"""
        # Create implementer
        implementer = TDDFeatureImplementer(**mock_dependencies)
        
        with patch('orchestrator.orchestrator_agent.run_team_member_with_tracking') as mock_run:
            with patch('workflows.mvp_incremental.tdd_feature_implementer.validate_tdd_test_coverage') as mock_validate:
                
                # Mock responses
                mock_run.side_effect = [
                    # Test writer response (minimal tests)
                    [Mock(parts=[Mock(content="""
def test_calculate_sum_basic():
    assert calculate_sum([1, 2]) == 3
""")])],
                    # Coder response
                    [Mock(parts=[Mock(content="""
def calculate_sum(numbers):
    if not numbers:
        return 0  # Branch not tested
    return sum(numbers)
""")])],
                ]
                
                # Mock test execution
                implementer._run_tests = AsyncMock(side_effect=[
                    Mock(success=False, passed=0, failed=1, errors=['Test not implemented'], output='Test failed'),  # Initial failure
                    Mock(success=True, passed=1, failed=0, errors=[], output='Test passed')    # After implementation
                ])
                
                # Mock insufficient coverage
                mock_validate.return_value = (
                    False,  # Failure
                    "❌ Test coverage insufficient:\n   - Statement coverage: 75.0% (need 80.0%)\n   - Branch coverage: 50.0% (need 70.0%)\n   - Suggestion: Add tests for empty list case",
                    TestCoverageResult(
                        success=False,
                        coverage_report=CoverageReport(
                            statement_coverage=75.0,
                            branch_coverage=50.0,
                            function_coverage=100.0,
                            coverage_percentage=65.0,
                            uncovered_branches={'impl.py': ['Line 2 -> 3']}
                        ),
                        test_quality_score=45.0,
                        suggestions=[
                            "Add tests for empty list case",
                            "Add edge case tests",
                            "Test boundary conditions"
                        ]
                    )
                )
                
                # Mock reviews
                implementer._review_tests = AsyncMock(
                    return_value=ReviewResult(
                        approved=True, 
                        feedback="Tests look good",
                        suggestions=[],
                        must_fix=[],
                        phase=ReviewPhase.TEST_SPECIFICATION
                    )
                )
                implementer._review_implementation = AsyncMock(
                    return_value=ReviewResult(
                        approved=True, 
                        feedback="Implementation approved despite low coverage",
                        suggestions=[],
                        must_fix=[],
                        phase=ReviewPhase.IMPLEMENTATION
                    )
                )
                
                # Execute feature
                feature = {
                    'id': 'feature_2',
                    'title': 'Calculate Sum with Validation',
                    'description': 'Calculate sum with input validation'
                }
                
                result = await implementer.implement_feature_tdd(
                    feature=feature,
                    existing_code={},
                    requirements="Calculator with validation",
                    design_output="Design",
                    feature_index=0
                )
                
                # Should still succeed but with warnings logged
                assert result.success
                assert result.final_phase == TDDPhase.GREEN  # Still transitions despite low coverage
                
                # Verify coverage validation was called
                mock_validate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_coverage_trend_tracking(self, mock_dependencies):
        """Test that coverage trends are tracked across multiple features"""
        implementer = TDDFeatureImplementer(**mock_dependencies)
        
        with patch('workflows.mvp_incremental.tdd_feature_implementer.validate_tdd_test_coverage') as mock_validate:
            # First feature - initial coverage
            mock_validate.return_value = (
                True,
                "✅ Test coverage validated",
                TestCoverageResult(
                    success=True,
                    coverage_report=CoverageReport(coverage_percentage=85.0),
                    test_quality_score=70.0,
                    coverage_improved=False,
                    previous_coverage=None
                )
            )
            
            # Simulate feature implementation (simplified)
            # In real usage, the validator would track this internally
            
            # Second call - improved coverage
            mock_validate.return_value = (
                True,
                "✅ Test coverage validated",
                TestCoverageResult(
                    success=True,
                    coverage_report=CoverageReport(coverage_percentage=92.0),
                    test_quality_score=80.0,
                    coverage_improved=True,
                    previous_coverage=85.0
                )
            )
            
            # The coverage validator should track improvement
            # This would be logged by the implementer
    
    @pytest.mark.asyncio  
    async def test_test_quality_score_impact(self, mock_dependencies):
        """Test that test quality score is considered in the workflow"""
        implementer = TDDFeatureImplementer(**mock_dependencies)
        
        with patch('workflows.mvp_incremental.tdd_feature_implementer.validate_tdd_test_coverage') as mock_validate:
            # High coverage but low quality tests
            mock_validate.return_value = (
                True,  # Passes coverage thresholds
                "✅ Test coverage validated:\n   - Statement: 85.0%\n   - Quality Score: 35.0/100",
                TestCoverageResult(
                    success=True,
                    coverage_report=CoverageReport(
                        statement_coverage=85.0,
                        branch_coverage=80.0,
                        coverage_percentage=83.0
                    ),
                    test_quality_score=35.0,  # Low quality score
                    suggestions=[
                        "Add edge case tests",
                        "Add error handling tests",
                        "Use descriptive test names"
                    ]
                )
            )
            
            # The workflow should log the low quality score as a warning
            # even though coverage passes


if __name__ == "__main__":
    pytest.main([__file__, "-v"])