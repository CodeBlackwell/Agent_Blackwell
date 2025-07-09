"""
Test Fixtures and Utilities for Live Testing
Provides helper functions and data generators for test execution
"""

import asyncio
import json
import os
import random
import string
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, AsyncGenerator
import docker
import shutil


class TestDataGenerator:
    """Generate test data for various scenarios"""
    
    @staticmethod
    def generate_random_string(length: int = 10, chars: str = None) -> str:
        """Generate random string
        
        Args:
            length: String length
            chars: Character set to use
            
        Returns:
            Random string
        """
        if chars is None:
            chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(length))
    
    @staticmethod
    def generate_test_requirements(complexity: str = "simple") -> str:
        """Generate test requirements based on complexity
        
        Args:
            complexity: simple, moderate, or complex
            
        Returns:
            Requirements string
        """
        templates = {
            "simple": [
                "Create a function that {operation} two numbers",
                "Build a class that manages a {data_structure}",
                "Implement a utility that {string_operation} strings"
            ],
            "moderate": [
                "Create a REST API for managing {resource} with CRUD operations",
                "Build a data processing pipeline that {data_operation}",
                "Implement a {algorithm} algorithm with proper error handling"
            ],
            "complex": [
                "Design a microservice architecture for {domain} with {features}",
                "Create a distributed system that handles {distributed_feature}",
                "Build a full-stack application with {frontend} and {backend}"
            ]
        }
        
        # Select template and fill placeholders
        template = random.choice(templates.get(complexity, templates["simple"]))
        
        placeholders = {
            "operation": random.choice(["adds", "multiplies", "divides"]),
            "data_structure": random.choice(["list", "queue", "stack"]),
            "string_operation": random.choice(["reverses", "validates", "transforms"]),
            "resource": random.choice(["users", "products", "orders"]),
            "data_operation": random.choice(["filters CSV files", "aggregates JSON data", "transforms XML"]),
            "algorithm": random.choice(["sorting", "searching", "graph traversal"]),
            "domain": random.choice(["e-commerce", "social media", "banking"]),
            "features": random.choice(["authentication and caching", "real-time updates", "payment processing"]),
            "distributed_feature": random.choice(["consensus", "sharding", "replication"]),
            "frontend": random.choice(["React", "Vue", "Angular"]),
            "backend": random.choice(["FastAPI", "Django", "Flask"])
        }
        
        for key, value in placeholders.items():
            template = template.replace(f"{{{key}}}", value)
            
        return template
    
    @staticmethod
    def generate_test_files(num_files: int = 3) -> Dict[str, str]:
        """Generate test file contents
        
        Args:
            num_files: Number of files to generate
            
        Returns:
            Dictionary of filename to content
        """
        files = {}
        
        for i in range(num_files):
            filename = f"test_file_{i}.py"
            content = f'''"""
Test file {i} generated for testing
"""

def function_{i}(x, y):
    """Test function {i}"""
    return x + y

class TestClass_{i}:
    """Test class {i}"""
    
    def __init__(self):
        self.value = {i}
        
    def method(self):
        return self.value * 2
'''
            files[filename] = content
            
        return files
    
    @staticmethod
    def generate_csv_data(rows: int = 100, columns: List[str] = None) -> str:
        """Generate CSV test data
        
        Args:
            rows: Number of rows
            columns: Column names
            
        Returns:
            CSV content
        """
        if columns is None:
            columns = ["id", "name", "value", "timestamp"]
            
        lines = [",".join(columns)]
        
        for i in range(rows):
            row = []
            for col in columns:
                if col == "id":
                    row.append(str(i + 1))
                elif col == "name":
                    row.append(f"Item_{i}")
                elif col == "value":
                    row.append(str(random.uniform(0, 100)))
                elif col == "timestamp":
                    date = datetime.now() - timedelta(days=random.randint(0, 30))
                    row.append(date.isoformat())
                else:
                    row.append(TestDataGenerator.generate_random_string(5))
                    
            lines.append(",".join(row))
            
        return "\n".join(lines)
    
    @staticmethod
    def generate_json_data(depth: int = 3, width: int = 4) -> Dict[str, Any]:
        """Generate nested JSON test data
        
        Args:
            depth: Nesting depth
            width: Number of keys per level
            
        Returns:
            JSON data structure
        """
        if depth == 0:
            return {
                "value": random.choice([
                    random.randint(0, 100),
                    TestDataGenerator.generate_random_string(10),
                    random.choice([True, False]),
                    None
                ])
            }
            
        data = {}
        for i in range(width):
            key = f"key_{i}"
            if random.random() < 0.7:  # 70% chance of nesting
                data[key] = TestDataGenerator.generate_json_data(depth - 1, width)
            else:
                data[key] = {
                    "id": i,
                    "name": TestDataGenerator.generate_random_string(8),
                    "values": [random.randint(0, 10) for _ in range(5)]
                }
                
        return data


class DockerTestEnvironment:
    """Manages Docker containers for testing"""
    
    def __init__(self, client: docker.DockerClient = None):
        """Initialize Docker environment
        
        Args:
            client: Docker client instance
        """
        self.client = client or docker.from_env()
        self.containers = []
        
    async def create_python_container(self, 
                                    code_dir: Path,
                                    image: str = "python:3.9-slim",
                                    requirements: List[str] = None) -> docker.models.containers.Container:
        """Create Python test container
        
        Args:
            code_dir: Directory with code to test
            image: Docker image to use
            requirements: Python packages to install
            
        Returns:
            Docker container instance
        """
        # Create Dockerfile if requirements exist
        if requirements:
            dockerfile_content = f'''FROM {image}
WORKDIR /app
RUN pip install {' '.join(requirements)}
COPY . /app/
'''
            dockerfile_path = code_dir / "Dockerfile"
            with open(dockerfile_path, "w") as f:
                f.write(dockerfile_content)
                
        # Create container
        container = self.client.containers.create(
            image,
            command="sleep 3600",  # Keep alive for tests
            volumes={str(code_dir): {"bind": "/app", "mode": "rw"}},
            working_dir="/app",
            detach=True
        )
        
        self.containers.append(container)
        container.start()
        
        return container
        
    async def run_test_command(self, 
                             container: docker.models.containers.Container,
                             command: str,
                             timeout: int = 60) -> Tuple[int, str]:
        """Run command in container
        
        Args:
            container: Docker container
            command: Command to execute
            timeout: Execution timeout
            
        Returns:
            Exit code and output
        """
        try:
            result = container.exec_run(command, timeout=timeout)
            return result.exit_code, result.output.decode()
        except Exception as e:
            return 1, str(e)
            
    async def cleanup(self):
        """Clean up all containers"""
        for container in self.containers:
            try:
                container.stop(timeout=5)
                container.remove()
            except:
                pass
        self.containers.clear()


class WorkflowTestHelper:
    """Helper for testing workflows"""
    
    @staticmethod
    async def create_test_session(base_dir: Path = None) -> Path:
        """Create test session directory
        
        Args:
            base_dir: Base directory for sessions
            
        Returns:
            Session directory path
        """
        if base_dir is None:
            base_dir = Path("tests/outputs/live_tests")
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        session_dir = base_dir / f"session_{timestamp}"
        session_dir.mkdir(parents=True, exist_ok=True)
        
        return session_dir
        
    @staticmethod
    async def capture_workflow_output(workflow_coro) -> Dict[str, Any]:
        """Capture all output from workflow execution
        
        Args:
            workflow_coro: Workflow coroutine
            
        Returns:
            Captured output and metadata
        """
        start_time = datetime.now()
        outputs = []
        errors = []
        
        try:
            # Run workflow and capture result
            result = await workflow_coro
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            return {
                "success": True,
                "result": result,
                "outputs": outputs,
                "errors": errors,
                "duration": duration,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            }
            
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            return {
                "success": False,
                "result": None,
                "outputs": outputs,
                "errors": errors + [str(e)],
                "duration": duration,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "exception": str(e)
            }
            
    @staticmethod
    def validate_generated_code(code_dir: Path, expected_files: List[str]) -> Dict[str, Any]:
        """Validate generated code structure
        
        Args:
            code_dir: Directory with generated code
            expected_files: List of expected file paths
            
        Returns:
            Validation results
        """
        results = {
            "all_files_exist": True,
            "missing_files": [],
            "extra_files": [],
            "file_sizes": {},
            "total_lines": 0
        }
        
        # Check expected files
        for expected in expected_files:
            file_path = code_dir / expected
            if not file_path.exists():
                results["all_files_exist"] = False
                results["missing_files"].append(expected)
            else:
                # Get file stats
                size = file_path.stat().st_size
                results["file_sizes"][expected] = size
                
                # Count lines
                try:
                    with open(file_path, "r") as f:
                        lines = len(f.readlines())
                        results["total_lines"] += lines
                except:
                    pass
                    
        # Check for extra files
        actual_files = set()
        for file_path in code_dir.rglob("*.py"):
            relative = file_path.relative_to(code_dir)
            actual_files.add(str(relative))
            
        expected_set = set(expected_files)
        extra = actual_files - expected_set
        results["extra_files"] = list(extra)
        
        return results
        
    @staticmethod
    async def run_integration_test(test_func, *args, **kwargs) -> Dict[str, Any]:
        """Run integration test with proper error handling
        
        Args:
            test_func: Test function to run
            *args: Test function arguments
            **kwargs: Test function keyword arguments
            
        Returns:
            Test results
        """
        try:
            result = await test_func(*args, **kwargs)
            return {
                "success": True,
                "result": result,
                "error": None
            }
        except AssertionError as e:
            return {
                "success": False,
                "result": None,
                "error": f"Assertion failed: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "result": None,
                "error": f"Test error: {type(e).__name__}: {str(e)}"
            }


class PerformanceMonitor:
    """Monitor performance during tests"""
    
    def __init__(self):
        """Initialize performance monitor"""
        self.metrics = {
            "start_time": None,
            "end_time": None,
            "checkpoints": [],
            "resource_usage": []
        }
        
    def start(self):
        """Start monitoring"""
        self.metrics["start_time"] = datetime.now()
        
    def checkpoint(self, name: str, metadata: Dict[str, Any] = None):
        """Record performance checkpoint
        
        Args:
            name: Checkpoint name
            metadata: Additional metadata
        """
        checkpoint = {
            "name": name,
            "timestamp": datetime.now(),
            "metadata": metadata or {}
        }
        
        if self.metrics["start_time"]:
            elapsed = (checkpoint["timestamp"] - self.metrics["start_time"]).total_seconds()
            checkpoint["elapsed_seconds"] = elapsed
            
        self.metrics["checkpoints"].append(checkpoint)
        
    def stop(self) -> Dict[str, Any]:
        """Stop monitoring and return metrics
        
        Returns:
            Complete performance metrics
        """
        self.metrics["end_time"] = datetime.now()
        
        if self.metrics["start_time"] and self.metrics["end_time"]:
            total_duration = (self.metrics["end_time"] - self.metrics["start_time"]).total_seconds()
            self.metrics["total_duration_seconds"] = total_duration
            
        return self.metrics.copy()
        
    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary
        
        Returns:
            Summary statistics
        """
        summary = {
            "total_checkpoints": len(self.metrics["checkpoints"]),
            "duration": self.metrics.get("total_duration_seconds", 0)
        }
        
        # Calculate checkpoint durations
        if len(self.metrics["checkpoints"]) > 1:
            durations = []
            for i in range(1, len(self.metrics["checkpoints"])):
                prev = self.metrics["checkpoints"][i-1]["timestamp"]
                curr = self.metrics["checkpoints"][i]["timestamp"]
                duration = (curr - prev).total_seconds()
                durations.append(duration)
                
            summary["avg_checkpoint_duration"] = sum(durations) / len(durations)
            summary["max_checkpoint_duration"] = max(durations)
            summary["min_checkpoint_duration"] = min(durations)
            
        return summary


# Fixture instances for easy access
data_generator = TestDataGenerator()
docker_env = DockerTestEnvironment()
workflow_helper = WorkflowTestHelper()
perf_monitor = PerformanceMonitor()