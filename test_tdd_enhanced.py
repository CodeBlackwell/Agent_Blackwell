#!/usr/bin/env python3
"""
Test script for the enhanced TDD workflow
This demonstrates the proper red-green-refactor cycle
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from shared.data_models import CodingTeamInput, TeamMember
from workflows.tdd.tdd_workflow import execute_tdd_workflow
from workflows.workflow_config import init_workflow_config


async def test_tdd_workflow():
    """Test the enhanced TDD workflow with a simple calculator example"""
    
    # Initialize workflow configuration
    init_workflow_config()
    
    # Simple calculator requirements
    requirements = """
Create a Calculator class with the following methods:
1. add(a, b) - returns sum of a and b
2. subtract(a, b) - returns difference a - b
3. multiply(a, b) - returns product of a and b
4. divide(a, b) - returns quotient a / b, raises ValueError if b is 0

All methods should handle integers and floats.
"""
    
    # Create input
    input_data = CodingTeamInput(
        requirements=requirements,
        workflow_type="TDD",
        team_members=[
            TeamMember.planner,
            TeamMember.designer,
            TeamMember.test_writer,
            TeamMember.coder,
            TeamMember.reviewer
        ],
        max_retries=3,
        timeout_seconds=600
    )
    
    print("🚀 Starting Enhanced TDD Workflow Test")
    print("=" * 60)
    print("Requirements:")
    print(requirements)
    print("=" * 60)
    
    try:
        # Execute workflow
        results, report = await execute_tdd_workflow(input_data)
        
        print("\n✅ TDD Workflow completed successfully!")
        print(f"Total steps executed: {len(report.steps)}")
        
        # Show TDD cycle metrics if available
        tdd_step = next((s for s in report.steps if s.step_name == "tdd_cycle"), None)
        if tdd_step and tdd_step.output:
            print("\n📊 TDD Cycle Metrics:")
            output = tdd_step.output
            if isinstance(output, dict):
                print(f"  - Iterations: {output.get('iterations', 'N/A')}")
                print(f"  - Initial failures: {output.get('initial_failures', 'N/A')}")
                print(f"  - Final passes: {output.get('final_passes', 'N/A')}")
                print(f"  - All tests passing: {output.get('all_tests_passing', 'N/A')}")
        
        # Show results summary
        print("\n📝 Agent Results:")
        for result in results:
            print(f"  - {result.name}: {len(result.output)} chars")
            
        # Show any errors
        if report.errors:
            print("\n⚠️  Errors encountered:")
            for error in report.errors:
                print(f"  - {error}")
                
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("Testing Enhanced TDD Workflow")
    print("This will demonstrate the red-green-refactor cycle")
    print("-" * 60)
    
    # Check if orchestrator is running
    print("\n⚠️  Note: Make sure the orchestrator is running:")
    print("  python orchestrator/orchestrator_agent.py")
    print("")
    
    asyncio.run(test_tdd_workflow())