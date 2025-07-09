"""
End-to-End Tests for MVP Incremental TDD Workflow
Tests the complete TDD cycle with mandatory RED→YELLOW→GREEN phases
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import List, Dict, Any

from workflows.mvp_incremental.mvp_incremental import execute_mvp_incremental_workflow
from workflows.mvp_incremental.tdd_phase_tracker import TDDPhase, TDDPhaseTracker
from workflows.mvp_incremental.testable_feature_parser import TestableFeature
from workflows.mvp_incremental.tdd_feature_implementer import TDDFeatureResult
from shared.data_models import CodingTeamInput, TeamMemberResult, TeamMember
from workflows.monitoring import WorkflowExecutionTracer


class TestTDDWorkflowE2E:
    """End-to-end tests for the complete TDD workflow"""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Mock all external dependencies"""
        with patch('orchestrator.orchestrator_agent.run_team_member_with_tracking') as mock_run_team, \
             patch('agents.feature_reviewer.feature_reviewer_agent.feature_reviewer_agent') as mock_reviewer:
            
            # Configure mock responses
            mock_run_team.side_effect = self._mock_team_member_responses
            
            yield {
                'run_team_member': mock_run_team,
                'reviewer_agent': mock_reviewer
            }
    
    def _mock_team_member_responses(self, agent_name: str, *args, **kwargs):
        """Mock responses for different team members"""
        if agent_name == "planner_agent":
            return [Mock(parts=[Mock(content="Create a calculator with add and subtract functions")])]
        elif agent_name == "designer_agent":
            return [Mock(parts=[Mock(content="""
## Design for Calculator

### Features:
1. Add function - adds two numbers
2. Subtract function - subtracts second number from first

### Test Criteria:
- Input: Two numbers
- Output: Result of operation
- Edge cases: Zero, negative numbers
""")])]
        elif agent_name == "feature_reviewer_agent":
            # Always approve for simplicity
            return Mock(approved=True, feedback="Looks good", must_fix=[], suggestions=[])
        return [Mock(parts=[Mock(content="Generic response")])]
    
    def _mock_tdd_team_member_responses(self, agent_name: str, context: str, *args, **kwargs):
        """Mock responses for TDD-specific team members"""
        if agent_name == "test_writer_agent":
            return [Mock(parts=[Mock(content="""
```python
# filename: tests/test_calculator.py
import pytest
from calculator import add, subtract

def test_add():
    # This will fail initially - no implementation
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
    assert add(0, 0) == 0

def test_subtract():
    # This will fail initially - no implementation
    assert subtract(5, 3) == 2
    assert subtract(0, 5) == -5
    assert subtract(-2, -3) == 1
```
""")])]
        elif agent_name == "feature_coder_agent":
            if "RED phase" in context or "failing tests" in context:
                # Implementation to make tests pass
                return [Mock(parts=[Mock(content="""
```python
# filename: calculator.py
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b
```
""")])]
        return [Mock(parts=[Mock(content="Generic TDD response")])]
    
    @pytest.mark.asyncio
    async def test_complete_tdd_cycle(self, mock_dependencies):
        """Test a complete TDD cycle from requirements to GREEN phase"""
        # Arrange
        input_data = CodingTeamInput(
            requirements="Create a simple calculator with add and subtract functions"
        )
        tracer = WorkflowExecutionTracer("test_tdd_e2e")
        
        # Mock validator responses for RED phase (tests must fail)
        with patch('workflows.mvp_incremental.red_phase.RedPhaseOrchestrator.enforce_red_phase') as mock_red_phase:
            mock_red_phase.return_value = {
                'feature_id': 'feature_1',
                'phase': 'RED',
                'tests_failed': True,
                'failure_summary': {
                    'total_failures': 6,
                    'failure_types': ['ImportError', 'NameError']
                },
                'detailed_failures': [
                    {'test_name': 'test_add', 'failure_type': 'ImportError', 'failure_message': 'No module named calculator'},
                    {'test_name': 'test_subtract', 'failure_type': 'ImportError', 'failure_message': 'No module named calculator'}
                ],
                'missing_components': ['calculator module', 'add function', 'subtract function'],
                'implementation_hints': ['Create calculator.py with add and subtract functions']
            }
            
            # Mock test execution results (passing after implementation)
            with patch('workflows.mvp_incremental.tdd_feature_implementer.TestExecutor.execute_tests') as mock_test_exec:
                # First call: RED phase - tests fail
                # Second call: After implementation - tests pass
                mock_test_exec.side_effect = [
                    Mock(success=False, passed=0, failed=6, errors=['ImportError: No module named calculator'], 
                         output="Tests failed as expected", test_files=['tests/test_calculator.py'], expected_failure=True),
                    Mock(success=True, passed=6, failed=0, errors=[], 
                         output="All tests passed", test_files=['tests/test_calculator.py'], expected_failure=False)
                ]
                
                # Mock review integration
                with patch('workflows.mvp_incremental.review_integration.ReviewIntegration.request_review') as mock_review:
                    mock_review.return_value = Mock(approved=True, feedback="Good implementation", 
                                                  must_fix=[], suggestions=[])
                    
                    # Act
                    results = await execute_mvp_incremental_workflow(input_data, tracer)
        
        # Assert
        assert len(results) > 0
        
        # Check that we have planning and design results
        planner_results = [r for r in results if r.name == "planner"]
        assert len(planner_results) == 1
        assert "calculator" in planner_results[0].output.lower()
        
        designer_results = [r for r in results if r.name == "designer"]
        assert len(designer_results) == 1
        assert "add function" in designer_results[0].output.lower()
        
        # Check TDD feature results
        tdd_results = [r for r in results if r.name.startswith("tdd_feature_")]
        assert len(tdd_results) >= 1
        
        # Verify TDD metadata
        for result in tdd_results:
            if hasattr(result, 'metadata') and result.metadata:
                # Should have TDD phase information
                assert 'tdd_phase' in result.metadata
                assert 'test_results' in result.metadata
                
                # Initial tests should have failed (RED phase)
                initial_results = result.metadata['test_results']['initial']
                assert initial_results['expected_failure'] == True
                assert initial_results['failed'] > 0
                
                # Final tests should pass (moving toward GREEN)
                final_results = result.metadata['test_results']['final']
                assert final_results['success'] == True
    
    @pytest.mark.asyncio
    async def test_tdd_enforces_red_phase(self, mock_dependencies):
        """Test that TDD workflow enforces RED phase - tests must fail first"""
        input_data = CodingTeamInput(requirements="Create a function to reverse a string")
        
        # Mock RED phase to simulate tests that accidentally pass
        with patch('workflows.mvp_incremental.red_phase.RedPhaseOrchestrator.enforce_red_phase') as mock_red_phase:
            # Simulate RED phase validation failure (tests didn't fail)
            mock_red_phase.side_effect = Exception("RED phase validation failed: Tests must fail initially but 2 tests passed")
            
            # Act & Assert
            with pytest.raises(Exception) as exc_info:
                await execute_mvp_incremental_workflow(input_data)
            
            assert "RED phase validation failed" in str(exc_info.value)
            assert "Tests must fail initially" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_multi_feature_tdd_flow(self, mock_dependencies):
        """Test TDD workflow with multiple features"""
        # Update designer mock to return multiple features
        def multi_feature_designer(*args, **kwargs):
            if args[0] == "designer_agent":
                return [Mock(parts=[Mock(content="""
## Design for String Utilities

### Features:
1. Reverse string function - reverses input string
2. Capitalize words function - capitalizes first letter of each word
3. Count vowels function - counts vowels in string

### Test Criteria for each:
- Input validation
- Edge cases (empty, null)
- Expected outputs
""")])]
            return mock_dependencies['run_team_member'].side_effect(*args, **kwargs)
        
        mock_dependencies['run_team_member'].side_effect = multi_feature_designer
        
        input_data = CodingTeamInput(requirements="Create string utility functions")
        
        # Mock multiple RED phase validations
        red_phase_results = [
            {
                'feature_id': 'feature_1',
                'phase': 'RED',
                'tests_failed': True,
                'failure_summary': {'total_failures': 3, 'failure_types': ['ImportError']},
                'detailed_failures': [{'test_name': 'test_reverse', 'failure_type': 'ImportError', 
                                     'failure_message': 'No module named string_utils'}],
                'missing_components': ['reverse_string function'],
                'implementation_hints': ['Create reverse_string function']
            },
            {
                'feature_id': 'feature_2',
                'phase': 'RED',
                'tests_failed': True,
                'failure_summary': {'total_failures': 3, 'failure_types': ['ImportError']},
                'detailed_failures': [{'test_name': 'test_capitalize', 'failure_type': 'ImportError',
                                     'failure_message': 'No module named string_utils'}],
                'missing_components': ['capitalize_words function'],
                'implementation_hints': ['Create capitalize_words function']
            },
            {
                'feature_id': 'feature_3',
                'phase': 'RED',
                'tests_failed': True,
                'failure_summary': {'total_failures': 3, 'failure_types': ['ImportError']},
                'detailed_failures': [{'test_name': 'test_vowels', 'failure_type': 'ImportError',
                                     'failure_message': 'No module named string_utils'}],
                'missing_components': ['count_vowels function'],
                'implementation_hints': ['Create count_vowels function']
            }
        ]
        
        with patch('workflows.mvp_incremental.red_phase.RedPhaseOrchestrator.enforce_red_phase') as mock_red:
            mock_red.side_effect = red_phase_results
            
            with patch('workflows.mvp_incremental.tdd_feature_implementer.TestExecutor.execute_tests') as mock_test:
                # Each feature: fails then passes
                mock_test.side_effect = [
                    # Feature 1
                    Mock(success=False, passed=0, failed=3, expected_failure=True),
                    Mock(success=True, passed=3, failed=0, expected_failure=False),
                    # Feature 2
                    Mock(success=False, passed=0, failed=3, expected_failure=True),
                    Mock(success=True, passed=3, failed=0, expected_failure=False),
                    # Feature 3
                    Mock(success=False, passed=0, failed=3, expected_failure=True),
                    Mock(success=True, passed=3, failed=0, expected_failure=False)
                ]
                
                with patch('workflows.mvp_incremental.review_integration.ReviewIntegration.request_review') as mock_review:
                    mock_review.return_value = Mock(approved=True, feedback="Good", must_fix=[], suggestions=[])
                    
                    # Act
                    results = await execute_mvp_incremental_workflow(input_data)
        
        # Assert
        tdd_results = [r for r in results if r.name.startswith("tdd_feature_")]
        assert len(tdd_results) >= 3  # Should have results for 3 features
        
        # Each feature should have gone through TDD
        for result in tdd_results:
            if hasattr(result, 'metadata') and result.metadata:
                assert result.metadata['test_results']['initial']['expected_failure'] == True
                assert result.metadata['test_results']['final']['success'] == True
    
    @pytest.mark.asyncio
    async def test_tdd_retry_on_test_failure(self, mock_dependencies):
        """Test that TDD workflow retries implementation when tests fail"""
        input_data = CodingTeamInput(requirements="Create a factorial function")
        
        # Mock test writer to create comprehensive tests
        def mock_test_writer_response(*args, **kwargs):
            if args[0] == "test_writer_agent":
                return [Mock(parts=[Mock(content="""
```python
# filename: tests/test_factorial.py
import pytest
from math_utils import factorial

def test_factorial_basic():
    assert factorial(5) == 120
    assert factorial(0) == 1
    assert factorial(1) == 1

def test_factorial_large():
    assert factorial(10) == 3628800

def test_factorial_negative():
    with pytest.raises(ValueError):
        factorial(-1)
```
""")])]
            return self._mock_tdd_team_member_responses(*args, **kwargs)
        
        mock_dependencies['run_team_member'].side_effect = mock_test_writer_response
        
        # Mock coder to fail first attempt (incomplete implementation)
        attempt_count = 0
        def mock_coder_response(agent_name, context, *args, **kwargs):
            nonlocal attempt_count
            if agent_name == "feature_coder_agent":
                attempt_count += 1
                if attempt_count == 1:
                    # First attempt - incomplete (doesn't handle edge cases)
                    return [Mock(parts=[Mock(content="""
```python
# filename: math_utils.py
def factorial(n):
    if n == 0:
        return 1
    result = 1
    for i in range(1, n + 1):
        result *= i
    return result
```
""")])]
                else:
                    # Second attempt - complete (handles negative numbers)
                    return [Mock(parts=[Mock(content="""
```python
# filename: math_utils.py
def factorial(n):
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    if n == 0:
        return 1
    result = 1
    for i in range(1, n + 1):
        result *= i
    return result
```
""")])]
            return mock_test_writer_response(agent_name, *args, **kwargs)
        
        mock_dependencies['run_team_member'].side_effect = mock_coder_response
        
        with patch('workflows.mvp_incremental.red_phase.RedPhaseOrchestrator.enforce_red_phase') as mock_red:
            mock_red.return_value = {
                'feature_id': 'feature_1',
                'phase': 'RED',
                'tests_failed': True,
                'failure_summary': {'total_failures': 5, 'failure_types': ['ImportError']},
                'detailed_failures': [],
                'missing_components': ['factorial function'],
                'implementation_hints': []
            }
            
            with patch('workflows.mvp_incremental.tdd_feature_implementer.TestExecutor.execute_tests') as mock_test:
                # First implementation attempt: negative test fails
                # Second implementation attempt: all tests pass
                mock_test.side_effect = [
                    Mock(success=False, passed=0, failed=5, expected_failure=True),  # RED phase
                    Mock(success=False, passed=4, failed=1, errors=['ValueError not raised'], expected_failure=False),  # First impl
                    Mock(success=True, passed=5, failed=0, expected_failure=False)  # Second impl
                ]
                
                with patch('workflows.mvp_incremental.review_integration.ReviewIntegration.request_review') as mock_review:
                    mock_review.return_value = Mock(approved=True, feedback="Good", must_fix=[], suggestions=[])
                    
                    # Act
                    results = await execute_mvp_incremental_workflow(input_data)
        
        # Assert
        tdd_results = [r for r in results if r.name.startswith("tdd_feature_")]
        assert len(tdd_results) >= 1
        
        # Should have retry information
        result = tdd_results[0]
        if hasattr(result, 'metadata') and result.metadata:
            assert result.metadata.get('retry_count', 0) > 0  # Should have retried
            assert result.metadata['test_results']['final']['success'] == True
    
    @pytest.mark.asyncio
    async def test_tdd_phase_transitions(self, mock_dependencies):
        """Test that features properly transition through RED→YELLOW→GREEN phases"""
        input_data = CodingTeamInput(requirements="Create a simple function")
        
        # Track phase transitions
        phase_transitions = []
        
        # Mock phase tracker to record transitions
        original_tracker = TDDPhaseTracker()
        original_transition = original_tracker.transition_to
        
        def track_transition(feature_id, phase, reason=""):
            phase_transitions.append((feature_id, phase))
            return original_transition(feature_id, phase, reason)
        
        with patch.object(TDDPhaseTracker, 'transition_to', side_effect=track_transition):
            with patch('workflows.mvp_incremental.red_phase.RedPhaseOrchestrator.enforce_red_phase') as mock_red:
                mock_red.return_value = {
                    'feature_id': 'feature_1',
                    'phase': 'RED',
                    'tests_failed': True,
                    'failure_summary': {'total_failures': 2, 'failure_types': ['ImportError']},
                    'detailed_failures': [],
                    'missing_components': [],
                    'implementation_hints': []
                }
                
                with patch('workflows.mvp_incremental.tdd_feature_implementer.TestExecutor.execute_tests') as mock_test:
                    mock_test.side_effect = [
                        Mock(success=False, passed=0, failed=2, expected_failure=True),
                        Mock(success=True, passed=2, failed=0, expected_failure=False)
                    ]
                    
                    with patch('workflows.mvp_incremental.yellow_phase.YellowPhaseOrchestrator.enter_yellow_phase') as mock_yellow:
                        mock_yellow.return_value = Mock(time_entered_yellow=Mock(), review_attempts=0)
                        
                        with patch('workflows.mvp_incremental.yellow_phase.YellowPhaseOrchestrator.handle_review_result') as mock_yellow_review:
                            mock_yellow_review.return_value = TDDPhase.GREEN.value
                            
                            with patch('workflows.mvp_incremental.green_phase.GreenPhaseOrchestrator.enter_green_phase') as mock_green:
                                mock_green.return_value = Mock()
                                
                                with patch('workflows.mvp_incremental.green_phase.GreenPhaseOrchestrator.complete_feature') as mock_complete:
                                    mock_complete.return_value = {"celebration_message": "Feature completed!"}
                                    
                                    with patch('workflows.mvp_incremental.review_integration.ReviewIntegration.request_review') as mock_review:
                                        mock_review.return_value = Mock(approved=True, feedback="Good", must_fix=[], suggestions=[])
                                        
                                        # Act
                                        await execute_mvp_incremental_workflow(input_data)
        
        # Assert - should see transitions through all phases
        # Note: exact transitions depend on implementation, but should include progression
        assert len(phase_transitions) > 0
        # Should start in RED (though this might be set during feature start)
        # Should transition to YELLOW when tests pass
        # Should transition to GREEN after review approval
    
    @pytest.mark.asyncio
    async def test_no_non_tdd_paths(self, mock_dependencies):
        """Verify that there are no non-TDD code paths in the workflow"""
        input_data = CodingTeamInput(requirements="Any requirement")
        
        # The workflow should ALWAYS use TDD - no way to bypass it
        # We'll check this by ensuring test_writer_agent is always called
        
        test_writer_called = False
        original_side_effect = mock_dependencies['run_team_member'].side_effect
        
        def track_test_writer(*args, **kwargs):
            nonlocal test_writer_called
            if args[0] == "test_writer_agent":
                test_writer_called = True
            return original_side_effect(*args, **kwargs)
        
        mock_dependencies['run_team_member'].side_effect = track_test_writer
        
        with patch('workflows.mvp_incremental.red_phase.RedPhaseOrchestrator.enforce_red_phase') as mock_red:
            mock_red.return_value = {
                'feature_id': 'feature_1',
                'phase': 'RED',
                'tests_failed': True,
                'failure_summary': {'total_failures': 1, 'failure_types': ['ImportError']},
                'detailed_failures': [],
                'missing_components': [],
                'implementation_hints': []
            }
            
            with patch('workflows.mvp_incremental.tdd_feature_implementer.TestExecutor.execute_tests') as mock_test:
                mock_test.side_effect = [
                    Mock(success=False, passed=0, failed=1, expected_failure=True),
                    Mock(success=True, passed=1, failed=0, expected_failure=False)
                ]
                
                with patch('workflows.mvp_incremental.review_integration.ReviewIntegration.request_review') as mock_review:
                    mock_review.return_value = Mock(approved=True, feedback="Good", must_fix=[], suggestions=[])
                    
                    # Act
                    await execute_mvp_incremental_workflow(input_data)
        
        # Assert
        assert test_writer_called, "Test writer must be called - TDD is mandatory!"
        
        # Also verify the old validation-based implementation is not used
        # The workflow should not be looking for "validation_passed" in metadata
        # It should be looking for TDD phases instead
        # This is implicitly tested by the successful execution with TDD mocks


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])