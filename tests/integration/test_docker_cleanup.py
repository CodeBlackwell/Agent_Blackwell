#!/usr/bin/env python3
"""
Test script to verify Docker container cleanup functionality
"""

import asyncio
import sys
import os
import docker
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.data_models import CodingTeamInput, WorkflowType
from workflows import execute_workflow
from workflows.monitoring import WorkflowExecutionTracer


async def list_executor_containers():
    """List all executor containers"""
    client = docker.from_env()
    containers = client.containers.list(
        all=True,
        filters={"label": "executor=true"}
    )
    return containers


async def test_docker_cleanup():
    """Test that Docker containers are cleaned up after workflow execution"""
    print("\n🧪 Docker Cleanup Test")
    print("=" * 80)
    
    # 1. Check initial state
    print("\n1️⃣ Initial container state:")
    initial_containers = await list_executor_containers()
    print(f"   Found {len(initial_containers)} executor containers")
    for container in initial_containers:
        print(f"   - {container.name} ({container.status})")
    
    # 2. Run a simple workflow that uses executor
    print("\n2️⃣ Running TDD workflow with executor...")
    
    requirements = """
    Create a simple Python function called 'add_numbers' that:
    1. Takes two integer parameters
    2. Returns their sum
    3. Include a simple test that verifies 2 + 3 = 5
    """
    
    input_data = CodingTeamInput(
        requirements=requirements,
        workflow_type="tdd"
    )
    
    tracer = WorkflowExecutionTracer("tdd")
    
    try:
        results, report = await execute_workflow(input_data, tracer)
        print(f"   ✅ Workflow completed successfully")
        
        # Extract session ID from results
        session_id = None
        for result in results:
            if result.name == 'executor' and 'SESSION_ID:' in result.output:
                import re
                match = re.search(r'SESSION_ID:\s*(\S+)', result.output)
                if match:
                    session_id = match.group(1)
                    print(f"   📋 Session ID: {session_id}")
                    break
        
    except Exception as e:
        print(f"   ❌ Workflow failed: {str(e)}")
        return
    
    # 3. Wait a moment for cleanup to complete
    print("\n3️⃣ Waiting for cleanup to complete...")
    await asyncio.sleep(3)
    
    # 4. Check final state
    print("\n4️⃣ Final container state:")
    final_containers = await list_executor_containers()
    print(f"   Found {len(final_containers)} executor containers")
    for container in final_containers:
        print(f"   - {container.name} ({container.status})")
    
    # 5. Verify cleanup
    print("\n5️⃣ Cleanup verification:")
    if session_id:
        # Check if any containers with this session ID still exist
        session_containers = [c for c in final_containers 
                             if session_id in c.name or 
                             (c.labels.get('session_id') == session_id)]
        
        if session_containers:
            print(f"   ❌ FAILED: Found {len(session_containers)} containers still running for session {session_id}")
            for container in session_containers:
                print(f"      - {container.name}")
        else:
            print(f"   ✅ SUCCESS: No containers found for session {session_id} - cleanup worked!")
    
    # Compare container counts
    if len(final_containers) < len(initial_containers):
        print(f"   ✅ Container count decreased from {len(initial_containers)} to {len(final_containers)}")
    elif len(final_containers) == len(initial_containers):
        print(f"   ⚠️  Container count unchanged at {len(final_containers)}")
    else:
        print(f"   ❌ Container count increased from {len(initial_containers)} to {len(final_containers)}")
    
    print("\n" + "=" * 80)
    

async def test_cleanup_on_failure():
    """Test that cleanup happens even when workflow fails"""
    print("\n🧪 Docker Cleanup on Failure Test")
    print("=" * 80)
    
    # 1. Check initial state
    print("\n1️⃣ Initial container state:")
    initial_containers = await list_executor_containers()
    print(f"   Found {len(initial_containers)} executor containers")
    
    # 2. Run a workflow that will fail
    print("\n2️⃣ Running workflow that will fail...")
    
    requirements = """
    This is an intentionally malformed requirement that should cause issues:
    Create a function that @#$%^&* invalid syntax everywhere
    """
    
    input_data = CodingTeamInput(
        requirements=requirements,
        workflow_type="full"  # Use full workflow to test failure cleanup
    )
    
    tracer = WorkflowExecutionTracer("full")
    
    try:
        results, report = await execute_workflow(input_data, tracer)
        print(f"   ✅ Workflow completed (unexpected)")
    except Exception as e:
        print(f"   ⚠️  Workflow failed as expected: {str(e)[:100]}...")
    
    # 3. Wait for cleanup
    print("\n3️⃣ Waiting for cleanup after failure...")
    await asyncio.sleep(3)
    
    # 4. Check final state
    print("\n4️⃣ Final container state after failure:")
    final_containers = await list_executor_containers()
    print(f"   Found {len(final_containers)} executor containers")
    
    # 5. Verify cleanup happened
    print("\n5️⃣ Cleanup verification:")
    if len(final_containers) <= len(initial_containers):
        print(f"   ✅ SUCCESS: Cleanup executed even after failure")
    else:
        print(f"   ❌ FAILED: New containers were not cleaned up after failure")
    
    print("\n" + "=" * 80)


async def manual_cleanup_all():
    """Manually clean up all executor containers"""
    print("\n🧹 Manual Cleanup of All Executor Containers")
    print("=" * 80)
    
    from agents.executor.docker_manager import DockerEnvironmentManager
    
    containers = await list_executor_containers()
    print(f"Found {len(containers)} executor containers to clean up")
    
    if containers:
        print("Cleaning up...")
        await DockerEnvironmentManager.cleanup_all_sessions()
        print("✅ Cleanup completed")
        
        # Verify
        remaining = await list_executor_containers()
        print(f"Remaining containers: {len(remaining)}")
    else:
        print("No containers to clean up")
    
    print("=" * 80)


async def main():
    """Run all tests"""
    print("\n🐳 Docker Container Cleanup Test Suite")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Clean up any existing containers first
    await manual_cleanup_all()
    
    # Run tests
    await test_docker_cleanup()
    await test_cleanup_on_failure()
    
    # Final cleanup
    await manual_cleanup_all()
    
    print(f"\n✅ All tests completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    asyncio.run(main())