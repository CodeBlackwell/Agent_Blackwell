#!/usr/bin/env python3
"""Test script to verify proof of execution integration in workflow reports"""

import asyncio
import json
from workflows.workflow_manager import execute_workflow
from shared.data_models import CodingTeamInput, TeamMember
from workflows.monitoring import WorkflowExecutionTracer

async def test_proof_integration():
    """Test that proof of execution is properly integrated into reports"""
    
    print("Testing Proof of Execution Integration...")
    print("=" * 80)
    
    # Create test input that includes executor
    test_input = CodingTeamInput(
        requirements="Create a simple Python function that adds two numbers and include a test for it.",
        workflow_type="tdd",
        team_members=[TeamMember.planner, TeamMember.designer, TeamMember.test_writer, 
                     TeamMember.coder, TeamMember.executor, TeamMember.reviewer]
    )
    
    print("Running TDD workflow with executor...")
    print(f"Requirements: {test_input.requirements}")
    print(f"Team members: {[m.value for m in test_input.team_members]}")
    print()
    
    try:
        # Execute workflow
        results, execution_report = await execute_workflow(test_input)
        
        print(f"\nWorkflow completed successfully!")
        print(f"Number of results: {len(results)}")
        
        # Check if executor was run
        executor_found = False
        for result in results:
            if result.name == "executor":
                executor_found = True
                print(f"\nExecutor output preview: {result.output[:200]}...")
                break
        
        if not executor_found:
            print("\n⚠️  WARNING: Executor agent was not found in results!")
            return
        
        # Check execution report for proof data
        print("\n" + "=" * 80)
        print("CHECKING EXECUTION REPORT FOR PROOF DATA")
        print("=" * 80)
        
        if hasattr(execution_report, 'proof_of_execution_path'):
            print(f"✅ Proof of execution path: {execution_report.proof_of_execution_path}")
        else:
            print("❌ No proof_of_execution_path attribute found in execution report!")
        
        if hasattr(execution_report, 'proof_of_execution_data'):
            if execution_report.proof_of_execution_data:
                print("✅ Proof of execution data found:")
                print(f"   - Session ID: {execution_report.proof_of_execution_data.get('session_id')}")
                print(f"   - Container ID: {execution_report.proof_of_execution_data.get('container_id')}")
                print(f"   - Execution Success: {execution_report.proof_of_execution_data.get('execution_success')}")
                print(f"   - Number of stages: {len(execution_report.proof_of_execution_data.get('stages', []))}")
            else:
                print("⚠️  proof_of_execution_data is None or empty")
        else:
            print("❌ No proof_of_execution_data attribute found in execution report!")
        
        # Check JSON serialization
        print("\n" + "=" * 80)
        print("CHECKING JSON SERIALIZATION")
        print("=" * 80)
        
        try:
            report_json = execution_report.to_json()
            report_dict = json.loads(report_json)
            
            if 'proof_of_execution_path' in report_dict:
                print(f"✅ proof_of_execution_path in JSON: {report_dict['proof_of_execution_path']}")
            else:
                print("❌ proof_of_execution_path not found in JSON!")
            
            if 'proof_of_execution_data' in report_dict:
                if report_dict['proof_of_execution_data']:
                    print("✅ proof_of_execution_data in JSON")
                else:
                    print("⚠️  proof_of_execution_data is null in JSON")
            else:
                print("❌ proof_of_execution_data not found in JSON!")
                
        except Exception as e:
            print(f"❌ Error serializing report to JSON: {str(e)}")
        
        print("\n" + "=" * 80)
        print("TEST COMPLETE")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error running workflow: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_proof_integration())