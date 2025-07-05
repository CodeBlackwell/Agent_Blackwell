#!/usr/bin/env python3
"""
Simple test script for the Orchestrator API
"""

import asyncio
import httpx
import json
from datetime import datetime

API_BASE_URL = "http://localhost:8000"

async def test_api():
    async with httpx.AsyncClient() as client:
        # Test health endpoint
        print("\n1. Testing health endpoint...")
        response = await client.get(f"{API_BASE_URL}/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        
        # Test workflow types endpoint
        print("\n2. Getting workflow types...")
        response = await client.get(f"{API_BASE_URL}/workflow-types")
        print(f"   Status: {response.status_code}")
        print(f"   Available workflows:")
        for wf in response.json():
            print(f"     - {wf['name']}: {wf['description']}")
        
        # Test workflow execution
        print("\n3. Executing a simple workflow...")
        workflow_request = {
            "requirements": "Create a simple Python function that adds two numbers and includes a docstring",
            "workflow_type": "full",
            "max_retries": 3,
            "timeout_seconds": 300
        }
        
        response = await client.post(
            f"{API_BASE_URL}/execute-workflow",
            json=workflow_request
        )
        print(f"   Status: {response.status_code}")
        result = response.json()
        print(f"   Response: {json.dumps(result, indent=2)}")
        
        if response.status_code == 200:
            session_id = result["session_id"]
            print(f"\n4. Monitoring workflow execution (session: {session_id})...")
            
            # Poll for status updates
            max_polls = 30  # Poll for up to 30 seconds
            poll_count = 0
            
            while poll_count < max_polls:
                await asyncio.sleep(1)
                response = await client.get(f"{API_BASE_URL}/workflow-status/{session_id}")
                status_data = response.json()
                
                print(f"   [{datetime.now().strftime('%H:%M:%S')}] Status: {status_data['status']}")
                
                if status_data.get('progress'):
                    progress = status_data['progress']
                    print(f"     Progress: Step {progress.get('current_step', 0)}/{progress.get('total_steps', '?')}")
                
                if status_data['status'] in ['completed', 'failed']:
                    print(f"\n5. Final workflow result:")
                    print(json.dumps(status_data, indent=2))
                    
                    if status_data['status'] == 'completed' and status_data.get('result'):
                        print(f"\n   Agent results summary:")
                        for agent_result in status_data['result'].get('agent_results', []):
                            print(f"     - {agent_result['agent']}: {agent_result['output_length']} chars")
                    break
                
                poll_count += 1
            else:
                print(f"\n   Workflow did not complete within {max_polls} seconds")

if __name__ == "__main__":
    print("Orchestrator API Simple Test")
    print("=" * 60)
    asyncio.run(test_api())
    print("\nTest completed!")