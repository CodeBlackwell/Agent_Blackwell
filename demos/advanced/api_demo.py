#!/usr/bin/env python3
"""
Demo script showing successful API usage to generate code
"""

import asyncio
import httpx
import json

API_BASE_URL = "http://localhost:8000"

async def demo_code_generation():
    async with httpx.AsyncClient(timeout=60.0) as client:
        print("=" * 60)
        print("ORCHESTRATOR API DEMO - Code Generation")
        print("=" * 60)
        
        # Submit a workflow request
        print("\n📝 Submitting code generation request...")
        workflow_request = {
            "requirements": "Create a Python class called Calculator with methods for add, subtract, multiply, and divide. Include error handling for division by zero and comprehensive docstrings.",
            "workflow_type": "full",
            "max_retries": 3,
            "timeout_seconds": 300
        }
        
        response = await client.post(
            f"{API_BASE_URL}/execute-workflow",
            json=workflow_request
        )
        
        if response.status_code == 200:
            result = response.json()
            session_id = result["session_id"]
            print(f"✅ Workflow started with session ID: {session_id}")
            
            # Monitor progress
            print("\n📊 Monitoring progress...")
            while True:
                await asyncio.sleep(2)
                status_response = await client.get(f"{API_BASE_URL}/workflow-status/{session_id}")
                status_data = status_response.json()
                
                print(f"   Status: {status_data['status']}")
                
                if status_data['status'] in ['completed', 'failed']:
                    if status_data['status'] == 'completed':
                        print(f"\n✅ SUCCESS! Code generated successfully")
                        
                        if status_data.get('result') and status_data['result'].get('agent_results'):
                            print("\n📋 Agent Activity Summary:")
                            for agent in status_data['result']['agent_results']:
                                print(f"   • {agent['agent']}: Generated {agent['output_length']} characters")
                        
                        # Show where files were generated
                        if 'coder' in str(status_data.get('result', {})):
                            print("\n📁 Generated files location:")
                            print("   Check the /generated directory for your new code!")
                    else:
                        print(f"\n❌ Workflow failed: {status_data.get('error', 'Unknown error')}")
                    break
        else:
            print(f"❌ Failed to start workflow: {response.status_code}")

if __name__ == "__main__":
    print("Starting API demo...")
    print("Make sure the API server is running on port 8000")
    print()
    asyncio.run(demo_code_generation())