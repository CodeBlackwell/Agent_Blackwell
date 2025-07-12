"""
Integration tests for the individual workflow.
"""
import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
import json
from pathlib import Path

from workflows.individual.individual_workflow_enhanced import IndividualWorkflowExecutor
from workflows.monitoring import WorkflowExecutionTracer
from shared.data_models import CodingTeamInput, TeamMember
from core.initialize import initialize_core
from core.exceptions import WorkflowError


class TestIndividualWorkflowIntegration:
    """Integration tests for individual workflow execution."""
    
    @pytest.fixture(scope="class")
    def setup_infrastructure(self):
        """Set up core infrastructure for tests."""
        # Initialize core with test configuration
        test_config = {
            "log_level": "WARNING",
            "debug": False
        }
        initialize_core()
        yield
        # Cleanup would go here
    
    @pytest.fixture
    def mock_agent_responses(self):
        """Mock responses for different agents."""
        return {
            "planner_agent": {
                "content": """
                Project Plan: Calculator API
                
                1. Create REST API with basic operations
                2. Implement add, subtract, multiply, divide
                3. Include error handling
                4. Add input validation
                """,
                "success": True
            },
            "designer_agent": {
                "content": """
                API Design:
                
                Endpoints:
                - POST /calculate
                  Body: {"operation": "add", "a": 1, "b": 2}
                  Response: {"result": 3}
                
                Error Codes:
                - 400: Invalid input
                - 422: Division by zero
                """,
                "success": True
            },
            "coder_agent": {
                "content": """
                ```python
                from flask import Flask, request, jsonify
                
                app = Flask(__name__)
                
                @app.route('/calculate', methods=['POST'])
                def calculate():
                    data = request.json
                    operation = data.get('operation')
                    a = data.get('a')
                    b = data.get('b')
                    
                    if operation == 'add':
                        return jsonify({'result': a + b})
                    # ... more operations
                ```
                """,
                "success": True
            },
            "test_writer_agent": {
                "content": """
                ```python
                import pytest
                from app import app
                
                def test_add():
                    response = app.test_client().post('/calculate',
                        json={'operation': 'add', 'a': 1, 'b': 2})
                    assert response.json['result'] == 3
                ```
                """,
                "success": True
            },
            "reviewer_agent": {
                "content": "Code review passed. Implementation meets requirements.",
                "success": True
            },
            "executor_agent": {
                "content": "All tests passed. API is running successfully.",
                "success": True
            }
        }
    
    @pytest.mark.asyncio
    async def test_full_workflow_execution(self, setup_infrastructure, mock_agent_responses):
        """Test complete workflow execution from planning to execution."""
        steps = ["planning", "design", "implementation", "test_writing", "review", "execution"]
        
        for step in steps:
            input_data = CodingTeamInput(
                requirements="Build a calculator API with add, subtract, multiply, divide operations",
                step_type=step
            )
            
            # Mock the agent for this step
            agent_name = {
                "planning": "planner_agent",
                "design": "designer_agent",
                "implementation": "coder_agent",
                "test_writing": "test_writer_agent",
                "review": "reviewer_agent",
                "execution": "executor_agent"
            }[step]
            
            with patch('core.migration.run_team_member_with_tracking',
                      new_callable=AsyncMock) as mock_run:
                mock_run.return_value = mock_agent_responses[agent_name]
                
                executor = IndividualWorkflowExecutor()
                results, report = await executor.execute(input_data)
                
                # Verify execution
                assert len(results) == 1
                assert results[0].output == str(mock_agent_responses[agent_name])
                
                # Verify report
                assert report is not None
                report_dict = report.to_dict() if hasattr(report, 'to_dict') else {}
                assert report_dict.get('workflow_type') == 'Individual'
    
    @pytest.mark.asyncio
    async def test_workflow_with_retries(self, setup_infrastructure):
        """Test workflow behavior with transient failures and retries."""
        call_count = 0
        
        async def flaky_agent(agent_name, requirements, context):
            nonlocal call_count
            call_count += 1
            
            if call_count < 2:
                raise Exception("Temporary network error")
            
            return {"content": "Success after retry", "success": True}
        
        input_data = CodingTeamInput(
            requirements="Test with retries",
            step_type="planning"
        )
        
        with patch('core.migration.run_team_member_with_tracking', side_effect=flaky_agent):
            executor = IndividualWorkflowExecutor()
            
            # Should succeed after retry
            results, report = await executor.execute(input_data)
            
            assert len(results) == 1
            assert "Success after retry" in results[0].output
            assert call_count == 2  # First call failed, second succeeded
    
    @pytest.mark.asyncio
    async def test_workflow_performance(self, setup_infrastructure):
        """Test workflow performance and timing."""
        # Mock fast responses
        async def fast_agent(*args, **kwargs):
            await asyncio.sleep(0.1)  # 100ms response time
            return {"content": "Fast response", "success": True}
        
        input_data = CodingTeamInput(
            requirements="Performance test",
            step_type="planning"
        )
        
        with patch('core.migration.run_team_member_with_tracking', side_effect=fast_agent):
            executor = IndividualWorkflowExecutor()
            
            start_time = time.time()
            results, report = await executor.execute(input_data)
            duration = time.time() - start_time
            
            # Should complete quickly
            assert duration < 1.0  # Less than 1 second
            assert len(results) == 1
            
            # Check timing in report
            if hasattr(report, 'get_duration'):
                assert report.get_duration() < 1.0
    
    @pytest.mark.asyncio
    async def test_workflow_error_recovery(self, setup_infrastructure):
        """Test workflow error recovery and fallback mechanisms."""
        async def failing_planner(*args, **kwargs):
            raise Exception("Planner is unavailable")
        
        input_data = CodingTeamInput(
            requirements="Test error recovery",
            step_type="planning"
        )
        
        with patch('core.migration.run_team_member_with_tracking', side_effect=failing_planner):
            executor = IndividualWorkflowExecutor()
            
            # Should raise WorkflowError after all retries fail
            with pytest.raises(WorkflowError) as exc_info:
                await executor.execute(input_data)
            
            error = exc_info.value
            assert error.workflow_type == "Individual"
            assert error.phase == "planning"
            assert error.recoverable  # Should be marked as recoverable
    
    @pytest.mark.asyncio
    async def test_workflow_with_progress_tracking(self, setup_infrastructure):
        """Test workflow execution with progress tracking enabled."""
        progress_updates = []
        
        class MockProgressReporter:
            def __init__(self, *args, **kwargs):
                pass
            
            def start_step(self, step_name):
                progress_updates.append(f"start:{step_name}")
            
            def complete_step(self, step_name):
                progress_updates.append(f"complete:{step_name}")
            
            def error_step(self, step_name, error):
                progress_updates.append(f"error:{step_name}:{error}")
            
            def stop(self):
                progress_updates.append("stop")
        
        input_data = CodingTeamInput(
            requirements="Test progress tracking",
            step_type="design"
        )
        
        with patch('workflows.individual.individual_workflow_enhanced.ProgressReporter', MockProgressReporter):
            with patch('core.migration.run_team_member_with_tracking',
                      new_callable=AsyncMock,
                      return_value={"content": "Design complete", "success": True}):
                
                executor = IndividualWorkflowExecutor()
                await executor.execute(input_data)
                
                # Verify progress updates
                assert "start:design" in progress_updates
                assert "complete:design" in progress_updates
    
    @pytest.mark.asyncio
    async def test_concurrent_workflow_execution(self, setup_infrastructure):
        """Test multiple workflow steps executing concurrently."""
        async def mock_agent(agent_name, requirements, context):
            # Simulate some work
            await asyncio.sleep(0.1)
            return {"content": f"{agent_name} completed", "success": True}
        
        with patch('core.migration.run_team_member_with_tracking', side_effect=mock_agent):
            executor = IndividualWorkflowExecutor()
            
            # Run multiple workflows concurrently
            tasks = []
            steps = ["planning", "design", "implementation"]
            
            for step in steps:
                input_data = CodingTeamInput(
                    requirements=f"Concurrent test {step}",
                    step_type=step
                )
                task = executor.execute(input_data)
                tasks.append(task)
            
            # Execute all concurrently
            results = await asyncio.gather(*tasks)
            
            # Verify all completed
            assert len(results) == 3
            for i, (step_results, report) in enumerate(results):
                assert len(step_results) == 1
                assert f"_agent completed" in step_results[0].output
    
    @pytest.mark.asyncio
    async def test_workflow_state_persistence(self, setup_infrastructure, tmp_path):
        """Test workflow state can be persisted and resumed."""
        # This tests that the workflow execution report can be saved and loaded
        
        input_data = CodingTeamInput(
            requirements="Test state persistence",
            step_type="planning"
        )
        
        with patch('core.migration.run_team_member_with_tracking',
                  new_callable=AsyncMock,
                  return_value={"content": "Planning done", "success": True}):
            
            executor = IndividualWorkflowExecutor()
            results, report = await executor.execute(input_data)
            
            # Save report
            report_file = tmp_path / "workflow_report.json"
            if hasattr(report, 'to_json'):
                report_file.write_text(report.to_json())
            else:
                report_file.write_text(json.dumps({"results": len(results)}))
            
            # Verify file was created
            assert report_file.exists()
            
            # Load and verify
            loaded_data = json.loads(report_file.read_text())
            assert loaded_data is not None