#!/usr/bin/env python3
"""
Integration test for Phases 9 and 10 together in the MVP Incremental workflow
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.data_models import CodingTeamInput
from workflows.workflow_manager import execute_workflow


async def test_mvp_incremental_with_phases_9_10():
    """Test MVP incremental workflow with test execution and integration verification enabled."""
    print("=" * 60)
    print("Testing MVP Incremental Workflow with Phases 9 & 10")
    print("=" * 60)
    
    # Create input with phases 9 and 10 enabled
    input_data = CodingTeamInput(
        requirements="""
Create a simple Calculator class with the following methods:
1. add(a, b) - returns the sum of a and b
2. subtract(a, b) - returns a minus b
3. multiply(a, b) - returns a times b
4. divide(a, b) - returns a divided by b, raise ValueError if b is 0

Also create unit tests for each method.
""",
        workflow_type="mvp_incremental",
        run_tests=True,  # Enable Phase 9
        run_integration_verification=True  # Enable Phase 10
    )
    
    print("\n🚀 Starting workflow with:")
    print(f"   - Phase 9 (Test Execution): {input_data.run_tests}")
    print(f"   - Phase 10 (Integration Verification): {input_data.run_integration_verification}")
    print()
    
    try:
        # Execute the workflow
        results, report = await execute_workflow(input_data)
        
        print("\n✅ Workflow completed successfully!")
        
        # Check if test execution occurred
        if hasattr(report, 'metadata') and report.metadata:
            metrics = report.metadata
            print(f"\n📊 Workflow Metrics:")
            print(f"   Total features: {metrics.get('total_features', 'N/A')}")
            print(f"   Successful features: {metrics.get('successful_features', 'N/A')}")
            print(f"   Failed features: {metrics.get('failed_features', 'N/A')}")
            print(f"   Retried features: {metrics.get('retried_features', 'N/A')}")
            
            # Check for integration verification results
            if 'integration_verification' in metrics:
                iv_results = metrics['integration_verification']
                print(f"\n🔍 Integration Verification Results:")
                print(f"   Tests passed: {iv_results.get('tests_passed', 'N/A')}")
                print(f"   Build successful: {iv_results.get('build_successful', 'N/A')}")
                print(f"   Issues found: {iv_results.get('issues_count', 'N/A')}")
        
        # Check if completion report was generated
        from workflows.workflow_config import get_generated_code_path
        generated_path = Path(get_generated_code_path())
        completion_report = generated_path / "COMPLETION_REPORT.md"
        
        if completion_report.exists():
            print(f"\n📄 Completion report generated at: {completion_report}")
            # Show first few lines
            lines = completion_report.read_text().split('\n')[:10]
            print("\n--- Report Preview ---")
            for line in lines:
                print(line)
            print("...")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Workflow failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_phases_disabled():
    """Test that phases 9 and 10 don't run when disabled."""
    print("\n" + "=" * 60)
    print("Testing MVP Incremental Workflow with Phases 9 & 10 DISABLED")
    print("=" * 60)
    
    input_data = CodingTeamInput(
        requirements="Create a simple Hello World function",
        workflow_type="mvp_incremental",
        run_tests=False,  # Disable Phase 9
        run_integration_verification=False  # Disable Phase 10
    )
    
    print("\n🚀 Starting workflow with phases disabled")
    
    try:
        results, report = await execute_workflow(input_data)
        
        print("\n✅ Workflow completed")
        
        # Verify no integration verification occurred
        if hasattr(report, 'metadata') and report.metadata:
            assert 'integration_verification' not in report.metadata, \
                "Integration verification should not run when disabled"
            print("   ✓ Confirmed: Phase 10 did not run")
        
        # Check no completion report was generated
        from workflows.workflow_config import get_generated_code_path
        generated_path = Path(get_generated_code_path())
        completion_report = generated_path / "COMPLETION_REPORT.md"
        
        if not completion_report.exists():
            print("   ✓ Confirmed: No completion report generated")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Workflow failed: {e}")
        return False


async def main():
    """Run all integration tests."""
    print("MVP Incremental Workflow - Phases 9 & 10 Integration Test")
    print("=" * 60)
    
    # Note: This test requires the orchestrator to be running
    print("\n⚠️  Note: This test requires the orchestrator server to be running")
    print("   Start it with: python orchestrator/orchestrator_agent.py")
    print()
    
    success = True
    
    # Test with phases enabled
    if not await test_mvp_incremental_with_phases_9_10():
        success = False
    
    # Test with phases disabled
    if not await test_phases_disabled():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("✅ All integration tests passed!")
    else:
        print("❌ Some tests failed")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())