"""
Individual workflow step implementation.
"""
from typing import List

from orchestrator.orchestrator_agent import (
    TeamMember, TeamMemberResult, WorkflowStep, run_team_member
)

async def run_individual_workflow(requirements: str, workflow_step: WorkflowStep) -> List[TeamMemberResult]:
    """
    Run a specific workflow step
    
    Args:
        requirements: The project requirements
        workflow_step: The specific workflow step to execute
        
    Returns:
        List of team member results (containing single result)
    """
    results = []
    
    agent_map = {
        WorkflowStep.planning: "planner_agent",
        WorkflowStep.design: "designer_agent",
        WorkflowStep.test_writing: "test_writer_agent",
        WorkflowStep.implementation: "coder_agent",
        WorkflowStep.review: "reviewer_agent"
    }
    
    if workflow_step in agent_map:
        print(f"🔄 Running {workflow_step.value} phase...")
        result = await run_team_member(agent_map[workflow_step], requirements)
        output = str(result[0])
        
        # Map workflow steps to team members
        step_to_member = {
            WorkflowStep.planning: TeamMember.planner,
            WorkflowStep.design: TeamMember.designer,
            WorkflowStep.test_writing: TeamMember.test_writer,
            WorkflowStep.implementation: TeamMember.coder,
            WorkflowStep.review: TeamMember.reviewer
        }
        
        team_member = step_to_member[workflow_step]
        results.append(TeamMemberResult(team_member=team_member, output=output))
    
    return results
