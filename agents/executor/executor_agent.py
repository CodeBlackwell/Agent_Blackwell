#!/usr/bin/env python3
"""
Executor Agent Module - Responsible for executing code and tests in isolated environments

This agent handles:
1. Code execution in appropriate runtime environments
2. Test execution and result parsing
3. Environment setup and teardown
4. Structured result reporting

File: agents/executor/executor_agent.py
"""

from collections.abc import AsyncGenerator
import os
import sys
import json
import re
import tempfile
import subprocess
import asyncio
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from dotenv import load_dotenv

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from acp_sdk import Message
from acp_sdk.models import MessagePart
from beeai_framework.agents.react import ReActAgent
from beeai_framework.backend.chat import ChatModel
from beeai_framework.memory import TokenMemory
from beeai_framework.utils.dicts import exclude_none

# Load environment variables from .env file
load_dotenv()

# ============================================================================
# EXECUTION RESULT MODELS
# ============================================================================

class ExecutionStatus(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    ENVIRONMENT_ERROR = "environment_error"
    PARSING_ERROR = "parsing_error"

class TechnologyStack(str, Enum):
    PYTHON = "python"
    NODEJS = "nodejs"
    JAVASCRIPT = "javascript"
    JAVA = "java"
    GO = "go"
    RUST = "rust"
    UNKNOWN = "unknown"

@dataclass
class TestResult:
    """Individual test result"""
    name: str
    status: str  # "passed", "failed", "skipped", "error"
    duration: float = 0.0
    message: Optional[str] = None
    stacktrace: Optional[str] = None
    
    @property
    def status_emoji(self) -> str:
        return {
            "passed": "✅",
            "failed": "❌", 
            "skipped": "⏭️",
            "error": "💥"
        }.get(self.status, "❓")

@dataclass
class ExecutionResult:
    """Complete execution result"""
    status: ExecutionStatus
    tech_stack: TechnologyStack
    execution_time: float
    exit_code: int
    stdout: str
    stderr: str
    test_results: List[TestResult] = field(default_factory=list)
    environment_info: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    
    @property
    def success(self) -> bool:
        return self.status == ExecutionStatus.SUCCESS
    
    @property
    def test_summary(self) -> Dict[str, int]:
        summary = {"passed": 0, "failed": 0, "skipped": 0, "error": 0}
        for test in self.test_results:
            summary[test.status] = summary.get(test.status, 0) + 1
        return summary
    
    @property
    def test_pass_rate(self) -> float:
        total = len(self.test_results)
        if total == 0:
            return 100.0
        passed = self.test_summary["passed"]
        return (passed / total) * 100

# ============================================================================
# EXECUTOR AGENT CONFIGURATION
# ============================================================================

executor_config = {
    "model": "openai:gpt-3.5-turbo",
    "timeout": 300,  # 5 minutes default timeout
    "max_output_size": 10000,  # Maximum stdout/stderr size to capture
}

EXECUTION_INSTRUCTIONS = """
You are a code execution specialist. Your role is to:
1. Analyze code and determine the appropriate execution environment
2. Execute code and tests in isolated, secure environments
3. Parse execution results and test outputs accurately
4. Provide detailed, structured feedback on execution results
5. Identify and report runtime errors, test failures, and environment issues

IMPORTANT EXECUTION PRINCIPLES:
- Always execute code in isolated environments
- Parse test results accurately from various testing frameworks
- Provide clear, actionable feedback on failures
- Report performance metrics and resource usage
- Handle timeouts and resource limits gracefully

OUTPUT FORMAT: Always structure your response with:
- Execution Status (success/failure/timeout/error)
- Technology Stack Detected
- Execution Summary
- Test Results (if applicable)
- Performance Metrics
- Error Analysis (if applicable)
- Recommendations for fixing issues

Be precise, helpful, and security-conscious in all executions.
"""

# ============================================================================
# TECHNOLOGY STACK DETECTION
# ============================================================================

class TechStackDetector:
    """Detects technology stack from code content and files"""
    
    @staticmethod
    def detect_from_files(files: List[Dict[str, str]]) -> TechnologyStack:
        """Detect tech stack from file list"""
        for file in files:
            filename = file.get("filename", "").lower()
            content = file.get("content", "").lower()
            
            # Node.js/JavaScript detection
            if (filename.endswith((".js", ".ts", ".json")) or 
                "package.json" in filename or
                "node_modules" in content or
                "npm" in content or
                "require(" in content or
                ("import" in content and "from" in content)):
                return TechnologyStack.NODEJS
            
            # Python detection
            if (filename.endswith((".py", ".pyw")) or
                "requirements.txt" in filename or
                "setup.py" in filename or
                "def " in content or
                "import " in content or
                ("from " in content and "import" in content)):
                return TechnologyStack.PYTHON
            
            # Java detection
            if (filename.endswith((".java", ".jar")) or
                "pom.xml" in filename or
                "build.gradle" in filename or
                "public class" in content or
                "public static void main" in content):
                return TechnologyStack.JAVA
            
            # Go detection
            if (filename.endswith(".go") or
                "go.mod" in filename or
                "package main" in content or
                "func main()" in content):
                return TechnologyStack.GO
            
            # Rust detection
            if (filename.endswith(".rs") or
                "Cargo.toml" in filename or
                "fn main()" in content or
                "use std::" in content):
                return TechnologyStack.RUST
        
        return TechnologyStack.UNKNOWN
    
    @staticmethod
    def detect_from_content(content: str) -> TechnologyStack:
        """Detect tech stack from code content"""
        content_lower = content.lower()
        
        # JavaScript/Node.js patterns
        if any(pattern in content_lower for pattern in [
            "const ", "let ", "var ", "require(", "module.exports", 
            "express", "app.listen", "npm", "node"
        ]):
            return TechnologyStack.NODEJS
        
        # Python patterns
        if any(pattern in content_lower for pattern in [
            "def ", "import ", "from ", "print(", "if __name__", 
            "flask", "django", "fastapi", "pip install"
        ]):
            return TechnologyStack.PYTHON
        
        return TechnologyStack.UNKNOWN

# ============================================================================
# TEST RESULT PARSERS
# ============================================================================

class TestResultParser:
    """Parses test results from various testing frameworks"""
    
    @staticmethod
    def parse_python_tests(output: str) -> List[TestResult]:
        """Parse Python test results (pytest, unittest)"""
        tests = []
        
        # Pytest format parsing
        pytest_pattern = r"(\w+\.py)::\w+::(\w+)\s+(PASSED|FAILED|SKIPPED|ERROR)(?:\s+\[(\d+\.\d+)s\])?"
        for match in re.finditer(pytest_pattern, output):
            file_name, test_name, status, duration = match.groups()
            tests.append(TestResult(
                name=f"{file_name}::{test_name}",
                status=status.lower(),
                duration=float(duration) if duration else 0.0
            ))
        
        # Unittest format parsing
        unittest_pattern = r"(\w+)\s+\((\w+\.\w+)\)\s+\.\.\.\s+(ok|FAIL|ERROR|SKIP)"
        for match in re.finditer(unittest_pattern, output):
            test_name, class_name, status = match.groups()
            status_map = {"ok": "passed", "FAIL": "failed", "ERROR": "error", "SKIP": "skipped"}
            tests.append(TestResult(
                name=f"{class_name}.{test_name}",
                status=status_map.get(status, "unknown")
            ))
        
        # Simple pattern for basic test output
        if not tests:
            lines = output.split('\n')
            for line in lines:
                if 'test' in line.lower():
                    if any(word in line.lower() for word in ['ok', 'pass', 'success', '.']):
                        tests.append(TestResult(name=line.strip()[:50], status="passed"))
                    elif any(word in line.lower() for word in ['fail', 'error', 'f']):
                        tests.append(TestResult(name=line.strip()[:50], status="failed"))
        
        return tests
    
    @staticmethod
    def parse_javascript_tests(output: str) -> List[TestResult]:
        """Parse JavaScript test results (Jest, Mocha, Jasmine)"""
        tests = []
        
        # Jest format parsing
        jest_pattern = r"(✓|×|○)\s+(.+?)(?:\s+\((\d+)\s*ms\))?"
        for match in re.finditer(jest_pattern, output):
            symbol, test_name, duration = match.groups()
            status_map = {"✓": "passed", "×": "failed", "○": "skipped"}
            tests.append(TestResult(
                name=test_name.strip(),
                status=status_map.get(symbol, "unknown"),
                duration=float(duration) / 1000 if duration else 0.0
            ))
        
        # Mocha format parsing
        mocha_pattern = r"(✓|×|△)\s+(.+?)(?:\s+\((\d+)ms\))?"
        for match in re.finditer(mocha_pattern, output):
            symbol, test_name, duration = match.groups()
            status_map = {"✓": "passed", "×": "failed", "△": "skipped"}
            tests.append(TestResult(
                name=test_name.strip(),
                status=status_map.get(symbol, "unknown"),
                duration=float(duration) / 1000 if duration else 0.0
            ))
        
        # Generic test parsing for Node.js
        if not tests:
            lines = output.split('\n')
            for line in lines:
                if any(indicator in line.lower() for indicator in ['test', 'spec']):
                    if any(success in line for success in ['✓', 'pass', 'ok']):
                        tests.append(TestResult(name=line.strip()[:50], status="passed"))
                    elif any(failure in line for failure in ['×', 'fail', 'error']):
                        tests.append(TestResult(name=line.strip()[:50], status="failed"))
        
        return tests

# ============================================================================
# CODE EXECUTOR
# ============================================================================

class CodeExecutor:
    """Handles code execution in various environments"""
    
    def __init__(self):
        self.temp_dir = None
        self.timeout = executor_config["timeout"]
    
    async def execute_code(self, files: List[Dict[str, str]], tech_stack: TechnologyStack) -> ExecutionResult:
        """Execute code files in appropriate environment"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Create temporary directory for execution
            self.temp_dir = tempfile.mkdtemp(prefix="executor_")
            print(f"🔧 Created temp directory: {self.temp_dir}")
            
            # Write files to temp directory
            await self._write_files(files)
            
            # Execute based on technology stack
            if tech_stack == TechnologyStack.PYTHON:
                result = await self._execute_python()
            elif tech_stack == TechnologyStack.NODEJS:
                result = await self._execute_nodejs()
            else:
                result = await self._execute_generic()
            
            result.execution_time = asyncio.get_event_loop().time() - start_time
            result.tech_stack = tech_stack
            
            return result
            
        except asyncio.TimeoutError:
            return ExecutionResult(
                status=ExecutionStatus.TIMEOUT,
                tech_stack=tech_stack,
                execution_time=self.timeout,
                exit_code=-1,
                stdout="",
                stderr="Execution timed out",
                error_message=f"Execution exceeded {self.timeout}s timeout"
            )
        except Exception as e:
            return ExecutionResult(
                status=ExecutionStatus.ENVIRONMENT_ERROR,
                tech_stack=tech_stack,
                execution_time=asyncio.get_event_loop().time() - start_time,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                error_message=f"Environment error: {str(e)}"
            )
        finally:
            await self._cleanup()
    
    async def _write_files(self, files: List[Dict[str, str]]):
        """Write files to temporary directory"""
        for file in files:
            filename = file.get("filename", "")
            content = file.get("content", "")
            
            if not filename:
                continue
            
            file_path = Path(self.temp_dir) / filename
            
            # Create directory structure if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"📝 Created file: {filename}")
    
    async def _execute_python(self) -> ExecutionResult:
        """Execute Python code"""
        try:
            # Look for main Python file
            main_files = ["app.py", "main.py", "run.py", "server.py"]
            test_files = [f for f in os.listdir(self.temp_dir) if f.startswith("test_") and f.endswith(".py")]
            
            main_file = None
            for candidate in main_files:
                if os.path.exists(os.path.join(self.temp_dir, candidate)):
                    main_file = candidate
                    break
            
            # Execute tests if available
            if test_files:
                print(f"🧪 Found test files: {test_files}")
                return await self._run_python_tests()
            elif main_file:
                print(f"▶️ Running main file: {main_file}")
                return await self._run_python_main(main_file)
            else:
                # Try to find any .py file
                py_files = [f for f in os.listdir(self.temp_dir) if f.endswith(".py")]
                if py_files:
                    print(f"▶️ Running Python file: {py_files[0]}")
                    return await self._run_python_main(py_files[0])
                else:
                    return ExecutionResult(
                        status=ExecutionStatus.FAILURE,
                        tech_stack=TechnologyStack.PYTHON,
                        execution_time=0,
                        exit_code=1,
                        stdout="",
                        stderr="No Python files found to execute",
                        error_message="No executable Python files found"
                    )
        except Exception as e:
            return ExecutionResult(
                status=ExecutionStatus.ENVIRONMENT_ERROR,
                tech_stack=TechnologyStack.PYTHON,
                execution_time=0,
                exit_code=1,
                stdout="",
                stderr=str(e),
                error_message=f"Python execution error: {str(e)}"
            )
    
    async def _run_python_tests(self) -> ExecutionResult:
        """Run Python tests using pytest or unittest"""
        # Check for test files
        test_files = [f for f in os.listdir(self.temp_dir) if f.startswith("test_") and f.endswith(".py")]
        if not test_files:
            return ExecutionResult(
                status=ExecutionStatus.SUCCESS,  # No tests is not a failure
                tech_stack=TechnologyStack.PYTHON,
                execution_time=0,
                exit_code=0,
                stdout="No test files found.",
                stderr="",
                test_results=[],
                environment_info={"test_framework": "none"}
            )
        
        # Try multiple test execution methods
        methods = [
            # Method 1: Run test files directly
            {
                "name": "direct",
                "cmd": [sys.executable] + [os.path.join(self.temp_dir, f) for f in test_files],
                "framework": "direct"
            },
            # Method 2: Try pytest
            {
                "name": "pytest",
                "cmd": [sys.executable, "-m", "pytest", "-v", "."],
                "framework": "pytest"
            },
            # Method 3: Try unittest discover
            {
                "name": "unittest",
                "cmd": [sys.executable, "-m", "unittest", "discover", "-v"],
                "framework": "unittest"
            }
        ]
        
        for method in methods:
            try:
                print(f"🔄 Attempting to run tests with {method['name']}...")
                process = await asyncio.wait_for(
                    asyncio.create_subprocess_exec(
                        *method["cmd"],
                        cwd=self.temp_dir,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    ),
                    timeout=self.timeout
                )
                
                stdout, stderr = await process.communicate()
                stdout_str = stdout.decode('utf-8', errors='ignore')
                stderr_str = stderr.decode('utf-8', errors='ignore')
                
                # Debug output
                print(f"📝 {method['name']} exit code: {process.returncode}")
                
                # Skip to next method if there's an error about missing module
                if "No module named" in stderr_str and method["name"] != "direct":
                    continue
                
                # Parse test results
                test_results = TestResultParser.parse_python_tests(stdout_str + stderr_str)
                
                # If we got here, we've successfully run the tests with this method
                return ExecutionResult(
                    status=ExecutionStatus.SUCCESS if process.returncode == 0 else ExecutionStatus.FAILURE,
                    tech_stack=TechnologyStack.PYTHON,
                    execution_time=0,  # Will be set by caller
                    exit_code=process.returncode,
                    stdout=stdout_str,
                    stderr=stderr_str,
                    test_results=test_results,
                    environment_info={"test_framework": method["framework"]}
                )
                
            except Exception as e:
                print(f"Error with {method['name']}: {str(e)}")
                # Continue to next method
        
        # If all methods failed
        return ExecutionResult(
            status=ExecutionStatus.ENVIRONMENT_ERROR,
            tech_stack=TechnologyStack.PYTHON,
            execution_time=0,
            exit_code=1,
            stdout="",
            stderr="Failed to run tests with any available method",
            error_message="Failed to run Python tests: No suitable test execution method found"
        )
    async def _run_python_main(self, main_file: str) -> ExecutionResult:
        """Run main Python file"""
        try:
            process = await asyncio.wait_for(
                asyncio.create_subprocess_exec(
                    sys.executable, main_file,
                    cwd=self.temp_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                ),
                timeout=self.timeout
            )
            
            stdout, stderr = await process.communicate()
            stdout_str = stdout.decode('utf-8', errors='ignore')
            stderr_str = stderr.decode('utf-8', errors='ignore')
            
            return ExecutionResult(
                status=ExecutionStatus.SUCCESS if process.returncode == 0 else ExecutionStatus.FAILURE,
                tech_stack=TechnologyStack.PYTHON,
                execution_time=0,
                exit_code=process.returncode,
                stdout=stdout_str,
                stderr=stderr_str,
                environment_info={"main_file": main_file}
            )
            
        except Exception as e:
            return ExecutionResult(
                status=ExecutionStatus.ENVIRONMENT_ERROR,
                tech_stack=TechnologyStack.PYTHON,
                execution_time=0,
                exit_code=1,
                stdout="",
                stderr=str(e),
                error_message=f"Failed to run Python file: {str(e)}"
            )
    
    async def _execute_nodejs(self) -> ExecutionResult:
        """Execute Node.js code"""
        try:
            # Check if package.json exists and install dependencies
            package_json_path = os.path.join(self.temp_dir, "package.json")
            if os.path.exists(package_json_path):
                print("📦 Installing Node.js dependencies...")
                # Install dependencies
                process = await asyncio.wait_for(
                    asyncio.create_subprocess_exec(
                        "npm", "install",
                        cwd=self.temp_dir,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    ),
                    timeout=60  # 1 minute for npm install
                )
                stdout, stderr = await process.communicate()
                if process.returncode != 0:
                    print(f"⚠️ npm install failed: {stderr.decode()}")
            
            # Look for test files first
            test_files = [f for f in os.listdir(self.temp_dir) if "test" in f.lower() and f.endswith(".js")]
            
            if test_files:
                print(f"🧪 Found test files: {test_files}")
                return await self._run_nodejs_tests()
            else:
                # Look for main file
                main_files = ["app.js", "index.js", "server.js", "main.js"]
                main_file = None
                for candidate in main_files:
                    if os.path.exists(os.path.join(self.temp_dir, candidate)):
                        main_file = candidate
                        break
                
                if main_file:
                    print(f"▶️ Running main file: {main_file}")
                    return await self._run_nodejs_main(main_file)
                else:
                    # Try any .js file
                    js_files = [f for f in os.listdir(self.temp_dir) if f.endswith(".js")]
                    if js_files:
                        print(f"▶️ Running JavaScript file: {js_files[0]}")
                        return await self._run_nodejs_main(js_files[0])
                    else:
                        return ExecutionResult(
                            status=ExecutionStatus.FAILURE,
                            tech_stack=TechnologyStack.NODEJS,
                            execution_time=0,
                            exit_code=1,
                            stdout="",
                            stderr="No Node.js files found to execute",
                            error_message="No executable Node.js files found"
                        )
                    
        except Exception as e:
            return ExecutionResult(
                status=ExecutionStatus.ENVIRONMENT_ERROR,
                tech_stack=TechnologyStack.NODEJS,
                execution_time=0,
                exit_code=1,
                stdout="",
                stderr=str(e),
                error_message=f"Node.js execution error: {str(e)}"
            )
    
    async def _run_nodejs_tests(self) -> ExecutionResult:
        """Run Node.js tests"""
        try:
            # Try npm test first
            print("🔄 Running npm test...")
            process = await asyncio.wait_for(
                asyncio.create_subprocess_exec(
                    "npm", "test",
                    cwd=self.temp_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                ),
                timeout=self.timeout
            )
            
            stdout, stderr = await process.communicate()
            stdout_str = stdout.decode('utf-8', errors='ignore')
            stderr_str = stderr.decode('utf-8', errors='ignore')
            
            # Parse test results
            test_results = TestResultParser.parse_javascript_tests(stdout_str + stderr_str)
            
            return ExecutionResult(
                status=ExecutionStatus.SUCCESS if process.returncode == 0 else ExecutionStatus.FAILURE,
                tech_stack=TechnologyStack.NODEJS,
                execution_time=0,
                exit_code=process.returncode,
                stdout=stdout_str,
                stderr=stderr_str,
                test_results=test_results,
                environment_info={"test_framework": "npm"}
            )
            
        except Exception as e:
            return ExecutionResult(
                status=ExecutionStatus.ENVIRONMENT_ERROR,
                tech_stack=TechnologyStack.NODEJS,
                execution_time=0,
                exit_code=1,
                stdout="",
                stderr=str(e),
                error_message=f"Failed to run Node.js tests: {str(e)}"
            )
    
    async def _run_nodejs_main(self, main_file: str) -> ExecutionResult:
        """Run main Node.js file"""
        try:
            process = await asyncio.wait_for(
                asyncio.create_subprocess_exec(
                    "node", main_file,
                    cwd=self.temp_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                ),
                timeout=self.timeout
            )
            
            stdout, stderr = await process.communicate()
            stdout_str = stdout.decode('utf-8', errors='ignore')
            stderr_str = stderr.decode('utf-8', errors='ignore')
            
            return ExecutionResult(
                status=ExecutionStatus.SUCCESS if process.returncode == 0 else ExecutionStatus.FAILURE,
                tech_stack=TechnologyStack.NODEJS,
                execution_time=0,
                exit_code=process.returncode,
                stdout=stdout_str,
                stderr=stderr_str,
                environment_info={"main_file": main_file}
            )
            
        except Exception as e:
            return ExecutionResult(
                status=ExecutionStatus.ENVIRONMENT_ERROR,
                tech_stack=TechnologyStack.NODEJS,
                execution_time=0,
                exit_code=1,
                stdout="",
                stderr=str(e),
                error_message=f"Failed to run Node.js file: {str(e)}"
            )
    
    async def _execute_generic(self) -> ExecutionResult:
        """Generic execution for unknown tech stacks"""
        return ExecutionResult(
            status=ExecutionStatus.ENVIRONMENT_ERROR,
            tech_stack=TechnologyStack.UNKNOWN,
            execution_time=0,
            exit_code=1,
            stdout="",
            stderr="Unknown technology stack - cannot execute",
            error_message="Technology stack not supported for execution"
        )
    
    async def _cleanup(self):
        """Clean up temporary files"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
                print(f"🧹 Cleaned up temp directory: {self.temp_dir}")
            except Exception as e:
                print(f"⚠️ Warning: Failed to cleanup temp directory {self.temp_dir}: {e}")

# ============================================================================
# MAIN EXECUTOR AGENT
# ============================================================================

async def executor_agent(input: list[Message]) -> AsyncGenerator:
    """Agent responsible for executing code and tests in isolated environments"""
    
    print("🚀 Executor Agent Starting...")
    
    # Extract input content
    input_text = ""
    for message in input:
        for part in message.parts:
            input_text += part.content + "\n"
    
    try:
        # Parse the input to extract files and execution request
        files = await _parse_execution_request(input_text)
        
        if not files:
            yield MessagePart(content="❌ No executable files found in the input. Please provide code files to execute.")
            return
        
        print(f"📁 Found {len(files)} files to execute")
        
        # Detect technology stack
        tech_stack = TechStackDetector.detect_from_files(files)
        print(f"🔍 Detected technology stack: {tech_stack.value}")
        
        # Create executor and run code
        executor = CodeExecutor()
        result = await executor.execute_code(files, tech_stack)
        
        # Format and yield the response
        response = await _format_execution_response(result)
        yield MessagePart(content=response)
        
    except Exception as e:
        print(f"❌ Executor error: {e}")
        error_response = f"""
❌ EXECUTION ERROR

An error occurred while processing the execution request:
{str(e)}

Please check your input format and try again.
"""
        yield MessagePart(content=error_response)

async def _parse_execution_request(input_text: str) -> List[Dict[str, str]]:
    """Parse execution request to extract files"""
    files = []
    
    # Look for FILENAME: pattern (consistent with coder agent output)
    filename_pattern = r'FILENAME:\s*(.+?)\n```(?:\w+)?\n(.*?)\n```'
    matches = re.findall(filename_pattern, input_text, re.DOTALL)
    
    for filename, content in matches:
        files.append({
            "filename": filename.strip(),
            "content": content.strip()
        })
    
    # Alternative: Look for code blocks with filenames in comments
    if not files:
        code_block_pattern = r'```(?:\w+)?\n(?:#\s*(.+?)\n)?(.*?)\n```'
        matches = re.findall(code_block_pattern, input_text, re.DOTALL)
        
        for i, (potential_filename, content) in enumerate(matches):
            filename = potential_filename.strip() if potential_filename else f"code_{i+1}.py"
            if filename and content.strip():
                files.append({
                    "filename": filename,
                    "content": content.strip()
                })
    
    # Fallback: Treat entire input as single file
    if not files and input_text.strip():
        # Try to detect file type from content
        if "def " in input_text or "import " in input_text:
            filename = "main.py"
        elif "const " in input_text or "function " in input_text:
            filename = "main.js"
        else:
            filename = "code.txt"
        
        files.append({
            "filename": filename,
            "content": input_text.strip()
        })
    
    return files

async def _format_execution_response(result: ExecutionResult) -> str:
    """Format execution result into readable response"""
    response = []
    
    # Header with status
    status_emoji = "✅" if result.success else "❌"
    response.append(f"{status_emoji} CODE EXECUTION RESULT")
    response.append("=" * 60)
    response.append(f"📋 Technology Stack: {result.tech_stack.value}")
    response.append(f"⏱️  Execution Time: {result.execution_time:.2f}s")
    response.append(f"🔢 Exit Code: {result.exit_code}")
    response.append(f"📊 Status: {result.status.value}")
    response.append("")
    
    # Test Results Section
    if result.test_results:
        test_summary = result.test_summary
        total_tests = len(result.test_results)
        response.append("🧪 TEST RESULTS")
        response.append("-" * 40)
        response.append(f"📝 Total Tests: {total_tests}")
        response.append(f"✅ Passed: {test_summary['passed']}")
        response.append(f"❌ Failed: {test_summary['failed']}")
        response.append(f"⏭️  Skipped: {test_summary['skipped']}")
        response.append(f"💥 Errors: {test_summary['error']}")
        response.append(f"📊 Pass Rate: {result.test_pass_rate:.1f}%")
        response.append("")
        
        # Individual test results (limit to prevent overwhelming output)
        if len(result.test_results) <= 20:
            response.append("📋 Individual Test Results:")
            for test in result.test_results:
                duration_str = f" ({test.duration:.2f}s)" if test.duration > 0 else ""
                response.append(f"  {test.status_emoji} {test.name}{duration_str}")
                if test.message:
                    response.append(f"    └─ {test.message}")
        response.append("")
    
    # Output Section
    if result.stdout:
        response.append("📤 STDOUT OUTPUT")
        response.append("-" * 40)
        # Truncate very long output
        stdout = result.stdout[:executor_config["max_output_size"]]
        if len(result.stdout) > executor_config["max_output_size"]:
            stdout += "\n... (output truncated)"
        response.append(stdout)
        response.append("")
    
    # Error Section
    if result.stderr or result.error_message:
        response.append("⚠️  ERROR OUTPUT")
        response.append("-" * 40)
        if result.error_message:
            response.append(f"Error: {result.error_message}")
        if result.stderr:
            stderr = result.stderr[:executor_config["max_output_size"]]
            if len(result.stderr) > executor_config["max_output_size"]:
                stderr += "\n... (error output truncated)"
            response.append(stderr)
        response.append("")
    
    # Environment Info
    if result.environment_info:
        response.append("🔧 ENVIRONMENT INFO")
        response.append("-" * 40)
        for key, value in result.environment_info.items():
            response.append(f"• {key}: {value}")
        response.append("")
    
    # Summary and Recommendations
    response.append("🎯 EXECUTION SUMMARY")
    response.append("-" * 40)
    if result.success:
        if result.test_results:
            response.append(f"✅ Code executed successfully with {result.test_pass_rate:.1f}% test pass rate")
        else:
            response.append("✅ Code executed successfully")
        
        if result.test_results and result.test_summary["failed"] > 0:
            response.append("⚠️  Some tests failed - review test results above")
    else:
        if result.status == ExecutionStatus.TIMEOUT:
            response.append(f"⏰ Execution timed out after {result.execution_time:.1f}s")
            response.append("💡 Consider optimizing code performance or increasing timeout")
        elif result.status == ExecutionStatus.ENVIRONMENT_ERROR:
            response.append("🔧 Environment setup failed")
            response.append("💡 Check dependencies and system requirements")
        else:
            response.append("❌ Code execution failed")
            if result.test_results and result.test_summary["failed"] > 0:
                response.append("💡 Review failed tests and fix implementation")
            else:
                response.append("💡 Check error output and fix syntax/runtime issues")
    
    return "\n".join(response)