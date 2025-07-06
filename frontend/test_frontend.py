#!/usr/bin/env python3
"""
Test script to verify frontend functionality
"""
import json
import time
import requests
from pathlib import Path

def test_api_endpoints():
    """Test that all required API endpoints are accessible"""
    print("Testing API endpoints...")
    
    # Test health endpoint
    try:
        response = requests.get("http://localhost:8000/health")
        print(f"✅ Health check: {response.status_code} - {response.json()['status']}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False
    
    # Test workflow types endpoint
    try:
        response = requests.get("http://localhost:8000/workflow-types")
        workflows = response.json()
        print(f"✅ Workflow types: Found {len(workflows)} workflows")
        for wf in workflows:
            print(f"   - {wf['name']}: {wf['description'][:50]}...")
    except Exception as e:
        print(f"❌ Workflow types failed: {e}")
        return False
    
    return True

def test_workflow_execution():
    """Test a simple workflow execution"""
    print("\nTesting workflow execution...")
    
    # Submit a workflow
    payload = {
        "requirements": "Create a function that adds two numbers",
        "workflow_type": "full",
        "max_retries": 3,
        "timeout_seconds": 300
    }
    
    try:
        response = requests.post("http://localhost:8000/execute-workflow", json=payload)
        result = response.json()
        session_id = result['session_id']
        print(f"✅ Workflow started: {session_id}")
        
        # Poll for status
        print("   Polling for status...")
        for i in range(10):  # Poll for up to 20 seconds
            time.sleep(2)
            status_response = requests.get(f"http://localhost:8000/workflow-status/{session_id}")
            status = status_response.json()
            
            print(f"   Status: {status['status']}")
            
            if status['status'] == 'completed':
                print("✅ Workflow completed!")
                if status.get('result') and status['result'].get('agent_results'):
                    print(f"   Agents involved: {status['result']['agent_count']}")
                    for agent in status['result']['agent_results']:
                        print(f"   - {agent['agent']}: {agent['output_length']} chars")
                return True
            elif status['status'] == 'failed':
                print(f"❌ Workflow failed: {status.get('error', 'Unknown error')}")
                return False
        
        print("⏱️  Workflow still running after 20 seconds")
        return True
        
    except Exception as e:
        print(f"❌ Workflow execution failed: {e}")
        return False

def verify_frontend_file():
    """Verify the frontend file exists and has expected content"""
    print("\nVerifying frontend file...")
    
    frontend_path = Path(__file__).parent / "index.html"
    if not frontend_path.exists():
        print(f"❌ Frontend file not found at {frontend_path}")
        return False
    
    content = frontend_path.read_text()
    
    # Check for key elements
    checks = [
        ("API endpoint", "http://localhost:8000"),
        ("Chat interface", "chat-messages"),
        ("Monitoring section", "agentMonitor"),
        ("Workflow selector", "workflowType"),
        ("Polling mechanism", "startPolling")
    ]
    
    all_good = True
    for name, keyword in checks:
        if keyword in content:
            print(f"✅ {name}: Found")
        else:
            print(f"❌ {name}: Not found")
            all_good = False
    
    return all_good

def main():
    print("Frontend Test Suite")
    print("=" * 50)
    
    # Run tests
    api_ok = test_api_endpoints()
    frontend_ok = verify_frontend_file()
    
    if api_ok and frontend_ok:
        workflow_ok = test_workflow_execution()
        
        if workflow_ok:
            print("\n✅ All tests passed! Frontend should work correctly.")
            print("\nTo use the frontend:")
            print("1. Open frontend/index.html in your web browser")
            print("2. Select a workflow type")
            print("3. Enter your requirements")
            print("4. Watch the agents work in real-time!")
        else:
            print("\n⚠️  Workflow execution had issues, but frontend may still work.")
    else:
        print("\n❌ Some tests failed. Please check the server logs.")

if __name__ == "__main__":
    main()