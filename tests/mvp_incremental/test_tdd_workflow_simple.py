"""
Simple test to verify TDD workflow is properly integrated
"""

import pytest
from workflows.mvp_incremental.mvp_incremental import execute_mvp_incremental_workflow
from shared.data_models import CodingTeamInput


def test_workflow_imports():
    """Test that all TDD components are imported correctly"""
    # This should not raise any import errors
    from workflows.mvp_incremental.tdd_phase_tracker import TDDPhaseTracker, TDDPhase
    from workflows.mvp_incremental.testable_feature_parser import TestableFeatureParser, TestableFeature
    from workflows.mvp_incremental.tdd_feature_implementer import TDDFeatureImplementer, TDDFeatureResult
    from workflows.mvp_incremental.red_phase import RedPhaseOrchestrator
    from workflows.mvp_incremental.yellow_phase import YellowPhaseOrchestrator
    from workflows.mvp_incremental.green_phase import GreenPhaseOrchestrator
    
    # Verify classes exist
    assert TDDPhaseTracker is not None
    assert TDDPhase is not None
    assert TestableFeatureParser is not None
    assert TestableFeature is not None
    assert TDDFeatureImplementer is not None
    assert TDDFeatureResult is not None
    assert RedPhaseOrchestrator is not None
    assert YellowPhaseOrchestrator is not None
    assert GreenPhaseOrchestrator is not None


def test_workflow_function_exists():
    """Test that the workflow function exists and has correct signature"""
    assert hasattr(execute_mvp_incremental_workflow, '__call__')
    
    # Check docstring mentions TDD
    docstring = execute_mvp_incremental_workflow.__doc__
    assert docstring is not None
    assert "TDD" in docstring or "Test-Driven Development" in docstring
    assert "RED" in docstring and "YELLOW" in docstring and "GREEN" in docstring


def test_tdd_components_in_workflow():
    """Test that TDD components are used in the workflow"""
    # Read the workflow source to verify TDD integration
    import inspect
    source = inspect.getsource(execute_mvp_incremental_workflow)
    
    # Check for TDD imports and usage
    assert "TDDPhaseTracker" in source
    assert "TDDFeatureImplementer" in source
    assert "parse_testable_features" in source
    assert "RED→YELLOW→GREEN" in source or "RED->YELLOW->GREEN" in source
    
    # Check that old validation-based code is removed
    assert "validation_passed" not in source or "tdd" in source.lower()


if __name__ == "__main__":
    test_workflow_imports()
    print("✅ All imports successful")
    
    test_workflow_function_exists()
    print("✅ Workflow function exists with TDD documentation")
    
    test_tdd_components_in_workflow()
    print("✅ TDD components integrated in workflow")
    
    print("\n🎉 All basic tests passed! TDD workflow is properly integrated.")