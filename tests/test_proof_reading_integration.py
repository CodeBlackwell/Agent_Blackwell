#!/usr/bin/env python3
"""
Test script to verify that proof of execution reading is integrated into workflows.
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from workflows.workflow_manager import execute_workflow
from agents.executor.proof_reader import ProofOfExecutionReader
from workflows.workflow_config import GENERATED_CODE_PATH


async def test_tdd_workflow_with_proof():
    """Test TDD workflow with executor and verify proof of execution is included"""
    print("🧪 Testing TDD Workflow with Proof of Execution Integration")
    print("=" * 80)
    
    # Simple test requirements
    requirements = """
Create a simple Python function that calculates the factorial of a number.
Include comprehensive tests that verify:
1. Factorial of 0 is 1
2. Factorial of positive numbers
3. Error handling for negative numbers

The function should raise a ValueError for negative inputs.
"""
    
    session_id = f"proof_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        print(f"\n📋 Starting TDD workflow with session ID: {session_id}")
        print("This will include the executor agent for proof of execution...\n")
        
        # Execute workflow with executor
        result = await execute_workflow(
            requirements=requirements,
            workflow_type="tdd",
            session_id=session_id
        )
        
        print("\n✅ Workflow completed!")
        
        # Check if executor output contains proof of execution
        executor_results = [r for r in result.results if r.name == "executor"]
        
        if executor_results:
            print("\n📄 Checking executor output for proof of execution...")
            executor_output = executor_results[0].output
            
            # Check if proof details are in the output
            if "📄 PROOF OF EXECUTION" in executor_output:
                print("✅ Proof of execution details found in executor output!")
                
                # Extract and display the proof section
                proof_start = executor_output.find("📄 PROOF OF EXECUTION")
                if proof_start != -1:
                    proof_section = executor_output[proof_start:]
                    print("\n" + "-" * 40)
                    print("Proof of Execution Section:")
                    print("-" * 40)
                    print(proof_section[:1000])  # First 1000 chars
                    if len(proof_section) > 1000:
                        print("... (truncated)")
            else:
                print("⚠️ Proof of execution details not found in executor output")
                
                # Try to read proof directly
                print("\n🔍 Attempting to read proof document directly...")
                reader = ProofOfExecutionReader(session_id)
                proof_summary = reader.get_execution_summary()
                
                if proof_summary["found"]:
                    print(f"✅ Found proof document at: {proof_summary['proof_path']}")
                    print(f"   Total stages: {proof_summary['total_stages']}")
                    print(f"   Execution success: {proof_summary.get('execution_success', False)}")
                else:
                    print("❌ No proof document found")
        else:
            print("\n⚠️ No executor results found in workflow output")
        
        # Display all team member outputs summary
        print("\n📊 Workflow Results Summary:")
        print("-" * 40)
        for team_result in result.results:
            print(f"{team_result.name}: {len(team_result.output)} characters")
            
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()


async def test_full_workflow_with_proof():
    """Test Full workflow with executor and verify proof of execution is included"""
    print("\n\n🧪 Testing Full Workflow with Proof of Execution Integration")
    print("=" * 80)
    
    # Simple test requirements
    requirements = """
Create a simple REST API endpoint that returns the current time.
Use FastAPI framework and include proper error handling.
"""
    
    session_id = f"proof_full_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        print(f"\n📋 Starting Full workflow with session ID: {session_id}")
        print("This will include the executor agent for proof of execution...\n")
        
        # Execute workflow with executor
        result = await execute_workflow(
            requirements=requirements,
            workflow_type="full",
            session_id=session_id
        )
        
        print("\n✅ Workflow completed!")
        
        # Check executor results
        executor_results = [r for r in result.results if r.name == "executor"]
        
        if executor_results:
            print("\n📄 Checking executor output for proof of execution...")
            executor_output = executor_results[0].output
            
            if "📄 PROOF OF EXECUTION" in executor_output:
                print("✅ Proof of execution details found in executor output!")
            else:
                print("⚠️ Proof of execution details not found in executor output")
        else:
            print("\n⚠️ No executor results found in workflow output")
            
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all tests"""
    print("🚀 Proof of Execution Integration Test Suite")
    print("=" * 80)
    print("\nThis test verifies that proof of execution details are")
    print("automatically included in workflow executor outputs.\n")
    
    # Run TDD workflow test
    await test_tdd_workflow_with_proof()
    
    # Run Full workflow test
    await test_full_workflow_with_proof()
    
    print("\n" + "=" * 80)
    print("✅ All tests completed!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())