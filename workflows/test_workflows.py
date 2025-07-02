"""
Test script for the modular workflows.

This script tests that the refactored workflows system works correctly,
including TDD workflow, full workflow, and individual workflow steps.
"""
import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from orchestrator.orchestrator_agent import (
    TeamMember, WorkflowStep, CodingTeamInput, CodingTeamResult
)
from workflows import execute_workflow

# Test requirements
TEST_REQUIREMENTS = "Create a simple Express.js TODO API with the following endpoints: GET /todos, POST /todos, GET /todos/:id, PUT /todos/:id, DELETE /todos/:id"

async def test_tdd_workflow():
    """Test the TDD workflow execution"""
    print("\n🧪 Testing TDD workflow...")
    input_data = CodingTeamInput(
        requirements=TEST_REQUIREMENTS,
        workflow=WorkflowStep.tdd_workflow,
        team_members=[TeamMember.planner, TeamMember.designer]  # Limited for testing speed
    )
    
    try:
        results = await execute_workflow(input_data)
        print(f"✅ TDD workflow test completed with {len(results)} results")
        # Save result to file for inspection
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(project_root) / "tests" / "outputs"
        output_path.mkdir(exist_ok=True, parents=True)
        
        output_file = output_path / f"tdd_workflow_test_{timestamp}.txt"
        with open(output_file, "w") as f:
            for idx, result in enumerate(results):
                f.write(f"\n{idx+1}. {result.team_member.value.upper()} OUTPUT:\n")
                f.write("="*50 + "\n")
                f.write(result.output)
                f.write("\n" + "-"*50 + "\n")
        
        print(f"📝 Results saved to {output_file}")
        return True
    except Exception as e:
        print(f"❌ TDD workflow test failed: {e}")
        return False

async def test_full_workflow():
    """Test the full workflow execution"""
    print("\n🔄 Testing full workflow...")
    input_data = CodingTeamInput(
        requirements=TEST_REQUIREMENTS,
        workflow=WorkflowStep.full_workflow,
        team_members=[TeamMember.planner, TeamMember.designer]  # Limited for testing speed
    )
    
    try:
        results = await execute_workflow(input_data)
        print(f"✅ Full workflow test completed with {len(results)} results")
        # Results are saved in the TDD test already, so no need to duplicate
        return True
    except Exception as e:
        print(f"❌ Full workflow test failed: {e}")
        return False

async def test_individual_workflow():
    """Test individual workflow step execution"""
    print("\n🔀 Testing individual workflow step...")
    input_data = CodingTeamInput(
        requirements=TEST_REQUIREMENTS,
        workflow=WorkflowStep.planning,  # Just test the planning step
        team_members=[TeamMember.planner]
    )
    
    try:
        results = await execute_workflow(input_data)
        print(f"✅ Individual workflow step test completed with {len(results)} results")
        return True
    except Exception as e:
        print(f"❌ Individual workflow step test failed: {e}")
        return False

async def run_tests():
    """Run all workflow tests"""
    print("🧪 Starting workflow module tests...")
    
    tests = [
        ("TDD Workflow", test_tdd_workflow()),
        ("Full Workflow", test_full_workflow()),
        ("Individual Workflow Step", test_individual_workflow())
    ]
    
    results = []
    for name, test_coro in tests:
        print(f"\n📋 Running {name} test...")
        try:
            result = await test_coro
            results.append((name, result))
        except Exception as e:
            print(f"❌ Test {name} failed with error: {e}")
            results.append((name, False))
    
    # Print summary
    print("\n📊 Test Results:")
    print("=" * 50)
    success_count = 0
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        if result:
            success_count += 1
        print(f"{name}: {status}")
    print("-" * 50)
    print(f"Total: {success_count}/{len(results)} tests passed")

if __name__ == "__main__":
    print("📋 Workflow Module Test Script")
    print("=" * 50)
    print("This script tests the refactored workflow module functionality")
    asyncio.run(run_tests())
