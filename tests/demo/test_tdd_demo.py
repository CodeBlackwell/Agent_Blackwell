#!/usr/bin/env python3
"""
Quick test script to verify TDD workflow integration
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.data_models import CodingTeamInput
from workflows.workflow_manager import execute_workflow, get_workflow_description
from workflows.monitoring import WorkflowExecutionTracer


async def test_tdd_workflow():
    """Test the TDD workflow with a simple example"""
    print("🧪 Testing MVP Incremental TDD Workflow")
    print("=" * 60)
    
    # Show available workflows
    print("\n📋 Checking TDD workflow registration...")
    desc = get_workflow_description("mvp_incremental_tdd")
    print(f"✅ Found: {desc}")
    
    # Create test input
    print("\n📝 Creating test input...")
    test_input = CodingTeamInput(
        requirements="""Create a simple math utilities module with:
1. Function to check if a number is prime
2. Function to calculate factorial
3. Proper error handling for invalid inputs""",
        workflow_type="mvp_incremental_tdd",
        run_tests=True  # Enable test execution
    )
    print("✅ Input created")
    
    # Create tracer
    tracer = WorkflowExecutionTracer("test_tdd_demo")
    
    print("\n🚀 Starting TDD workflow...")
    print("This will:")
    print("  1. Plan the project")
    print("  2. Design the architecture")
    print("  3. For each feature:")
    print("     - Write tests first")
    print("     - Run tests (expect failure)")
    print("     - Implement code")
    print("     - Run tests (expect success)")
    
    try:
        # Execute workflow
        results, report = await execute_workflow(test_input, tracer)
        
        print(f"\n✅ Workflow completed successfully!")
        print(f"📊 Results: {len(results)} team member outputs")
        
        # Check for test writer outputs
        test_results = [r for r in results if r.name.startswith("test_writer")]
        impl_results = [r for r in results if r.name.startswith("coder_feature")]
        
        print(f"\n📋 TDD Metrics:")
        print(f"  - Test writer outputs: {len(test_results)}")
        print(f"  - Implementation outputs: {len(impl_results)}")
        
        # Show some test content
        if test_results:
            print(f"\n📝 Sample test output (first 200 chars):")
            print(test_results[0].output[:200] + "...")
            
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_workflow_selection():
    """Test that workflow selection works correctly"""
    print("\n🔍 Testing workflow type selection...")
    
    test_cases = [
        ("mvp_incremental", "Standard MVP incremental"),
        ("mvp_incremental_tdd", "TDD version"),
        ("mvp_tdd", "Alias for TDD"),
    ]
    
    for workflow_type, description in test_cases:
        print(f"\n  Testing {workflow_type} ({description})...")
        try:
            test_input = CodingTeamInput(
                requirements="Test",
                workflow_type=workflow_type
            )
            print(f"  ✅ {workflow_type} accepted")
        except Exception as e:
            print(f"  ❌ {workflow_type} failed: {e}")


def main():
    """Run all tests"""
    print("🧪 TDD Workflow Integration Test")
    print("=" * 60)
    
    # Test workflow selection
    asyncio.run(test_workflow_selection())
    
    # Ask if user wants to run full test
    print("\n" + "=" * 60)
    choice = input("\n🤔 Run full TDD workflow test? This will execute agents (y/N): ").strip().lower()
    
    if choice == 'y':
        success = asyncio.run(test_tdd_workflow())
        
        if success:
            print("\n✅ All tests passed!")
            return 0
        else:
            print("\n❌ Some tests failed")
            return 1
    else:
        print("\n👍 Skipping full workflow test")
        return 0


if __name__ == "__main__":
    sys.exit(main())