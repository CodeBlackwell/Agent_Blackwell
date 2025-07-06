"""
Container Manager for Validator Agent

Manages a single Docker container per workflow session for lightweight validation.
No directory creation, purely in-memory execution.
"""

import docker
import hashlib
import asyncio
import os
import tempfile
import tarfile
import io
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from datetime import datetime


class ValidatorContainerManager:
    """Singleton manager for validator containers"""
    
    _instance = None
    _containers = {}  # session_id -> container_info
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ValidatorContainerManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.docker_client = None
        
    def initialize(self):
        """Initialize Docker client"""
        try:
            self.docker_client = docker.from_env()
            self.docker_client.ping()
            print("✅ Validator: Docker connection established")
        except Exception as e:
            raise RuntimeError(f"Failed to connect to Docker: {e}")
    
    def get_or_create_container(self, session_id: str) -> Dict:
        """Get existing container or create new one for session"""
        # Ensure Docker client is initialized
        if self.docker_client is None:
            self.initialize()
            
        if session_id in self._containers:
            # Check if container still exists
            try:
                container = self.docker_client.containers.get(self._containers[session_id]['container_id'])
                if container.status == 'running':
                    print(f"♻️  Validator: Reusing container for session {session_id}")
                    return self._containers[session_id]
            except docker.errors.NotFound:
                # Container was removed, need to create new one
                del self._containers[session_id]
        
        # Create new container
        print(f"🔨 Validator: Creating container for session {session_id}")
        container_info = self._create_container(session_id)
        self._containers[session_id] = container_info
        return container_info
    
    def _create_container(self, session_id: str) -> Dict:
        """Create a new Python container for validation"""
        container_name = f"validator_{session_id}"
        
        try:
            # Simple Python container with minimal setup
            container = self.docker_client.containers.run(
                "python:3.9-slim",
                command="tail -f /dev/null",  # Keep container running
                name=container_name,
                detach=True,
                remove=False,
                labels={
                    "validator": "true",
                    "session_id": session_id,
                    "created": datetime.now().isoformat()
                },
                working_dir="/code",
                mem_limit="512m",  # Limit memory for safety
                cpu_quota=50000,   # Limit CPU (50% of one core)
            )
            
            # Wait for container to be ready
            container.reload()
            
            return {
                "container_id": container.id,
                "container_name": container_name,
                "session_id": session_id,
                "created": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise RuntimeError(f"Failed to create container: {e}")
    
    def execute_code(self, session_id: str, code_files: Dict[str, str]) -> Tuple[bool, str, str]:
        """
        Execute code in container without creating files on host.
        Returns (success, stdout, stderr)
        """
        container_info = self.get_or_create_container(session_id)
        container = self.docker_client.containers.get(container_info['container_id'])
        
        try:
            # Create a temporary archive in memory
            tar_stream = io.BytesIO()
            tar = tarfile.open(fileobj=tar_stream, mode='w')
            
            # Add each code file to the archive
            for filename, content in code_files.items():
                file_data = content.encode('utf-8')
                tarinfo = tarfile.TarInfo(name=filename)
                tarinfo.size = len(file_data)
                tar.addfile(tarinfo, io.BytesIO(file_data))
            
            tar.close()
            tar_stream.seek(0)
            
            # Copy files to container
            container.put_archive('/code', tar_stream.getvalue())
            
            # Determine main file to execute
            main_file = None
            if 'main.py' in code_files:
                main_file = 'main.py'
            elif 'calculator.py' in code_files:
                main_file = 'calculator.py'
            elif len(code_files) == 1:
                main_file = list(code_files.keys())[0]
            else:
                # Find first .py file
                for filename in code_files.keys():
                    if filename.endswith('.py'):
                        main_file = filename
                        break
            
            if not main_file:
                return False, "", "No Python file found to execute"
            
            # Execute the code
            result = container.exec_run(
                f"python {main_file}",
                workdir="/code",
                demux=True
            )
            
            stdout = result.output[0].decode() if result.output[0] else ""
            stderr = result.output[1].decode() if result.output[1] else ""
            
            # Also try to run basic tests
            test_results = self._run_basic_tests(container, code_files)
            if test_results:
                stdout += f"\n\n=== VALIDATION TESTS ===\n{test_results}"
            
            success = result.exit_code == 0
            return success, stdout, stderr
            
        except Exception as e:
            return False, "", f"Execution error: {str(e)}"
    
    def _run_basic_tests(self, container, code_files: Dict[str, str]) -> str:
        """Run basic validation tests on the code"""
        # For calculator-like classes, try basic operations
        test_script = '''
import sys
import traceback

try:
    # Try to import and test Calculator if it exists
    if 'calculator.py' in sys.modules or 'Calculator' in globals():
        from calculator import Calculator
        calc = Calculator()
        
        print("Testing basic operations:")
        
        # Test addition if exists
        if hasattr(calc, 'add'):
            result = calc.add(5, 3)
            print(f"add(5, 3) = {result}")
            assert result == 8, f"Expected 8, got {result}"
            print("✓ Addition works")
        
        # Test subtraction if exists
        if hasattr(calc, 'subtract'):
            result = calc.subtract(10, 4)
            print(f"subtract(10, 4) = {result}")
            assert result == 6, f"Expected 6, got {result}"
            print("✓ Subtraction works")
        
        # Test division if exists
        if hasattr(calc, 'divide'):
            result = calc.divide(10, 2)
            print(f"divide(10, 2) = {result}")
            assert result == 5, f"Expected 5, got {result}"
            print("✓ Division works")
            
            # Test division by zero
            try:
                calc.divide(10, 0)
                print("✗ Division by zero not handled properly")
            except (ValueError, ZeroDivisionError):
                print("✓ Division by zero handled")
        
        print("\\nValidation successful!")
    else:
        print("No Calculator class found to test")
        
except Exception as e:
    print(f"Validation error: {e}")
    traceback.print_exc()
'''
        
        # Only run tests if we have a calculator-like file
        if any('calculator' in f.lower() for f in code_files.keys()):
            try:
                # Write test script to container
                test_data = test_script.encode('utf-8')
                tar_stream = io.BytesIO()
                tar = tarfile.open(fileobj=tar_stream, mode='w')
                tarinfo = tarfile.TarInfo(name='validator_test.py')
                tarinfo.size = len(test_data)
                tar.addfile(tarinfo, io.BytesIO(test_data))
                tar.close()
                tar_stream.seek(0)
                
                container.put_archive('/code', tar_stream.getvalue())
                
                # Run tests
                result = container.exec_run(
                    "python validator_test.py",
                    workdir="/code"
                )
                
                return result.output.decode() if result.output else ""
            except:
                return ""
        
        return ""
    
    def cleanup_container(self, session_id: str):
        """Clean up container for session"""
        if session_id in self._containers:
            try:
                container = self.docker_client.containers.get(self._containers[session_id]['container_id'])
                print(f"🧹 Validator: Cleaning up container for session {session_id}")
                container.stop()
                container.remove()
            except:
                pass  # Container might already be gone
            finally:
                del self._containers[session_id]
    
    def cleanup_all(self):
        """Clean up all validator containers"""
        for session_id in list(self._containers.keys()):
            self.cleanup_container(session_id)


# Global instance with lazy initialization
_container_manager = None


def get_container_manager() -> ValidatorContainerManager:
    """Get the global container manager instance"""
    global _container_manager
    if _container_manager is None:
        _container_manager = ValidatorContainerManager()
    return _container_manager