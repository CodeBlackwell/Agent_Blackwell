#!/usr/bin/env python3
"""Test script to verify proof of execution is included in API responses"""

import requests
import json
import time

API_BASE_URL = "http://localhost:8000"

def test_proof_in_api():
    """Test that proof of execution data is included in API responses"""
    
    print("Testing Proof of Execution in API Responses...")
    print("=" * 80)
    
    # Create a workflow request that includes executor
    request_data = {
        "requirements": "Create a simple calculator function that adds two numbers with a test",
        "workflow_type": "tdd",
        "team_members": ["planner", "designer", "test_writer", "coder", "executor", "reviewer"]
    }
    
    print("1. Submitting workflow request...")
    print(f"   Requirements: {request_data['requirements']}")
    print(f"   Workflow type: {request_data['workflow_type']}")
    print(f"   Team members: {request_data['team_members']}")
    
    try:
        # Submit workflow
        response = requests.post(f"{API_BASE_URL}/execute-workflow", json=request_data)
        response.raise_for_status()
        
        result = response.json()
        session_id = result['session_id']
        print(f"\n✅ Workflow submitted successfully!")
        print(f"   Session ID: {session_id}")
        
        # Poll for completion
        print("\n2. Polling for completion...")
        max_attempts = 60  # 5 minutes max
        attempt = 0
        
        while attempt < max_attempts:
            response = requests.get(f"{API_BASE_URL}/workflow-status/{session_id}")
            response.raise_for_status()
            
            status_data = response.json()
            status = status_data['status']
            
            if status == 'completed':
                print(f"\n✅ Workflow completed!")
                break
            elif status == 'failed':
                print(f"\n❌ Workflow failed!")
                print(f"   Error: {status_data.get('error', 'Unknown error')}")
                return
            else:
                print(f"   Status: {status} (attempt {attempt + 1}/{max_attempts})")
                time.sleep(5)
                attempt += 1
        
        if attempt >= max_attempts:
            print(f"\n❌ Timeout waiting for workflow completion")
            return
        
        # Check execution report
        print("\n3. Checking execution report for proof data...")
        print("=" * 80)
        
        if 'result' in status_data and status_data['result']:
            result = status_data['result']
            
            if 'execution_report' in result and result['execution_report']:
                try:
                    # Parse the execution report JSON
                    exec_report = json.loads(result['execution_report'])
                    
                    # Check for proof data
                    if 'proof_of_execution_path' in exec_report:
                        path = exec_report['proof_of_execution_path']
                        if path:
                            print(f"✅ Proof of execution path found: {path}")
                        else:
                            print("⚠️  proof_of_execution_path is null")
                    else:
                        print("❌ proof_of_execution_path not found in execution report!")
                    
                    if 'proof_of_execution_data' in exec_report:
                        proof_data = exec_report['proof_of_execution_data']
                        if proof_data:
                            print("✅ Proof of execution data found:")
                            print(f"   - Session ID: {proof_data.get('session_id')}")
                            print(f"   - Container ID: {proof_data.get('container_id')}")
                            print(f"   - Execution Success: {proof_data.get('execution_success')}")
                            print(f"   - Number of stages: {len(proof_data.get('stages', []))}")
                        else:
                            print("⚠️  proof_of_execution_data is null")
                    else:
                        print("❌ proof_of_execution_data not found in execution report!")
                    
                except json.JSONDecodeError as e:
                    print(f"❌ Failed to parse execution report JSON: {str(e)}")
            else:
                print("❌ No execution_report found in result!")
            
            # Check agent results for executor
            if 'agent_results' in result:
                executor_found = False
                for agent_result in result['agent_results']:
                    if agent_result['agent'] == 'executor':
                        executor_found = True
                        print(f"\n✅ Executor agent found in results")
                        print(f"   Output length: {agent_result['output_length']} characters")
                        break
                
                if not executor_found:
                    print("\n⚠️  Executor agent not found in agent results!")
        else:
            print("❌ No result data found in status response!")
        
        print("\n" + "=" * 80)
        print("API TEST COMPLETE")
        print("=" * 80)
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ API request failed: {str(e)}")
        print("\nMake sure the API server is running on port 8000")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_proof_in_api()