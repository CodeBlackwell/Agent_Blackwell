#!/usr/bin/env python3
"""
Demo script for Enhanced TDD Workflow
Shows the proper red-green-refactor cycle in action
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from shared.data_models import CodingTeamInput, TeamMember
from workflows.tdd import execute_enhanced_tdd_workflow
from workflows.monitoring import WorkflowExecutionTracer


async def main():
    """Run enhanced TDD workflow demo"""
    
    print("🚀 Enhanced TDD Workflow Demo")
    print("=" * 60)
    
    # Simple calculator example that demonstrates TDD
    requirements = """
Create a Calculator class with the following methods:
1. add(a, b) - returns sum of two numbers
2. subtract(a, b) - returns difference (a - b)
3. multiply(a, b) - returns product
4. divide(a, b) - returns quotient, raises ValueError for division by zero

Use proper Test-Driven Development:
- Write tests first that define the expected behavior
- Tests should fail initially (RED phase)
- Implement code to make tests pass (GREEN phase)
- Refactor if needed while keeping tests green
"""
    
    # Create input
    input_data = CodingTeamInput(
        requirements=requirements,
        workflow_type="enhanced_tdd",
        team_members=[
            TeamMember.planner,
            TeamMember.designer,
            TeamMember.test_writer,
            TeamMember.coder,
            TeamMember.reviewer
        ],
        max_retries=3,
        timeout_seconds=300
    )
    
    # Create tracer
    tracer = WorkflowExecutionTracer(
        workflow_type="enhanced_tdd",
        execution_id="tdd_demo_001"
    )
    
    try:
        print("\n📋 Requirements:")
        print(requirements)
        print("\n" + "=" * 60)
        
        # Execute workflow
        results, report = await execute_enhanced_tdd_workflow(input_data, tracer)
        
        print("\n✅ Workflow completed!")
        print(f"Total steps: {len(results)}")
        
        # Show TDD metrics
        tdd_results = [r for r in results if hasattr(r, 'metadata') and r.metadata and r.metadata.get('tdd_cycle')]
        if tdd_results:
            print("\n📊 TDD Metrics:")
            for r in tdd_results:
                print(f"  - Component: {r.name}")
                print(f"    Iterations: {r.metadata.get('iterations', 'N/A')}")
                print(f"    Tests Passing: {r.metadata.get('tests_passing', 'N/A')}")
        
        # Show final implementation
        final_impl = next((r for r in results if r.name == "final_tdd_implementation"), None)
        if final_impl:
            print("\n📦 Final Implementation Preview:")
            print("-" * 40)
            print(final_impl.output[:1000] + "..." if len(final_impl.output) > 1000 else final_impl.output)
        
        # Show execution report
        print("\n📈 Execution Report:")
        print(f"  Workflow: {report.workflow_type}")
        print(f"  Status: {report.status}")
        print(f"  Duration: {report.duration_seconds:.2f}s")
        print(f"  Total Steps: {report.total_steps}")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("Starting Enhanced TDD Demo...")
    print("Note: This demo shows proper test-first development")
    print("Tests are written before code and must fail initially")
    print()
    
    asyncio.run(main())