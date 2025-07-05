"""
Direct test for Docker environment manager functionality.
"""
import os
import asyncio
import sys
import tempfile
import shutil
import subprocess
from pathlib import Path

# Add the project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import Docker manager directly
from agents.executor.docker_manager import DockerEnvironmentManager, EnvironmentSpec
from agents.executor.executor_agent import generate_session_id

# Add simple logging for Docker operations
DOCKER_DEBUG = True

def log_debug(message):
    """Print debug messages if debug is enabled"""
    if DOCKER_DEBUG:
        print(message)

async def custom_build_container(code_content, env_spec, session_id):
    """Custom implementation to debug Docker build context issues"""
    # Create build context manually
    with tempfile.TemporaryDirectory() as build_dir:
        build_path = Path(build_dir)
        print(f"\n🔍 Debug: Created temp build dir: {build_path}")
        
        # Create a test Python file directly to verify build context
        test_file_path = build_path / "test_add.py"
        test_file_path.write_text("def add(a, b):\n    return a + b\n\nresult = add(5, 7)\nprint(f\"Result: {result}\")")
        print(f"📄 Debug: Wrote test file to {test_file_path} ({os.path.getsize(test_file_path)} bytes)")
        
        # Create Dockerfile manually
        dockerfile_content = f"FROM python:3.9-slim\nWORKDIR /app\nCOPY . .\nCMD [\"python\", \"test_add.py\"]"  
        dockerfile_path = build_path / "Dockerfile"
        dockerfile_path.write_text(dockerfile_content)
        print(f"📄 Debug: Wrote Dockerfile to {dockerfile_path} ({os.path.getsize(dockerfile_path)} bytes)")
        
        # List files in build context
        print("📁 Debug: Files in build context:")
        for item in build_path.iterdir():
            print(f"  - {item.name} ({os.path.getsize(item)} bytes)")

        # Try building with Docker API
        import docker
        client = docker.from_env()
        print("🔨 Debug: Building container with Docker API...")
        
        try:
            image_tag = f"executor_debug_{session_id}:latest"
            image, logs = client.images.build(
                path=str(build_path),
                tag=image_tag,
                rm=True,
                forcerm=True
            )
            print(f"✅ Debug: Successfully built image: {image.tags}")
            
            # Run container
            print("🚀 Debug: Running container...")
            container = client.containers.run(
                image_tag,
                detach=False,
                remove=True
            )
            print(f"📋 Debug: Container output:\n{container.decode('utf-8')}")
            
            return True
        except Exception as e:
            print(f"❌ Debug: Docker build error: {str(e)}")
            return False

async def main():
    """Test the Docker environment manager directly."""
    print("📦 Testing Docker Environment Manager Directly")
    
    # Generate a session ID
    session_id = generate_session_id()
    print(f"🆔 Session ID: {session_id}")
    
    # Try custom build first to verify Docker functionality
    print("\n🧪 Testing Docker functionality with custom build...")
    success = await custom_build_container("", None, session_id)
    
    # Create a Python environment spec
    env_spec = EnvironmentSpec(
        language="python",
        version="3.9",
        base_image="python:3.9-slim",
        dependencies=[],
        system_packages=[],
        build_commands=[],
        execution_commands=["python /app/test_add.py"],
        working_dir="/app"
    )
    
    # The DockerEnvironmentManager now creates requirements.txt files automatically
    # No need for monkey patching anymore
    
    # Simple Python code to execute with proper FILENAME format
    # Note: We need to ensure the format exactly matches what _parse_code_files expects
    code_content = "FILENAME: test_add.py\n```python\ndef add(a, b):\n    return a + b\n\nresult = add(5, 7)\nprint(f\"Result: {result}\")\n```"
    
    print("🚀 Building and executing in Docker...")
    
    # Initialize Docker manager
    docker_manager = DockerEnvironmentManager(session_id)
    try:
        # Debug: manually parse code files to see what's happening
        code_files = docker_manager._parse_code_files(code_content)
        print("\n📁 Parsed code files:")
        print(f"Found {len(code_files)} file(s):")
        for i, file in enumerate(code_files):
            print(f"  {i+1}. {file.get('filename', 'UNNAMED')} ({len(file.get('content', ''))} chars)")
        
        # Initialize Docker connection
        await docker_manager.initialize()
        
        # Build or retrieve container
        container_info = await docker_manager.get_or_create_environment(
            env_spec, code_content
        )
        print(f"✅ Container created: {container_info['container_name']}")
        
        # Execute in container
        execution_result = await docker_manager.execute_in_container(
            container_info['container_id'],
            env_spec.execution_commands
        )
        
        # Print result
        print("\n📋 Execution Results:")
        for execution in execution_result['executions']:
            print(f"\n▶️  Command: {execution['command']}")
            print(f"Exit Code: {execution['exit_code']}")
            print(f"STDOUT:\n{execution['stdout']}\n")
            if execution['stderr']:
                print(f"STDERR:\n{execution['stderr']}\n")
                
        # Clean up
        print("\n🧹 Cleaning up container...")
        await docker_manager.cleanup_session(session_id)
                
    except Exception as e:
        print(f"❌ Docker error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✅ Test completed")

if __name__ == "__main__":
    asyncio.run(main())
