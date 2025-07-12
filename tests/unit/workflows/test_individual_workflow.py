"""
Unit tests for the individual workflow implementation.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime

from workflows.individual.individual_workflow_enhanced import IndividualWorkflowExecutor
from workflows.monitoring import WorkflowExecutionTracer
from shared.data_models import CodingTeamInput, TeamMemberResult, TeamMember
from core.exceptions import (
    WorkflowError, AgentTimeoutError, AgentError,
    ValidationError
)


class TestIndividualWorkflowExecutor:
    """Test cases for IndividualWorkflowExecutor."""
    
    @pytest.fixture
    def executor(self):
        """Create a test executor instance."""
        with patch('workflows.individual.individual_workflow_enhanced.get_config_manager'):
            executor = IndividualWorkflowExecutor()
            # Mock configuration
            executor.workflow_config = {
                "timeout": 600,
                "max_retries": 3,
                "steps": {
                    "planning": {"timeout": 300, "retries": 2},
                    "design": {"timeout": 300, "retries": 2},
                    "implementation": {"timeout": 360, "retries": 3}
                },
                "progress": {
                    "show_step_progress": True,
                    "show_eta": True
                }
            }
            return executor
    
    @pytest.fixture
    def mock_input_data(self):
        """Create mock input data."""
        return CodingTeamInput(
            requirements="Build a calculator API",
            workflow_type="individual",
            step_type="planning"
        )
    
    @pytest.fixture
    def mock_tracer(self):
        """Create a mock tracer."""
        tracer = Mock(spec=WorkflowExecutionTracer)
        tracer.execution_id = "test_execution_123"
        tracer.start_step = Mock(return_value="step_123")
        tracer.complete_step = Mock()
        tracer.complete_execution = Mock()
        tracer.get_report = Mock(return_value=Mock())
        tracer.get_duration = Mock(return_value=10.5)
        return tracer
    
    @pytest.mark.asyncio
    async def test_execute_planning_step_success(self, executor, mock_input_data, mock_tracer):
        """Test successful execution of planning step."""
        # Mock the agent runner
        mock_result = {
            "content": "Planning completed successfully",
            "messages": [],
            "success": True
        }
        
        with patch('workflows.individual.individual_workflow_enhanced.run_team_member_with_tracking',
                  new_callable=AsyncMock) as mock_run:
            mock_run.return_value = mock_result
            
            # Execute
            results, report = await executor.execute(mock_input_data, mock_tracer)
            
            # Verify
            assert len(results) == 1
            assert results[0].team_member == TeamMember.planner
            assert results[0].name == "planner"
            assert str(mock_result) in results[0].output
            
            # Verify tracer calls
            mock_tracer.start_step.assert_called_once()
            mock_tracer.complete_step.assert_called_once()
            mock_tracer.complete_execution.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_with_timeout(self, executor, mock_input_data, mock_tracer):
        """Test execution with timeout."""
        # Make the agent call take too long
        async def slow_agent(*args, **kwargs):
            await asyncio.sleep(10)  # Longer than timeout
            
        mock_input_data.step_type = "planning"
        executor.workflow_config["steps"]["planning"]["timeout"] = 0.1  # 100ms timeout
        
        with patch('workflows.individual.individual_workflow_enhanced.run_team_member_with_tracking',
                  side_effect=slow_agent):
            
            # Should raise timeout error
            with pytest.raises(WorkflowError) as exc_info:
                await executor.execute(mock_input_data, mock_tracer)
            
            assert "timeout" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_execute_with_agent_error(self, executor, mock_input_data, mock_tracer):
        """Test execution when agent fails."""
        with patch('workflows.individual.individual_workflow_enhanced.run_team_member_with_tracking',
                  side_effect=Exception("Agent failed")):
            
            # Should raise workflow error
            with pytest.raises(WorkflowError) as exc_info:
                await executor.execute(mock_input_data, mock_tracer)
            
            assert "Agent failed" in str(exc_info.value)
            
            # Verify error was logged in tracer
            mock_tracer.complete_execution.assert_called_once()
            call_args = mock_tracer.complete_execution.call_args
            assert "error" in call_args.kwargs
    
    @pytest.mark.asyncio
    async def test_execute_all_workflow_steps(self, executor):
        """Test execution of all available workflow steps."""
        steps = ["planning", "design", "test_writing", "implementation", "review", "execution"]
        
        for step in steps:
            input_data = CodingTeamInput(
                requirements="Test requirement",
                step_type=step
            )
            
            mock_result = f"{step} completed"
            
            with patch('workflows.individual.individual_workflow_enhanced.run_team_member_with_tracking',
                      new_callable=AsyncMock, return_value=mock_result):
                
                results, _ = await executor.execute(input_data)
                
                # Verify correct agent was called
                assert len(results) == 1
                assert results[0].name == executor.agent_map[step][2]
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_logic(self, executor, mock_input_data, mock_tracer):
        """Test retry logic on agent failure."""
        # First two calls fail, third succeeds
        call_count = 0
        
        async def flaky_agent(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise AgentError("Temporary failure", "test_agent")
            return "Success"
        
        # Enable retries
        executor.workflow_config["steps"]["planning"]["retries"] = 3
        
        with patch('workflows.individual.individual_workflow_enhanced.run_team_member_with_tracking',
                  side_effect=flaky_agent):
            
            results, _ = await executor.execute(mock_input_data, mock_tracer)
            
            # Should succeed after retries
            assert len(results) == 1
            assert "Success" in results[0].output
    
    def test_unknown_workflow_step(self, executor):
        """Test handling of unknown workflow step."""
        input_data = CodingTeamInput(
            requirements="Test",
            step_type="unknown_step"
        )
        
        with pytest.raises(WorkflowError) as exc_info:
            asyncio.run(executor.execute(input_data))
        
        assert "Unknown workflow step" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_progress_reporter_integration(self, executor, mock_input_data, mock_tracer):
        """Test progress reporter is properly initialized and used."""
        with patch('workflows.individual.individual_workflow_enhanced.ProgressReporter') as mock_progress:
            mock_reporter = Mock()
            mock_progress.return_value = mock_reporter
            
            with patch('workflows.individual.individual_workflow_enhanced.run_team_member_with_tracking',
                      new_callable=AsyncMock, return_value="Result"):
                
                await executor.execute(mock_input_data, mock_tracer)
                
                # Verify progress reporter was created and used
                mock_progress.assert_called_once()
                mock_reporter.start_step.assert_called_with("planning")
                mock_reporter.complete_step.assert_called_with("planning")
    
    @pytest.mark.asyncio
    async def test_logging_integration(self, executor, mock_input_data, mock_tracer):
        """Test logging calls are made correctly."""
        with patch('workflows.individual.individual_workflow_enhanced.log_workflow_event') as mock_log_event:
            with patch('workflows.individual.individual_workflow_enhanced.log_agent_interaction') as mock_log_agent:
                with patch('workflows.individual.individual_workflow_enhanced.run_team_member_with_tracking',
                          new_callable=AsyncMock, return_value="Result"):
                    
                    await executor.execute(mock_input_data, mock_tracer)
                    
                    # Verify workflow events were logged
                    assert mock_log_event.call_count >= 2  # start and complete
                    
                    # Verify agent interaction was logged
                    mock_log_agent.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_configuration_loading(self):
        """Test configuration is properly loaded from config manager."""
        mock_config = {
            "timeout": 1200,
            "steps": {
                "planning": {"timeout": 600, "retries": 5}
            }
        }
        
        with patch('workflows.individual.individual_workflow_enhanced.get_config_manager') as mock_cm:
            mock_cm.return_value.get_workflow_config.return_value = mock_config
            
            executor = IndividualWorkflowExecutor()
            
            assert executor.workflow_config == mock_config


class TestIndividualWorkflowBackwardCompatibility:
    """Test backward compatibility with original workflow."""
    
    @pytest.mark.asyncio
    async def test_original_function_signature(self):
        """Test the original execute_individual_workflow function works."""
        from workflows.individual.individual_workflow import execute_individual_workflow
        
        input_data = CodingTeamInput(
            requirements="Test requirement",
            step_type="planning"
        )
        
        with patch('workflows.individual.individual_workflow.USE_ENHANCED', False):
            with patch('workflows.individual.individual_workflow.run_team_member_with_tracking',
                      new_callable=AsyncMock, return_value="Result"):
                
                # Should not raise any errors
                results, report = await execute_individual_workflow(input_data)
                
                assert isinstance(results, list)
                assert report is not None