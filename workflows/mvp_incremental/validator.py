"""
Code Validator Module for MVP Incremental Workflow

This module provides a wrapper around the validator agent for code validation
and execution within the MVP incremental workflow context.
"""

import asyncio
import os
import subprocess
import tempfile
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
import time

from workflows.logger import workflow_logger as logger


@dataclass
class ValidationResult:
    """Result from code validation."""
    success: bool
    output: str
    error: Optional[str] = None
    execution_time: float = 0.0


@dataclass
class ExecutionResult:
    """Result from code execution."""
    success: bool
    output: str
    error: Optional[str] = None
    return_code: int = 0


class CodeValidator:
    """Handles code validation and execution for the MVP incremental workflow."""
    
    def __init__(self, working_dir: Optional[Path] = None):
        """Initialize the validator with an optional working directory."""
        self.working_dir = working_dir or Path.cwd()
        self._session_dir = None
        self._docker_container = None
        
    async def validate_code(self, code: str, filename: str = "temp_code.py") -> ValidationResult:
        """
        Validate Python code by checking syntax and attempting to parse it.
        
        Args:
            code: The Python code to validate
            filename: Optional filename for better error messages
            
        Returns:
            ValidationResult with success status and any error messages
        """
        start_time = time.time()
        
        try:
            # First, try to compile the code to check for syntax errors
            compile(code, filename, 'exec')
            
            # If compilation succeeds, try to execute in a safe environment
            # to catch runtime errors in definitions
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
                
            try:
                # Run the code with Python in check mode
                result = subprocess.run(
                    ['python', '-m', 'py_compile', temp_file],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    return ValidationResult(
                        success=True,
                        output="Code validation successful",
                        execution_time=time.time() - start_time
                    )
                else:
                    return ValidationResult(
                        success=False,
                        output=result.stdout,
                        error=result.stderr,
                        execution_time=time.time() - start_time
                    )
                    
            finally:
                os.unlink(temp_file)
                
        except SyntaxError as e:
            return ValidationResult(
                success=False,
                output="",
                error=f"Syntax Error at line {e.lineno}: {e.msg}",
                execution_time=time.time() - start_time
            )
        except Exception as e:
            return ValidationResult(
                success=False,
                output="",
                error=f"Validation Error: {str(e)}",
                execution_time=time.time() - start_time
            )
            
    async def execute_code(self, code: str, timeout: int = 30) -> ExecutionResult:
        """
        Execute code in a subprocess with timeout.
        
        Args:
            code: The code to execute (can be Python code or shell command)
            timeout: Maximum execution time in seconds
            
        Returns:
            ExecutionResult with output and error information
        """
        try:
            # Determine if this is a shell command or Python code
            if code.strip().startswith(('python', 'pytest', 'pip', 'npm', 'git')):
                # Execute as shell command
                result = subprocess.run(
                    code,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=self.working_dir
                )
                
                return ExecutionResult(
                    success=(result.returncode == 0),
                    output=result.stdout,
                    error=result.stderr if result.stderr else None,
                    return_code=result.returncode
                )
            else:
                # Execute as Python code
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                    f.write(code)
                    temp_file = f.name
                    
                try:
                    result = subprocess.run(
                        ['python', temp_file],
                        capture_output=True,
                        text=True,
                        timeout=timeout,
                        cwd=self.working_dir
                    )
                    
                    return ExecutionResult(
                        success=(result.returncode == 0),
                        output=result.stdout,
                        error=result.stderr if result.stderr else None,
                        return_code=result.returncode
                    )
                    
                finally:
                    os.unlink(temp_file)
                    
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                output="",
                error=f"Execution timed out after {timeout} seconds",
                return_code=-1
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                output="",
                error=f"Execution Error: {str(e)}",
                return_code=-1
            )
            
    async def validate_in_docker(self, code: str, session_id: Optional[str] = None) -> ValidationResult:
        """
        Validate code in a Docker container for isolation.
        
        This is a simplified version that would need Docker integration
        in a real implementation.
        """
        # For now, fallback to regular validation
        # In a full implementation, this would:
        # 1. Start or reuse a Docker container
        # 2. Copy code into container
        # 3. Execute and validate
        # 4. Return results
        return await self.validate_code(code)
        
    def create_session(self, session_id: str) -> str:
        """Create a new validation session."""
        self._session_dir = self.working_dir / f"session_{session_id}"
        self._session_dir.mkdir(exist_ok=True)
        return str(self._session_dir)
        
    def cleanup_session(self, session_id: str):
        """Clean up a validation session."""
        if self._session_dir and self._session_dir.exists():
            # In a real implementation, this would also stop Docker containers
            import shutil
            shutil.rmtree(self._session_dir)
            self._session_dir = None
            
    async def run_tests(self, test_command: str = "pytest", test_path: str = ".") -> ExecutionResult:
        """
        Run tests using the specified test command.
        
        Args:
            test_command: The test command to run (default: pytest)
            test_path: Path to test files (default: current directory)
            
        Returns:
            ExecutionResult with test output
        """
        full_command = f"{test_command} {test_path} -v"
        return await self.execute_code(full_command)


# Helper functions for backward compatibility
async def validate_python_code(code: str) -> Tuple[bool, str]:
    """Legacy validation function for compatibility."""
    validator = CodeValidator()
    result = await validator.validate_code(code)
    error_msg = result.error if result.error else ""
    return result.success, error_msg