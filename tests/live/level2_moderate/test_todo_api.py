"""
Live Test: TODO API Implementation
Tests the system's ability to create a REST API with CRUD operations using TDD
"""

import asyncio
import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from tests.live.test_fixtures import workflow_helper, docker_env, perf_monitor, data_generator
from workflows.workflow_manager import execute_workflow


async def test_todo_api_implementation():
    """Test creating a TODO API with TDD workflow"""
    
    # Test requirements
    requirements = """Create a TODO list REST API using FastAPI and TDD with:
- POST /todos - Create a new todo item
- GET /todos - List all todos  
- GET /todos/{id} - Get a specific todo
- PUT /todos/{id} - Update a todo
- DELETE /todos/{id} - Delete a todo

Todo items should have: id, title, description, completed status, created_at timestamp.
Use in-memory storage (dictionary) for this implementation.
Include comprehensive tests for all endpoints and edge cases.

Follow the RED-YELLOW-GREEN TDD cycle for each endpoint."""
    
    # Create test session
    session_dir = await workflow_helper.create_test_session()
    print(f"📁 Test session: {session_dir}")
    
    # Start performance monitoring
    perf_monitor.start()
    perf_monitor.checkpoint("test_start")
    
    try:
        # Execute workflow
        print("🚀 Starting TDD workflow for TODO API...")
        result = await execute_workflow(
            requirements=requirements,
            workflow_type="mvp_incremental",
            session_id="test_todo_api",
            output_dir=str(session_dir / "generated")
        )
        
        perf_monitor.checkpoint("workflow_complete")
        
        # Validate generated files
        print("\n📋 Validating generated files...")
        expected_files = [
            "main.py",
            "models.py",
            "test_main.py"
        ]
        
        validation = workflow_helper.validate_generated_code(
            session_dir / "generated",
            expected_files
        )
        
        assert validation["all_files_exist"], f"Missing files: {validation['missing_files']}"
        print(f"✅ All expected files generated")
        print(f"📊 Total lines of code: {validation['total_lines']}")
        
        # Run tests in Docker
        print("\n🐳 Running tests in Docker container...")
        perf_monitor.checkpoint("docker_start")
        
        # Create requirements.txt for the API
        requirements_txt = session_dir / "generated" / "requirements.txt"
        with open(requirements_txt, "w") as f:
            f.write("fastapi\nuvicorn\npytest\nhttpx\npydantic\n")
        
        container = await docker_env.create_python_container(
            session_dir / "generated",
            requirements=["fastapi", "uvicorn", "pytest", "httpx", "pydantic"]
        )
        
        # Run the tests
        exit_code, output = await docker_env.run_test_command(
            container,
            "python -m pytest test_main.py -v"
        )
        
        perf_monitor.checkpoint("docker_tests_complete")
        
        print("\n📤 Test output:")
        print(output)
        
        assert exit_code == 0, "Tests failed in Docker container"
        print("\n✅ All tests passed in Docker!")
        
        # Start the API server and test it
        print("\n🌐 Starting API server...")
        
        # Start server in background
        server_cmd = "nohup python -m uvicorn main:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &"
        await docker_env.run_test_command(container, server_cmd)
        
        # Wait for server to start
        await asyncio.sleep(3)
        
        # Test API endpoints
        print("\n🧪 Testing API endpoints...")
        
        # Test 1: Create a TODO
        create_todo_cmd = """python -c "
import httpx
import json

todo_data = {
    'title': 'Test TODO',
    'description': 'This is a test todo item',
    'completed': False
}

response = httpx.post('http://localhost:8000/todos', json=todo_data)
print(f'Create TODO: {response.status_code}')
print(json.dumps(response.json(), indent=2))
"
"""
        exit_code, output = await docker_env.run_test_command(container, create_todo_cmd)
        print(output)
        assert exit_code == 0 and "200" in output or "201" in output, "Failed to create TODO"
        
        # Test 2: List all TODOs
        list_todos_cmd = """python -c "
import httpx
import json

response = httpx.get('http://localhost:8000/todos')
print(f'List TODOs: {response.status_code}')
todos = response.json()
print(f'Number of TODOs: {len(todos)}')
"
"""
        exit_code, output = await docker_env.run_test_command(container, list_todos_cmd)
        print(output)
        assert exit_code == 0 and "200" in output, "Failed to list TODOs"
        
        # Test 3: Get specific TODO
        get_todo_cmd = """python -c "
import httpx

response = httpx.get('http://localhost:8000/todos/1')
print(f'Get TODO: {response.status_code}')
if response.status_code == 200:
    print('✅ Successfully retrieved TODO')
"
"""
        exit_code, output = await docker_env.run_test_command(container, get_todo_cmd)
        print(output)
        
        # Test 4: Update TODO
        update_todo_cmd = """python -c "
import httpx

update_data = {'completed': True}
response = httpx.put('http://localhost:8000/todos/1', json=update_data)
print(f'Update TODO: {response.status_code}')
if response.status_code in [200, 204]:
    print('✅ Successfully updated TODO')
"
"""
        exit_code, output = await docker_env.run_test_command(container, update_todo_cmd)
        print(output)
        
        # Test 5: Delete TODO
        delete_todo_cmd = """python -c "
import httpx

response = httpx.delete('http://localhost:8000/todos/1')
print(f'Delete TODO: {response.status_code}')
if response.status_code in [200, 204]:
    print('✅ Successfully deleted TODO')
"
"""
        exit_code, output = await docker_env.run_test_command(container, delete_todo_cmd)
        print(output)
        
        # Test edge cases
        print("\n🔍 Testing edge cases...")
        
        # Test non-existent TODO
        edge_case_cmd = """python -c "
import httpx

response = httpx.get('http://localhost:8000/todos/999')
print(f'Get non-existent TODO: {response.status_code}')
if response.status_code == 404:
    print('✅ Correctly returned 404 for non-existent TODO')
"
"""
        exit_code, output = await docker_env.run_test_command(container, edge_case_cmd)
        print(output)
        
        perf_monitor.checkpoint("api_tests_complete")
        
        # Check server logs
        exit_code, logs = await docker_env.run_test_command(container, "cat server.log")
        print("\n📜 Server logs:")
        print(logs[:500] + "..." if len(logs) > 500 else logs)
        
        perf_monitor.checkpoint("test_complete")
        
        # Clean up
        await docker_env.cleanup()
        
        # Performance summary
        perf_metrics = perf_monitor.stop()
        summary = perf_monitor.get_summary()
        
        print("\n📊 Performance Summary:")
        print(f"Total duration: {summary['duration']:.2f} seconds")
        print(f"Checkpoints: {summary['total_checkpoints']}")
        
        if "avg_checkpoint_duration" in summary:
            print(f"Average checkpoint duration: {summary['avg_checkpoint_duration']:.2f} seconds")
        
        print("\n✅ TODO API test completed successfully!")
        
        return {
            "success": True,
            "session_dir": str(session_dir),
            "validation": validation,
            "performance": summary
        }
        
    except Exception as e:
        await docker_env.cleanup()
        perf_monitor.stop()
        
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            "success": False,
            "error": str(e),
            "session_dir": str(session_dir)
        }


if __name__ == "__main__":
    # Run the test
    result = asyncio.run(test_todo_api_implementation())
    
    # Exit with appropriate code
    sys.exit(0 if result["success"] else 1)