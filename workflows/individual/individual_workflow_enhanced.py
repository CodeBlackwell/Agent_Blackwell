"""
Enhanced individual workflow implementation with comprehensive error handling,
timeouts, and progress reporting.
"""
import asyncio
import time
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timedelta

from workflows.monitoring import WorkflowExecutionTracer, WorkflowExecutionReport
from shared.data_models import (
    TeamMember, WorkflowStep, CodingTeamInput, CodingTeamResult, TeamMemberResult
)

# Import core infrastructure
from core.exceptions import (
    WorkflowError, AgentTimeoutError, AgentError,
    ErrorHandler, get_error_handler
)
from core.error_utils import (
    handle_errors_async, with_timeout, retry_on_error, ErrorContext
)
from core.logging_config import get_logger, log_workflow_event, log_agent_interaction
from config.config_manager import get_config_manager

# Import migration helpers
from core.migration import run_team_member_with_tracking

# Import progress reporting
from .progress_reporter import ProgressReporter


logger = get_logger(__name__)


class IndividualWorkflowExecutor:
    """Enhanced executor for individual workflow with full instrumentation."""
    
    def __init__(self):
        """Initialize the executor."""
        # Load workflow configuration
        self.config_manager = get_config_manager()
        self.workflow_config = self.config_manager.get_workflow_config("individual")
        
        # Initialize error handler
        self.error_handler = get_error_handler()
        
        # Agent mapping
        self.agent_map = {
            "planning": ("planner_agent", TeamMember.planner, "planner"),
            "design": ("designer_agent", TeamMember.designer, "designer"),
            "test_writing": ("test_writer_agent", TeamMember.test_writer, "test_writer"),
            "implementation": ("coder_agent", TeamMember.coder, "coder"),
            "review": ("reviewer_agent", TeamMember.reviewer, "reviewer"),
            "execution": ("executor_agent", TeamMember.executor, "executor")
        }
        
        # Progress reporter
        self.progress_reporter = None
    
    async def execute(
        self,
        input_data: CodingTeamInput,
        tracer: Optional[WorkflowExecutionTracer] = None
    ) -> Tuple[List[TeamMemberResult], WorkflowExecutionReport]:
        """
        Execute an individual workflow step with comprehensive monitoring.
        
        Args:
            input_data: The input data containing requirements and workflow configuration
            tracer: Optional tracer for monitoring execution
            
        Returns:
            Tuple of (team member results, execution report)
        """
        # Create tracer if not provided
        if tracer is None:
            execution_id = f"individual_{int(time.time())}"
            tracer = WorkflowExecutionTracer(
                workflow_type="Individual",
                execution_id=execution_id
            )
        
        # Initialize progress reporter
        if self.workflow_config.get("progress", {}).get("show_step_progress", True):
            self.progress_reporter = ProgressReporter(
                workflow_type="Individual",
                total_steps=1,
                show_eta=self.workflow_config.get("progress", {}).get("show_eta", True)
            )
        
        # Extract workflow step
        workflow_step = input_data.step_type or input_data.workflow_type or "planning"
        
        # Log workflow start
        log_workflow_event(
            workflow_id=tracer.execution_id,
            event_type="workflow_started",
            event_data={
                "step": workflow_step,
                "requirements_preview": input_data.requirements[:200]
            }
        )
        
        # Use error context for execution
        with ErrorContext(f"Individual workflow - {workflow_step}"):
            try:
                # Get step configuration
                step_config = self.workflow_config.get("steps", {}).get(workflow_step, {})
                step_timeout = step_config.get("timeout", 300)
                step_retries = step_config.get("retries", 2)
                
                # Execute with timeout
                results = await self._execute_with_timeout(
                    self._run_workflow_step(
                        input_data.requirements,
                        workflow_step,
                        tracer,
                        step_retries
                    ),
                    timeout_seconds=step_timeout,
                    step_name=workflow_step
                )
                
                # Complete workflow execution
                tracer.complete_execution(final_output={
                    "workflow": "Individual",
                    "step": workflow_step,
                    "results_count": len(results),
                    "success": True
                })
                
                # Log workflow completion
                log_workflow_event(
                    workflow_id=tracer.execution_id,
                    event_type="workflow_completed",
                    event_data={
                        "step": workflow_step,
                        "duration_seconds": tracer.get_duration()
                    }
                )
                
            except Exception as e:
                # Handle exceptions
                error_msg = f"Individual workflow error: {str(e)}"
                tracer.complete_execution(error=error_msg)
                
                # Log workflow failure
                log_workflow_event(
                    workflow_id=tracer.execution_id,
                    event_type="workflow_failed",
                    event_data={
                        "step": workflow_step,
                        "error": str(e),
                        "error_type": type(e).__name__
                    }
                )
                
                raise WorkflowError(
                    message=error_msg,
                    workflow_type="Individual",
                    phase=workflow_step,
                    details={"original_error": str(e)}
                )
        
        # Return results and execution report
        return results, tracer.get_report()
    
    async def _execute_with_timeout(
        self,
        coro,
        timeout_seconds: int,
        step_name: str
    ):
        """Execute coroutine with timeout."""
        try:
            return await asyncio.wait_for(coro, timeout=timeout_seconds)
        except asyncio.TimeoutError:
            raise AgentTimeoutError(
                agent_name=step_name,
                timeout_seconds=timeout_seconds
            )
    
    @retry_on_error(
        max_attempts=3,
        backoff_seconds=5,
        exponential_backoff=True,
        error_types=(AgentError,)
    )
    async def _run_workflow_step(
        self,
        requirements: str,
        workflow_step: str,
        tracer: WorkflowExecutionTracer,
        max_retries: int
    ) -> List[TeamMemberResult]:
        """
        Run a specific workflow step with retries and monitoring.
        
        Args:
            requirements: The project requirements
            workflow_step: The specific workflow step to execute
            tracer: Workflow execution tracer
            max_retries: Maximum number of retries for this step
            
        Returns:
            List of team member results
        """
        results = []
        
        if workflow_step not in self.agent_map:
            raise WorkflowError(
                message=f"Unknown workflow step: {workflow_step}",
                workflow_type="Individual",
                phase=workflow_step
            )
        
        agent_name, team_member, result_name = self.agent_map[workflow_step]
        
        # Update progress
        if self.progress_reporter:
            self.progress_reporter.start_step(workflow_step)
        
        logger.info(f"Running {workflow_step} phase...")
        
        # Start monitoring step
        step_id = tracer.start_step(
            step_name=workflow_step,
            agent_name=agent_name,
            input_data={
                "requirements": requirements,
                "workflow_type": "individual",
                "step_type": workflow_step
            }
        )
        
        # Track timing
        start_time = time.time()
        
        try:
            # Run agent with tracking
            result = await run_team_member_with_tracking(
                agent_name,
                requirements,
                f"individual_{workflow_step}"
            )
            
            output = str(result)
            duration_ms = (time.time() - start_time) * 1000
            
            # Log agent interaction
            log_agent_interaction(
                agent_name=agent_name,
                interaction_type=workflow_step,
                input_data=requirements[:500],
                output_data=output[:500],
                duration_ms=duration_ms
            )
            
            # Complete monitoring step
            tracer.complete_step(step_id, {
                "output": output[:200] + "...",
                "step_completed": workflow_step,
                "success": True,
                "duration_ms": duration_ms
            })
            
            # Create result
            results.append(TeamMemberResult(
                team_member=team_member,
                output=output,
                name=result_name
            ))
            
            # Update progress
            if self.progress_reporter:
                self.progress_reporter.complete_step(workflow_step)
            
            logger.info(f"{workflow_step} phase completed successfully in {duration_ms:.0f}ms")
            
        except Exception as e:
            error_msg = f"{workflow_step} step failed: {str(e)}"
            duration_ms = (time.time() - start_time) * 1000
            
            tracer.complete_step(step_id, error=error_msg)
            
            # Update progress with error
            if self.progress_reporter:
                self.progress_reporter.error_step(workflow_step, str(e))
            
            logger.error(f"{workflow_step} failed after {duration_ms:.0f}ms: {error_msg}")
            
            # Create agent-specific error
            raise AgentError(
                message=error_msg,
                agent_name=agent_name,
                details={
                    "step": workflow_step,
                    "duration_ms": duration_ms,
                    "original_error": str(e)
                }
            )
        
        return results


# Backward compatibility function
async def execute_individual_workflow(
    input_data: CodingTeamInput,
    tracer: Optional[WorkflowExecutionTracer] = None
) -> Tuple[List[TeamMemberResult], WorkflowExecutionReport]:
    """
    Execute an individual workflow step with comprehensive monitoring.
    
    This function maintains backward compatibility with the existing interface.
    """
    executor = IndividualWorkflowExecutor()
    return await executor.execute(input_data, tracer)