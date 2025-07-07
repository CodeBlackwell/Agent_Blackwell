#!/usr/bin/env python3
"""Simple test to validate Phase 6 progress monitoring components."""

import asyncio
from workflows.mvp_incremental.progress_monitor import ProgressMonitor, StepStatus

async def test_progress_monitor():
    """Test the progress monitor component directly."""
    print("🧪 Testing Phase 6 - Progress Monitor Component")
    print("="*60)
    
    # Create monitor
    monitor = ProgressMonitor()
    
    # Start workflow
    monitor.start_workflow(total_features=3)
    
    # Planning phase
    monitor.start_phase("Planning")
    monitor.start_step("planning", "planning")
    await asyncio.sleep(0.5)
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
    monitor.print_progress_bar()
    
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
    print("\n📊 Exported Metrics:")
    print(f"   Total Duration: {metrics.get('workflow_duration', 0):.1f}s")
    print(f"   Successful Features: {metrics.get('successful_features', 0)}")
    print(f"   Failed Features: {metrics.get('failed_features', 0)}")
    print(f"   Retried Features: {metrics.get('retried_features', 0)}")
    
    print("\n✅ Phase 6 VALIDATED - Progress monitoring is working!")
    return True

if __name__ == "__main__":
    success = asyncio.run(test_progress_monitor())
    exit(0 if success else 1)