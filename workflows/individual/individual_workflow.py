"""
Individual workflow step implementation with comprehensive monitoring.
"""
from typing import List, Optional, Tuple
import asyncio
import os
from workflows.monitoring import WorkflowExecutionTracer, WorkflowExecutionReport
from shared.data_models import (
    TeamMember, WorkflowStep, CodingTeamInput, CodingTeamResult, TeamMemberResult
)
# Import executor components
from agents.executor.session_utils import generate_session_id

# Check if we should use enhanced version
# For now, disable enhanced version until DI is properly set up
USE_ENHANCED = os.getenv('USE_ENHANCED_INDIVIDUAL', 'false').lower() == 'true'

async def execute_individual_workflow(input_data: CodingTeamInput, tracer: Optional[WorkflowExecutionTracer] = None) -> Tuple[List[TeamMemberResult], WorkflowExecutionReport]:
    """
    Execute an individual workflow step with comprehensive monitoring.
    
    This function now delegates to the enhanced version if enabled.
    """
    if USE_ENHANCED:
        try:
            from .individual_workflow_enhanced import execute_individual_workflow as enhanced_execute
            return await enhanced_execute(input_data, tracer)
        except ImportError:
            # Fall back to original implementation
            pass
    
    # Original implementation continues below
    return await _execute_individual_workflow_original(input_data, tracer)


async def _execute_individual_workflow_original(input_data: CodingTeamInput, tracer: Optional[WorkflowExecutionTracer] = None) -> Tuple[List[TeamMemberResult], WorkflowExecutionReport]:
    """
    Execute an individual workflow step with comprehensive monitoring.
    
    Args:
        input_data: The input data containing requirements and workflow configuration
        tracer: Optional tracer for monitoring execution (creates new one if not provided)
        
    Returns:
        Tuple of (team member results, execution report)
    """
    # Create tracer if not provided
    if tracer is None:
        tracer = WorkflowExecutionTracer(
            workflow_type="Individual",
            execution_id=f"individual_{int(asyncio.get_event_loop().time())}"
        )
    
    # Extract workflow step from input data
    workflow_step = input_data.step_type or input_data.workflow_type or "planning"
    
    # The tracer is already initialized by workflow_manager
    
    try:
        # Execute the workflow
        results = await run_individual_workflow(input_data.requirements, workflow_step, tracer)
        
        # Complete workflow execution
        tracer.complete_execution(final_output={
            "workflow": "Individual",
            "step": workflow_step,
            "results_count": len(results),
            "success": True
        })
    except Exception as e:
        # Handle exceptions and complete workflow with error
        error_msg = f"Individual workflow error: {str(e)}"
        tracer.complete_execution(error=error_msg)
        raise
    
    # Return results and execution report
    return results, tracer.get_report()


async def run_individual_workflow(requirements: str, workflow_step: str, tracer: WorkflowExecutionTracer) -> List[TeamMemberResult]:
    """
    Run a specific workflow step
    
    Args:
        requirements: The project requirements
        workflow_step: The specific workflow step to execute
        tracer: Workflow execution tracer
        
    Returns:
        List of team member results (containing single result)
    """
    # Use dependency injection instead of circular imports
    from core.migration import run_team_member_with_tracking
    
    results = []
    
    agent_map = {
        "planning": ("planner_agent", TeamMember.planner, "planner"),
        "design": ("designer_agent", TeamMember.designer, "designer"),
        "test_writing": ("test_writer_agent", TeamMember.test_writer, "test_writer"),
        "implementation": ("coder_agent", TeamMember.coder, "coder"),
        "review": ("reviewer_agent", TeamMember.reviewer, "reviewer"),
        "execution": ("executor_agent", TeamMember.executor, "executor")
    }
    
    if workflow_step in agent_map:
        agent_name, team_member, result_name = agent_map[workflow_step]
        
        # Only print in non-debug mode (debug mode has logger output)
        import logging
        if logging.getLogger().level > logging.DEBUG:
            print(f" Running {workflow_step} phase...")
        
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
        
        try:
            result = await run_team_member_with_tracking(agent_name, requirements, f"individual_{workflow_step}")
            output = str(result)
            
            # Complete monitoring step
            tracer.complete_step(step_id, {
                "output": output[:200] + "...",
                "step_completed": workflow_step,
                "success": True
            })
            
            results.append(TeamMemberResult(
                team_member=team_member,
                output=output,
                name=result_name
            ))
            if logging.getLogger().level > logging.DEBUG:
                print(f" {workflow_step} phase completed successfully")
            
        except Exception as e:
            error_msg = f"{workflow_step} step failed: {str(e)}"
            tracer.complete_step(step_id, error=error_msg)
            if logging.getLogger().level > logging.DEBUG:
                print(f" {workflow_step} failed: {error_msg}")
            raise
    
    return results