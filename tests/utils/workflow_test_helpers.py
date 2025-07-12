"""
Test helper utilities for workflow testing.
"""
import asyncio
import time
from typing import Dict, Any, List, Callable, Optional
from contextlib import contextmanager
from unittest.mock import Mock, patch
import json
from pathlib import Path

from workflows.monitoring import WorkflowExecutionTracer, WorkflowExecutionReport
from shared.data_models import TeamMemberResult


class WorkflowTestHelper:
    """Helper class for workflow testing."""
    
    @staticmethod
    async def run_workflow_with_mocks(
        workflow_func: Callable,
        input_data: Any,
        agent_mocks: Dict[str, Any]
    ) -> tuple:
        """Run a workflow with mocked agent responses."""
        async def mock_agent_runner(agent_name, requirements, context):
            if agent_name in agent_mocks:
                response = agent_mocks[agent_name]
                if isinstance(response, Exception):
                    raise response
                return response
            return {"content": f"Default mock for {agent_name}", "success": True}
        
        with patch('core.migration.run_team_member_with_tracking', side_effect=mock_agent_runner):
            return await workflow_func(input_data)
    
    @staticmethod
    def verify_workflow_report(report: WorkflowExecutionReport, expected: Dict[str, Any]):
        """Verify workflow execution report matches expectations."""
        report_dict = report.to_dict() if hasattr(report, 'to_dict') else {}
        
        # Check workflow type
        if "workflow_type" in expected:
            assert report_dict.get("workflow_type") == expected["workflow_type"]
        
        # Check execution status
        if "status" in expected:
            assert report_dict.get("status") == expected["status"]
        
        # Check step count
        if "step_count" in expected:
            steps = report_dict.get("steps", [])
            assert len(steps) == expected["step_count"]
        
        # Check for errors
        if "has_errors" in expected:
            errors = report_dict.get("errors", [])
            assert bool(errors) == expected["has_errors"]
    
    @staticmethod
    def create_performance_benchmark(name: str):
        """Create a performance benchmark context manager."""
        return PerformanceBenchmark(name)
    
    @staticmethod
    async def simulate_slow_agent(delay: float, response: Any):
        """Simulate a slow agent response."""
        await asyncio.sleep(delay)
        return response
    
    @staticmethod
    def assert_agent_called(mock_runner, agent_name: str, times: int = 1):
        """Assert an agent was called the expected number of times."""
        calls = [call for call in mock_runner.call_args_list 
                if call[0][0] == agent_name]
        assert len(calls) == times, f"{agent_name} was called {len(calls)} times, expected {times}"
    
    @staticmethod
    def extract_code_from_output(output: str) -> List[str]:
        """Extract code blocks from agent output."""
        code_blocks = []
        lines = output.split('\n')
        in_code_block = False
        current_block = []
        
        for line in lines:
            if line.strip().startswith('```'):
                if in_code_block:
                    code_blocks.append('\n'.join(current_block))
                    current_block = []
                in_code_block = not in_code_block
            elif in_code_block:
                current_block.append(line)
        
        return code_blocks
    
    @staticmethod
    def save_test_artifact(content: Any, filename: str, test_dir: Path):
        """Save test artifacts for debugging."""
        artifact_dir = test_dir / "artifacts"
        artifact_dir.mkdir(exist_ok=True)
        
        file_path = artifact_dir / filename
        
        if isinstance(content, (dict, list)):
            file_path.write_text(json.dumps(content, indent=2))
        else:
            file_path.write_text(str(content))
        
        return file_path


class PerformanceBenchmark:
    """Context manager for performance benchmarking."""
    
    def __init__(self, name: str):
        self.name = name
        self.start_time = None
        self.end_time = None
        self.duration = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        print(f"\nPerformance: {self.name} took {self.duration:.3f} seconds")
    
    def assert_faster_than(self, max_duration: float):
        """Assert the operation completed within the time limit."""
        assert self.duration is not None, "Benchmark not completed"
        assert self.duration < max_duration, \
            f"{self.name} took {self.duration:.3f}s, exceeding limit of {max_duration}s"


class MockTracer:
    """Mock implementation of WorkflowExecutionTracer for testing."""
    
    def __init__(self, workflow_type: str = "test"):
        self.workflow_type = workflow_type
        self.execution_id = f"test_{int(time.time())}"
        self.steps = []
        self.current_step = None
        self.start_time = time.time()
        self.end_time = None
        self.error = None
    
    def start_step(self, step_name: str, agent_name: str, input_data: Dict[str, Any]) -> str:
        """Start a workflow step."""
        step_id = f"step_{len(self.steps)}"
        step = {
            "id": step_id,
            "name": step_name,
            "agent": agent_name,
            "input": input_data,
            "start_time": time.time(),
            "status": "running"
        }
        self.steps.append(step)
        self.current_step = step
        return step_id
    
    def complete_step(self, step_id: str, output_data: Dict[str, Any] = None, error: str = None):
        """Complete a workflow step."""
        step = next((s for s in self.steps if s["id"] == step_id), None)
        if step:
            step["end_time"] = time.time()
            step["duration"] = step["end_time"] - step["start_time"]
            
            if error:
                step["status"] = "failed"
                step["error"] = error
            else:
                step["status"] = "completed"
                step["output"] = output_data
    
    def complete_execution(self, final_output: Dict[str, Any] = None, error: str = None):
        """Complete workflow execution."""
        self.end_time = time.time()
        if error:
            self.error = error
        else:
            self.final_output = final_output
    
    def get_report(self) -> Dict[str, Any]:
        """Get execution report."""
        duration = (self.end_time or time.time()) - self.start_time
        
        return {
            "workflow_type": self.workflow_type,
            "execution_id": self.execution_id,
            "duration": duration,
            "steps": self.steps,
            "error": self.error,
            "status": "failed" if self.error else "completed"
        }
    
    def get_duration(self) -> float:
        """Get execution duration."""
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time


def create_mock_workflow_manager(available_workflows: List[str] = None):
    """Create a mock workflow manager for testing."""
    if available_workflows is None:
        available_workflows = ["individual", "tdd", "full", "incremental"]
    
    mock = Mock()
    mock.get_available_workflows.return_value = available_workflows
    mock.execute_workflow = AsyncMock()
    
    return mock


@contextmanager
def capture_logs(logger_name: str = None):
    """Context manager to capture log messages during tests."""
    import logging
    from io import StringIO
    
    # Create string buffer and handler
    log_buffer = StringIO()
    handler = logging.StreamHandler(log_buffer)
    handler.setLevel(logging.DEBUG)
    
    # Get logger
    logger = logging.getLogger(logger_name) if logger_name else logging.getLogger()
    original_level = logger.level
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    
    try:
        yield log_buffer
    finally:
        logger.removeHandler(handler)
        logger.setLevel(original_level)


def assert_workflow_metrics(metrics: Dict[str, Any], expectations: Dict[str, Any]):
    """Assert workflow metrics meet expectations."""
    # Check duration
    if "max_duration" in expectations:
        assert metrics.get("duration", float('inf')) <= expectations["max_duration"]
    
    # Check step count
    if "step_count" in expectations:
        assert metrics.get("step_count", 0) == expectations["step_count"]
    
    # Check success rate
    if "min_success_rate" in expectations:
        total_steps = metrics.get("step_count", 0)
        successful_steps = metrics.get("successful_steps", 0)
        success_rate = successful_steps / total_steps if total_steps > 0 else 0
        assert success_rate >= expectations["min_success_rate"]