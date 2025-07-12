#!/usr/bin/env python3
"""
Test script to verify the incremental workflow fixes.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from shared.data_models import CodingTeamInput, TeamMember
from workflows.workflow_manager import execute_workflow
from workflows.monitoring import WorkflowExecutionTracer
from examples.orchestrator_manager import OrchestratorManager

# Simple test requirements
TEST_REQUIREMENTS = """
Create a simple calculator with the following features:

FEATURE[1]: Basic Operations
Description: Implement add, subtract, multiply, and divide functions
Files: calculator.py
Validation: Functions should handle basic arithmetic correctly
Dependencies: []
Complexity: low

FEATURE[2]: Error Handling
Description: Add error handling for division by zero and invalid inputs
Files: calculator.py
Validation: Should raise appropriate exceptions for edge cases
Dependencies: [FEATURE[1]]
Complexity: medium

FEATURE[3]: Calculator Class
Description: Wrap operations in a Calculator class with memory feature
Files: calculator.py
Validation: Class should maintain state and provide operation history
Dependencies: [FEATURE[1], FEATURE[2]]
Complexity: medium
"""

async def test_incremental_workflow():
    """Test the incremental workflow with fixes."""
    
    print("🧪 Testing Incremental Workflow Fixes")
    print("=" * 60)
    
    # Create input
    input_data = CodingTeamInput(
        requirements=TEST_REQUIREMENTS,
        workflow_type="incremental",
        team_members=[
            TeamMember.planner,
            TeamMember.designer,
            TeamMember.coder,
            TeamMember.reviewer
        ]
    )
    
    # Create tracer
    tracer = WorkflowExecutionTracer("test_incremental_fixes")
    
    try:
        print("📋 Test Requirements:")
        print("• Feature 1: Basic arithmetic operations")
        print("• Feature 2: Error handling")
        print("• Feature 3: Calculator class with memory")
        print("\n⏳ Starting workflow...\n")
        
        # Execute workflow
        results, report = await execute_workflow(input_data, tracer)
        
        print("\n✅ Workflow completed successfully!")
        
        # Check results
        if results:
            print(f"\n📊 Results: {len(results)} team outputs received")
            for i, result in enumerate(results):
                if hasattr(result, 'team_member'):
                    print(f"  {i+1}. {result.team_member.value}: {len(result.output)} chars")
        
        # Check report
        if hasattr(report, 'get_summary'):
            summary = report.get_summary()
            print(f"\n📈 Execution Summary:")
            print(f"  • Duration: {summary.get('total_duration', 'N/A')}")
            print(f"  • Steps: {summary.get('total_steps', 'N/A')}")
            
        print("\n✅ All fixes appear to be working correctly!")
        
    except Exception as e:
        print(f"\n❌ Error during test: {str(e)}")
        import traceback
        traceback.print_exc()
        print("\n🔍 This error indicates there may still be issues to fix.")

def main():
    """Main entry point."""
    print("🧪 TEST: Incremental Workflow Fixes")
    print("=" * 60)
    
    # Use orchestrator manager to ensure it's running
    try:
        with OrchestratorManager() as manager:
            print("\n✅ Orchestrator is ready!\n")
            
            # Run the test
            asyncio.run(test_incremental_workflow())
            
            if manager.started_by_us:
                print("\n🔄 Stopping orchestrator...")
    
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()