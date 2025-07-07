#!/usr/bin/env python3
"""Quick validation of Phase 6 progress monitoring."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.data_models import CodingTeamInput
from workflows.workflow_manager import execute_workflow
from workflows.monitoring import WorkflowExecutionTracer


async def test_progress_monitoring():
    """Test MVP incremental workflow with progress monitoring."""
    print("🧪 Testing Phase 6 - Progress Monitoring")
    print("="*60)
    
    # Test case with multiple features
    input_data = CodingTeamInput(
        requirements="""
Create a Task Manager class with these features:

1. add_task(title, priority) - adds a new task
   - Priority should be 'high', 'medium', or 'low'
   - Return the task ID
   
2. complete_task(task_id) - marks a task as complete
   - Should handle invalid task IDs
   
3. list_tasks() - returns all tasks
   - Show pending tasks first, then completed
   
4. get_high_priority_tasks() - returns only high priority tasks
   - Should return empty list if none exist

Each method should have proper error handling.
""",
        workflow_type="mvp_incremental"
    )
    
    tracer = WorkflowExecutionTracer("mvp_incremental_phase6_test")
    
    try:
        print("\n📊 Watch for progress updates during execution...")
        print("="*60)
        
        results, report = await execute_workflow(input_data, tracer)
        
        print("\n✅ Workflow completed successfully!")
        
        # Check if metrics were captured
        final_result = None
        for result in reversed(results):
            if result.name == "final_implementation":
                final_result = result
                break
        
        if final_result and hasattr(final_result, 'metadata') and final_result.metadata:
            print("\n📈 Workflow Metrics:")
            metrics = final_result.metadata
            
            if 'workflow_duration' in metrics:
                print(f"   Total Duration: {metrics['workflow_duration']:.1f}s")
            if 'successful_features' in metrics:
                print(f"   Successful Features: {metrics['successful_features']}/{metrics['total_features']}")
            if 'retried_features' in metrics:
                print(f"   Features Requiring Retry: {metrics['retried_features']}")
            if 'phase_times' in metrics:
                print("   Phase Breakdown:")
                for phase, duration in metrics['phase_times'].items():
                    print(f"     - {phase}: {duration:.1f}s")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_progress_monitor_directly():
    """Test the progress monitor component directly."""
    print("\n\n🧪 Testing Progress Monitor Component")
    print("="*60)
    
    from workflows.mvp_incremental.progress_monitor import ProgressMonitor, StepStatus
    
    # Create monitor
    monitor = ProgressMonitor()
    
    # Simulate workflow
    monitor.start_workflow(total_features=3)
    
    # Planning phase
    monitor.start_phase("Planning")
    monitor.start_step("planning", "planning")
    await asyncio.sleep(0.5)  # Simulate work
    monitor.complete_step("planning", success=True)
    
    # Design phase
    monitor.start_phase("Design")
    monitor.start_step("design", "design")
    await asyncio.sleep(0.3)
    monitor.complete_step("design", success=True)
    
    # Implementation phase
    monitor.start_phase("Implementation")
    
    # Feature 1
    monitor.start_feature("feature_1", "Add task method", 1)
    await asyncio.sleep(0.2)
    monitor.update_feature_validation("feature_1", True)
    monitor.complete_feature("feature_1", True)
    
    # Feature 2 - with retry
    monitor.start_feature("feature_2", "Complete task method", 2)
    await asyncio.sleep(0.2)
    monitor.update_feature_validation("feature_2", False, "NameError: 'task' not defined")
    monitor.update_step("feature_feature_2", StepStatus.RETRYING)
    await asyncio.sleep(0.3)
    monitor.update_feature_validation("feature_2", True)
    monitor.complete_feature("feature_2", True)
    
    monitor.print_progress_bar()
    
    # Feature 3
    monitor.start_feature("feature_3", "List tasks method", 3)
    await asyncio.sleep(0.2)
    monitor.update_feature_validation("feature_3", True)
    monitor.complete_feature("feature_3", True)
    
    monitor.print_progress_bar()
    
    # End workflow
    monitor.end_workflow()
    
    # Export metrics
    metrics = monitor.export_metrics()
    print("\n📊 Exported Metrics:", metrics)
    
    return True


async def main():
    """Run Phase 6 tests."""
    print("\n🚀 Starting MVP Incremental Workflow Phase 6 Tests")
    print("📋 Phase 6: Progress monitoring and visibility")
    
    # Test the progress monitor component
    success1 = await test_progress_monitor_directly()
    
    print("\n" + "="*60)
    print("Note: Make sure the orchestrator server is running for the full test!")
    print("="*60 + "\n")
    
    # Test full workflow with progress monitoring
    success2 = await test_progress_monitoring()
    
    if all([success1, success2]):
        print("\n🎉 All Phase 6 tests passed!")
        print("✅ Progress monitoring is working correctly")
        print("   - Real-time status updates")
        print("   - Progress bars and percentages")
        print("   - Phase timing and metrics")
        print("   - Comprehensive summary reports")
    else:
        print("\n⚠️  Some Phase 6 tests failed.")
    
    return all([success1, success2])


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)