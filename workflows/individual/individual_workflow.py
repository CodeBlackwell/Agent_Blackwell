"""
Individual workflow step implementation with comprehensive monitoring.
"""
from typing import List
from workflows.monitoring import WorkflowExecutionTracer
from orchestrator.orchestrator_agent import (
    TeamMember, TeamMemberResult, WorkflowStep, run_team_member
)

async def run_individual_workflow(requirements: str, workflow_step: WorkflowStep, tracer: WorkflowExecutionTracer) -> List[TeamMemberResult]:
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
    
    # Map workflow steps to result names
    step_to_name = {
        WorkflowStep.planning: "planner",
        WorkflowStep.design: "designer",
        WorkflowStep.test_writing: "test_writer",
        WorkflowStep.implementation: "coder",
        WorkflowStep.review: "reviewer"
    }
    
    if workflow_step in agent_map:
        print(f"🔄 Running {workflow_step.value} phase...")
        
        # Start monitoring step
        step_id = tracer.start_step(
            step_name=workflow_step.value,
            agent_name=agent_map[workflow_step],
            metadata={
                "requirements": requirements,
                "workflow_type": "individual",
                "step_type": workflow_step.value
            }
        )
        
        try:
            result = await run_team_member(agent_map[workflow_step], requirements)
            output = str(result)
            
            # Complete monitoring step
            tracer.complete_step(step_id, {
                "output": output,
                "step_completed": workflow_step.value,
                "success": True
            })
            
            result_name = step_to_name[workflow_step]
            results.append(TeamMemberResult(name=result_name, output=output))
            print(f"✅ {workflow_step.value} phase completed successfully")
            
        except Exception as e:
            error_msg = f"{workflow_step.value} step failed: {str(e)}"
            tracer.complete_step(step_id, error=error_msg)
            print(f"❌ {workflow_step.value} failed: {error_msg}")
    
    return results
