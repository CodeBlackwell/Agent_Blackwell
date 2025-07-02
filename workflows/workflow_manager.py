"""
Workflow manager for coordinating different workflow implementations.
"""
from typing import List

from orchestrator.orchestrator_agent import (
    TeamMember, TeamMemberResult, WorkflowStep, CodingTeamInput
)
from workflows.tdd.tdd_workflow import run_tdd_workflow
from workflows.full.full_workflow import run_full_workflow
from workflows.individual.individual_workflow import run_individual_workflow


async def execute_workflow(input: CodingTeamInput) -> List[TeamMemberResult]:
    """
    Execute a specific workflow based on the input
    
    Args:
        input: The coding team input containing requirements, workflow and team members
        
    Returns:
        List of team member results
    """
    if input.workflow == WorkflowStep.tdd_workflow:
        return await run_tdd_workflow(input.requirements, input.team_members)
    
    elif input.workflow == WorkflowStep.full_workflow:
        return await run_full_workflow(input.requirements, input.team_members)
    
    else:
        # Assume this is an individual workflow step
        return await run_individual_workflow(input.requirements, input.workflow)