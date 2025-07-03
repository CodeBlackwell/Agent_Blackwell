"""
Workflow manager for coordinating different workflow implementations.
"""
from typing import List, Tuple, Optional

from orchestrator.orchestrator_agent import (
    TeamMember, TeamMemberResult, WorkflowStep
)
from workflows.tdd.tdd_workflow import execute_tdd_workflow
from workflows.full.full_workflow import execute_full_workflow
from workflows.individual.individual_workflow import execute_individual_workflow
from workflows.monitoring import WorkflowExecutionTracer, WorkflowExecutionReport
from shared.models import CodingTeamInput, TeamMemberResult


async def execute_workflow(input_data: CodingTeamInput, 
                          tracer: Optional[WorkflowExecutionTracer] = None) -> Tuple[List[TeamMemberResult], WorkflowExecutionReport]:
    """
    Execute a workflow based on the specified type with comprehensive monitoring.
    
    Args:
        input_data: The input data containing workflow type and requirements
        tracer: Optional tracer for monitoring execution (creates new one if not provided)
        
    Returns:
        Tuple of (team member results, execution report)
    """
    workflow_type = input_data.workflow_type.lower()
    
    # Create tracer if not provided
    if tracer is None:
        tracer = WorkflowExecutionTracer(workflow_type)
    
    # Add input metadata to tracer
    tracer.add_metadata('input_requirements', input_data.requirements)
    tracer.add_metadata('team_members', [member.name for member in input_data.team_members])
    
    try:
        # Execute the appropriate workflow with monitoring
        if workflow_type == "tdd":
            results = await execute_tdd_workflow(input_data, tracer)
        elif workflow_type == "full":
            results = await execute_full_workflow(input_data, tracer)
        elif workflow_type == "individual":
            results = await execute_individual_workflow(input_data, tracer)
        else:
            error_msg = f"Unknown workflow type: {workflow_type}"
            tracer.complete_execution(error=error_msg)
            raise ValueError(error_msg)
        
        # Complete successful execution
        final_output = {
            'workflow_type': workflow_type,
            'results_count': len(results),
            'team_members': [result.name for result in results]
        }
        tracer.complete_execution(final_output=final_output)
        
        return results, tracer.get_report()
        
    except Exception as e:
        # Complete execution with error
        tracer.complete_execution(error=str(e))
        raise