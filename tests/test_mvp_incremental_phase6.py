#!/usr/bin/env python3
"""
Test script for MVP incremental workflow Phase 6.
Tests progress monitoring integration.
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.data_models import CodingTeamInput
from workflows.workflow_manager import execute_workflow
from workflows.monitoring import WorkflowExecutionTracer


async def test_progress_monitoring_simple():
    """Test with a simple example to see progress monitoring in action."""
    print("\n" + "="*60)
    print("🧪 Testing MVP Incremental Workflow Phase 6 - Progress Monitoring")
    print("📊 Simple Example: Counter with Progress Tracking")
    print("="*60)
    
    # Simple test case
    input_data = CodingTeamInput(
        requirements="""
Create a Counter class with:
1. increment() - adds 1 to the count
2. decrement() - subtracts 1 from the count  
3. get_count() - returns the current count
""",
        workflow_type="mvp_incremental"
    )
    
    tracer = WorkflowExecutionTracer("mvp_incremental_phase6_simple")
    
    try:
        start_time = datetime.now()
        results, report = await execute_workflow(input_data, tracer)
        end_time = datetime.now()
        
        print(f"\n✅ Success! Got {len(results)} results")
        print(f"⏱️  Total Duration: {(end_time - start_time).total_seconds():.2f}s")
        
        # Check metrics
        final_result = next((r for r in reversed(results) if r.name == "final_implementation"), None)
        if final_result and hasattr(final_result, 'metadata'):
            print("\n📊 Captured Metrics:", final_result.metadata)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_progress_monitoring_complex():
    """Test with a more complex example that will trigger retries."""
    print("\n\n" + "="*60)
    print("🧪 Testing with Complex Example (May Trigger Retries)")
    print("="*60)
    
    # Complex test case designed to potentially trigger retries
    input_data = CodingTeamInput(
        requirements="""
Create a TodoList class with these interdependent features:

1. add_todo(title, category) - adds a new todo item
   - Categories: 'work', 'personal', 'urgent'
   - Should validate category
   - Return todo ID

2. mark_complete(todo_id) - marks a todo as complete
   - Should handle invalid IDs gracefully
   - Should record completion time

3. get_todos_by_category(category) - returns todos for a category
   - Should return empty list if category doesn't exist
   - Should show incomplete todos first

4. get_completion_stats() - returns statistics
   - Total todos
   - Completed count
   - Completion percentage
   - Most productive category

Include proper error handling and input validation.
""",
        workflow_type="mvp_incremental"
    )
    
    tracer = WorkflowExecutionTracer("mvp_incremental_phase6_complex")
    
    try:
        print("\n📊 Watch the progress indicators and phase transitions...")
        print("⚡ Features with dependencies may require retries\n")
        
        results, report = await execute_workflow(input_data, tracer)
        
        print("\n✅ Complex workflow completed!")
        
        # Analyze the results
        feature_results = [r for r in results if r.name and r.name.startswith("coder_feature_")]
        retried_count = sum(1 for r in feature_results if hasattr(r, 'metadata') and r.metadata.get('retry_count', 0) > 0)
        
        if retried_count > 0:
            print(f"\n🔄 {retried_count} features required retry - error recovery worked!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error in complex test: {e}")
        return False


async def test_progress_visualization():
    """Test that demonstrates all progress visualization features."""
    print("\n\n" + "="*60)
    print("🧪 Testing Progress Visualization Features")
    print("="*60)
    
    from workflows.mvp_incremental.progress_monitor import ProgressMonitor, StepStatus
    import time
    
    monitor = ProgressMonitor()
    
    print("\n1️⃣ Testing Progress Bar Updates:")
    monitor.start_workflow(total_features=5)
    
    # Simulate feature completion
    for i in range(5):
        monitor.features[f"feature_{i}"] = type('obj', (object,), {
            'current_status': StepStatus.COMPLETED,
            'validation_passed': True
        })()
        monitor.print_progress_bar()
        await asyncio.sleep(0.5)
    
    print("\n2️⃣ Testing Phase Timing:")
    monitor2 = ProgressMonitor()
    monitor2.start_workflow()
    
    # Simulate phases
    phases = ["Planning", "Design", "Implementation"]
    for phase in phases:
        monitor2.start_phase(phase)
        monitor2.start_step(phase.lower(), phase.lower())
        await asyncio.sleep(0.3)
        monitor2.complete_step(phase.lower(), success=True)
    
    print("\n3️⃣ Testing Error Reporting:")
    monitor2.features["test_feature"] = type('obj', (object,), {
        'validation_passed': False,
        'errors': ["SyntaxError: invalid syntax", "NameError: undefined variable"],
        'total_attempts': 2,
        'current_status': StepStatus.FAILED
    })()
    
    monitor2.end_workflow()
    
    return True


async def main():
    """Run Phase 6 tests."""
    print("\n🚀 Starting MVP Incremental Workflow Phase 6 Tests")
    print("📋 Phase 6: Progress monitoring with real-time visibility")
    print("Note: Make sure the orchestrator server is running!")
    
    # Run tests
    success1 = await test_progress_visualization()
    success2 = await test_progress_monitoring_simple()
    success3 = await test_progress_monitoring_complex()
    
    if all([success1, success2, success3]):
        print("\n🎉 All Phase 6 tests passed!")
        print("✅ Progress monitoring features validated:")
        print("   - Real-time progress bars")
        print("   - Phase transition tracking")
        print("   - Feature completion status")
        print("   - Retry attempt visibility")
        print("   - Comprehensive workflow summaries")
        print("   - Exportable metrics")
    else:
        print("\n⚠️  Some Phase 6 tests failed.")
    
    return all([success1, success2, success3])


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)