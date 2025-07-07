#!/usr/bin/env python3
"""
Simple test to verify Docker cleanup is working
"""

import subprocess
import time

def count_executor_containers():
    """Count executor containers using docker CLI"""
    result = subprocess.run(
        ["docker", "ps", "-a", "--filter", "label=executor=true", "--format", "{{.Names}}"],
        capture_output=True,
        text=True
    )
    containers = [c for c in result.stdout.strip().split('\n') if c]
    return len(containers), containers

def main():
    print("\n🐳 Simple Docker Cleanup Test")
    print("=" * 60)
    
    # 1. Count initial containers
    initial_count, initial_containers = count_executor_containers()
    print(f"\n1. Initial executor containers: {initial_count}")
    for c in initial_containers:
        print(f"   - {c}")
    
    # 2. Run a simple workflow using API
    print("\n2. Running workflow via API...")
    
    api_test = """
import requests
import json
import time

# Submit workflow
response = requests.post(
    "http://localhost:8000/execute-workflow",
    json={
        "requirements": "Create a Python function that adds two numbers and test it",
        "workflow_type": "tdd"
    }
)

if response.status_code == 200:
    data = response.json()
    session_id = data["session_id"]
    print(f"   Workflow started: {session_id}")
    
    # Poll for completion
    for i in range(30):
        time.sleep(2)
        status_response = requests.get(f"http://localhost:8000/workflow-status/{session_id}")
        if status_response.status_code == 200:
            status = status_response.json()
            if status["status"] in ["completed", "failed"]:
                print(f"   Workflow {status['status']}")
                break
            else:
                print(f"   Status: {status['status']}...")
else:
    print(f"   Failed to start workflow: {response.status_code}")
"""
    
    # Save and run API test
    with open("/tmp/api_test.py", "w") as f:
        f.write(api_test)
    
    subprocess.run(["/usr/bin/python3", "/tmp/api_test.py"])
    
    # 3. Wait for cleanup
    print("\n3. Waiting 5 seconds for cleanup...")
    time.sleep(5)
    
    # 4. Count final containers
    final_count, final_containers = count_executor_containers()
    print(f"\n4. Final executor containers: {final_count}")
    for c in final_containers:
        print(f"   - {c}")
    
    # 5. Check results
    print("\n5. Results:")
    if final_count <= initial_count:
        print("   ✅ SUCCESS: Cleanup is working!")
        print(f"   Containers: {initial_count} → {final_count}")
    else:
        print("   ❌ FAILED: Containers were not cleaned up")
        print(f"   Containers increased: {initial_count} → {final_count}")
    
    # 6. Manual cleanup if needed
    if final_count > 0:
        print("\n6. Running manual cleanup...")
        subprocess.run(["docker", "rm", "-f"] + final_containers)
        print("   ✅ Manual cleanup completed")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    print("Note: Make sure both servers are running:")
    print("  - python orchestrator/orchestrator_agent.py")
    print("  - python api/orchestrator_api.py")
    input("\nPress Enter to continue...")
    main()