"""
Integration tests for executor agent in different workflows.
"""
import os
import asyncio
import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add the project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import modules to test
from shared.data_models import TeamMember, CodingTeamInput
from workflows.workflow_manager import execute_workflow
from workflows.monitoring import WorkflowExecutionTracer

class ExecutorIntegrationTest(unittest.TestCase):
    """Test the integration of the executor agent in workflows."""
    
    async def test_tdd_workflow_executor_integration(self):
        """Test executor integration in the TDD workflow."""
        # Setup tracer for monitoring
        tracer = WorkflowExecutionTracer(
            workflow_type="TDD",
            execution_id="test_tdd_executor_integration"
        )
        
        # Create test input with executor in team_members
        input_data = CodingTeamInput(
            requirements="Create a simple calculator function that adds two numbers.",
            workflow_type="tdd",
            team_members=[
                TeamMember.planner,
                TeamMember.designer,
                TeamMember.test_writer,
                TeamMember.coder,
                TeamMember.executor,  # Include executor
                TeamMember.reviewer
            ],
            max_retries=1,  # Keep it minimal for testing
            timeout_seconds=300
        )
        
        # Execute the workflow
        results, report = await execute_workflow(input_data, tracer)
        
        # Verify executor was called
        executor_result = None
        for result in results:
            if result.team_member == TeamMember.executor:
                executor_result = result
                break
        
        # Assert executor produced results
        self.assertIsNotNone(executor_result, "Executor agent was not called in TDD workflow")
        self.assertIn("SESSION_ID", executor_result.output, "Executor output should contain session ID")
        
        # Verify execution steps in trace report
        execution_steps = [step for step in report.steps if step.agent_name == "executor_agent"]
        self.assertTrue(len(execution_steps) > 0, "No execution steps found in workflow trace")
    
    async def test_full_workflow_executor_integration(self):
        """Test executor integration in the Full workflow."""
        # Setup tracer for monitoring
        tracer = WorkflowExecutionTracer(
            workflow_type="Full",
            execution_id="test_full_executor_integration"
        )
        
        # Create test input with executor in team_members
        input_data = CodingTeamInput(
            requirements="Create a simple todo list API with Express.",
            workflow_type="full",
            team_members=[
                TeamMember.planner,
                TeamMember.designer,
                TeamMember.coder,
                TeamMember.executor,  # Include executor
                TeamMember.reviewer
            ],
            max_retries=1,  # Keep it minimal for testing
            timeout_seconds=300
        )
        
        # Execute the workflow
        results, report = await execute_workflow(input_data, tracer)
        
        # Verify executor was called
        executor_result = None
        for result in results:
            if result.team_member == TeamMember.executor:
                executor_result = result
                break
        
        # Assert executor produced results
        self.assertIsNotNone(executor_result, "Executor agent was not called in Full workflow")
        self.assertIn("SESSION_ID", executor_result.output, "Executor output should contain session ID")
        
        # Verify execution steps in trace report
        execution_steps = [step for step in report.steps if step.agent_name == "executor_agent"]
        self.assertTrue(len(execution_steps) > 0, "No execution steps found in workflow trace")
    
    async def test_individual_executor_workflow(self):
        """Test individual workflow with executor step."""
        # Setup tracer for monitoring
        tracer = WorkflowExecutionTracer(
            workflow_type="Individual",
            execution_id="test_individual_executor"
        )
        
        # Sample code to execute
        sample_code = """
def add(a, b):
    return a + b

# Test the function
result = add(5, 7)
print(f"Result: {result}")
"""
        
        # Create test input for individual executor workflow
        input_data = CodingTeamInput(
            requirements=f"Execute this code:\n\n{sample_code}",
            workflow_type="execution",  # Executor individual step
            step_type="execution",
            team_members=[TeamMember.executor],
            max_retries=1,
            timeout_seconds=120
        )
        
        # Execute the workflow
        results, report = await execute_workflow(input_data, tracer)
        
        # Verify results
        self.assertEqual(len(results), 1, "Expected exactly one result")
        self.assertEqual(results[0].team_member, TeamMember.executor, "Result should be from executor agent")
        self.assertIn("SESSION_ID", results[0].output, "Executor output should contain session ID")
        
        # Check if execution contained the print output
        self.assertIn("Result: 12", results[0].output, "Execution output should contain the expected result")


# Run tests when module is executed directly
if __name__ == "__main__":
    # Run the async tests with asyncio
    test_loader = unittest.TestLoader()
    test_suite = test_loader.loadTestsFromTestCase(ExecutorIntegrationTest)
    
    # Create a loop and run the tests
    loop = asyncio.get_event_loop()
    for test in test_suite:
        loop.run_until_complete(test)
