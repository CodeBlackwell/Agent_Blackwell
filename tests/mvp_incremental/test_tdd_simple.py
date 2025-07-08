#!/usr/bin/env python3
"""
Simple test script for TDD workflow components
Tests individual components without full workflow execution
"""

import asyncio
import sys
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from workflows.mvp_incremental.test_accumulator import TestAccumulator
from workflows.mvp_incremental.progress_monitor import ProgressMonitor, StepStatus
from workflows.mvp_incremental.tdd_phase_tracker import TDDPhase


def test_test_accumulator():
    """Test the test accumulator component"""
    print("\n=== Testing Test Accumulator ===")
    
    accumulator = TestAccumulator()
    
    # Add tests for feature 1
    test_code_1 = '''```python
# filename: tests/test_calculator.py
import pytest
from calculator import add, subtract

def test_add():
    assert add(2, 3) == 5
    
def test_subtract():
    assert subtract(5, 3) == 2
```'''
    
    files_1 = accumulator.add_feature_tests("feature_1", test_code_1)
    print(f"✅ Added {len(files_1)} test files for feature 1")
    print(f"   - {files_1[0].filename}: {len(files_1[0].test_functions)} tests")
    
    # Add tests for feature 2
    test_code_2 = '''```python
# filename: tests/test_calculator_advanced.py
import pytest
from calculator import multiply, divide

def test_multiply():
    assert multiply(3, 4) == 12
    
def test_divide():
    assert divide(10, 2) == 5
    
def test_divide_by_zero():
    with pytest.raises(ValueError):
        divide(10, 0)
```'''
    
    files_2 = accumulator.add_feature_tests("feature_2", test_code_2, ["feature_1"])
    print(f"✅ Added {len(files_2)} test files for feature 2")
    
    # Get test command
    test_cmd = accumulator.get_test_command()
    print(f"\n📋 Test command: {test_cmd}")
    
    # Generate report
    report = accumulator.generate_test_report()
    print("\n📊 Test Report Preview:")
    print(report[:300] + "...")
    
    return True


def test_progress_monitor_tdd():
    """Test progress monitor with TDD states"""
    print("\n=== Testing Progress Monitor TDD States ===")
    
    monitor = ProgressMonitor()
    monitor.start_workflow(total_features=2)
    
    # Feature 1: Add function
    print("\n🎯 Feature 1: Add function")
    monitor.start_feature("feature_1", "Add function", 1)
    
    # TDD cycle
    monitor.update_step("feature_feature_1", StepStatus.WRITING_TESTS)
    monitor.update_tdd_progress("feature_1", "tests_written", {
        "test_files": 1,
        "test_functions": 2
    })
    
    monitor.update_step("feature_feature_1", StepStatus.TESTS_FAILING)
    monitor.update_tdd_progress("feature_1", "tests_initial_run", {
        "passed": 0,
        "failed": 2
    })
    
    monitor.update_step("feature_feature_1", StepStatus.IMPLEMENTING)
    
    monitor.update_step("feature_feature_1", StepStatus.TESTS_PASSING)
    monitor.update_tdd_progress("feature_1", "tests_passing", {
        "coverage": 100.0
    })
    
    monitor.complete_feature("feature_1", True)
    
    # Feature 2: Subtract function
    print("\n🎯 Feature 2: Subtract function")
    monitor.start_feature("feature_2", "Subtract function", 2)
    
    monitor.update_step("feature_feature_2", StepStatus.WRITING_TESTS)
    monitor.update_tdd_progress("feature_2", "tests_written", {
        "test_files": 1,
        "test_functions": 3
    })
    
    monitor.update_step("feature_feature_2", StepStatus.TESTS_FAILING)
    monitor.update_step("feature_feature_2", StepStatus.IMPLEMENTING)
    monitor.update_step("feature_feature_2", StepStatus.TESTS_PASSING)
    monitor.update_tdd_progress("feature_2", "tests_passing", {
        "coverage": 95.5
    })
    
    monitor.complete_feature("feature_2", True)
    
    # Show progress
    monitor.print_progress_bar()
    
    # End workflow
    monitor.end_workflow()
    
    # Export metrics
    metrics = monitor.export_metrics()
    print("\n📊 TDD Metrics:")
    tdd_metrics = metrics.get("tdd_metrics", {})
    for key, value in tdd_metrics.items():
        print(f"   - {key}: {value}")
    
    return True


def test_tdd_phase_tracking():
    """Test TDD phase enum and tracking"""
    print("\n=== Testing TDD Phase Tracking ===")
    
    phases = list(TDDPhase)
    print(f"TDD Phases: {[p.value for p in phases]}")
    
    # Test RED-YELLOW-GREEN cycle
    from workflows.mvp_incremental.tdd_phase_tracker import TDDPhaseTracker
    
    tracker = TDDPhaseTracker()
    feature_id = "test_feature_1"
    
    # Start in RED phase
    tracker.start_feature(feature_id)
    current_phase = tracker.get_current_phase(feature_id)
    print(f"\n{tracker.get_visual_status(feature_id)}")
    assert current_phase == TDDPhase.RED
    
    # Transition to YELLOW
    tracker.transition_to(feature_id, TDDPhase.YELLOW, "Tests passing")
    print(f"{tracker.get_visual_status(feature_id)}")
    assert tracker.get_current_phase(feature_id) == TDDPhase.YELLOW
    
    # Transition to GREEN
    tracker.transition_to(feature_id, TDDPhase.GREEN, "Code reviewed")
    print(f"{tracker.get_visual_status(feature_id)}")
    assert tracker.get_current_phase(feature_id) == TDDPhase.GREEN
    
    print("\n✅ RED-YELLOW-GREEN cycle completed")
    
    # Show summary
    print("\nPhase Tracker Summary:")
    print(tracker.get_summary_report())
    
    return True


@pytest.mark.asyncio
async def test_workflow_integration():
    """Test basic workflow integration"""
    print("\n=== Testing Basic Workflow Integration ===")
    
    # This would test actual workflow execution
    # For now, just verify imports work
    try:
        from workflows.mvp_incremental.mvp_incremental_tdd import execute_mvp_incremental_tdd_workflow
        from shared.data_models import CodingTeamInput
        
        print("✅ Workflow imports successful")
        
        # Create test input
        test_input = CodingTeamInput(
            requirements="Test requirement",
            workflow_type="mvp_incremental_tdd"
        )
        
        print(f"✅ Created test input with workflow_type={test_input.workflow_type}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run all tests"""
    print("🧪 Testing TDD Workflow Components")
    print("=" * 50)
    
    # Run synchronous tests
    tests = [
        test_test_accumulator,
        test_progress_monitor_tdd,
        test_tdd_phase_tracking
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed: {e}")
            results.append(False)
    
    # Run async test
    try:
        async_result = asyncio.run(test_workflow_integration())
        results.append(async_result)
    except Exception as e:
        print(f"❌ Async test failed: {e}")
        results.append(False)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    passed = sum(1 for r in results if r)
    print(f"   Passed: {passed}/{len(results)}")
    
    if passed == len(results):
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())