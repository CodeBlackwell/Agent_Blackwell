"""
Full workflow implementation with comprehensive monitoring.
"""
from typing import List, Optional, Tuple
import asyncio
from workflows.monitoring import WorkflowExecutionTracer, WorkflowExecutionReport
from shared.data_models import (
    TeamMember, WorkflowStep, CodingTeamInput, CodingTeamResult, TeamMemberResult
)
from workflows.workflow_config import MAX_REVIEW_RETRIES

import workflows.utils as workflow_utils
review_output = workflow_utils.review_output


async def execute_full_workflow(input_data: CodingTeamInput, tracer: Optional[WorkflowExecutionTracer] = None) -> Tuple[List[TeamMemberResult], WorkflowExecutionReport]:
    """
    Execute the full workflow with comprehensive monitoring.
    
    Args:
        input_data: The input data containing requirements and workflow configuration
        tracer: Optional tracer for monitoring execution (creates new one if not provided)
        
    Returns:
        Tuple of (team member results, execution report)
    """
    # Create tracer if not provided
    if tracer is None:
        tracer = WorkflowExecutionTracer(
            workflow_type="Full",
            execution_id=f"full_{int(asyncio.get_event_loop().time())}"
        )
    
    # The tracer is already initialized by workflow_manager
    
    try:
        # Execute the workflow
        team_members = ["planner", "designer", "coder", "reviewer"]
        results = await run_full_workflow(input_data.requirements, team_members, tracer)
        
        # Complete workflow execution
        tracer.complete_execution(final_output={
            "workflow": "Full",
            "results_count": len(results),
            "success": True
        })
    except Exception as e:
        # Handle exceptions and complete workflow with error
        error_msg = f"Full workflow error: {str(e)}"
        tracer.complete_execution(error=error_msg)
        raise
    
    # Return results and execution report
    return results, tracer.get_report()


async def run_full_workflow(requirements: str, team_members: List[str], tracer: WorkflowExecutionTracer) -> List[TeamMemberResult]:
    """
    Run full workflow: planner -> designer -> coder -> reviewer
    
    Args:
        requirements: The project requirements
        team_members: Team members to involve in the process
        tracer: Workflow execution tracer
        
    Returns:
        List of team member results
    """
    # Import run_team_member dynamically to avoid circular imports
    from orchestrator.orchestrator_agent import run_team_member
    
    results = []
    max_retries = MAX_REVIEW_RETRIES
    
    print(f"🔄 Starting full workflow for: {requirements[:50]}...")
    
    # Step 1: Planning
    if "planner" in team_members:
        print("📋 Planning phase...")
        step_id = tracer.start_step("planning", "planner_agent", {"requirements": requirements})
        
        planning_result = await run_team_member("planner_agent", requirements)
        plan_output = str(planning_result)
        
        tracer.complete_step(step_id, {"output": plan_output[:200] + "..."})
        results.append(TeamMemberResult(
            team_member=TeamMember.planner,
            output=plan_output,
            name="planner"
        ))
        
        # Review the plan
        approved, feedback = await review_output(
            plan_output, 
            "planning", 
            tracer=tracer,
            target_agent="planner_agent"
        )
        
        # Step 2: Design
        if "designer" in team_members:
            print("🎨 Design phase...")
            step_id = tracer.start_step("design", "designer_agent", {
                "plan_input": plan_output[:200] + "...",
                "requirements": requirements
            })
            
            design_input = f"Plan:\n{plan_output}\n\nRequirements: {requirements}"
            design_result = await run_team_member("designer_agent", design_input)
            design_output = str(design_result)
            
            tracer.complete_step(step_id, {"output": design_output[:200] + "..."})
            results.append(TeamMemberResult(
                team_member=TeamMember.designer,
                output=design_output,
                name="designer"
            ))
            
            # Review the design
            approved, feedback = await review_output(
                design_output, 
                "design", 
                tracer=tracer,
                target_agent="designer_agent"
            )
            
            # Step 3: Implementation
            if "coder" in team_members:
                print("💻 Implementation phase...")
                step_id = tracer.start_step("implementation", "coder_agent", {
                    "plan_input": plan_output[:200] + "...",
                    "design_input": design_output[:200] + "...",
                    "requirements": requirements
                })
                
                code_input = f"Plan:\n{plan_output}\n\nDesign:\n{design_output}\n\nRequirements: {requirements}"
                code_result = await run_team_member("coder_agent", code_input)
                code_output = str(code_result)
                
                tracer.complete_step(step_id, {"output": code_output[:200] + "..."})
                results.append(TeamMemberResult(
                    team_member=TeamMember.coder,
                    output=code_output,
                    name="coder"
                ))
                
                # Step 4: Final Review
                if "reviewer" in team_members:
                    print("🔍 Final review phase...")
                    step_id = tracer.start_step("final_review", "reviewer_agent", {
                        "code_input": code_output[:200] + "...",
                        "context": "Full workflow final review"
                    })
                    
                    review_input = f"Requirements: {requirements}\n\nPlan:\n{plan_output}\n\nDesign:\n{design_output}\n\nImplementation:\n{code_output}"
                    review_result = await run_team_member("reviewer_agent", review_input)
                    review_result_output = str(review_result)
                    
                    tracer.complete_step(step_id, {"output": review_result_output[:200] + "..."})
                    results.append(TeamMemberResult(
                        team_member=TeamMember.reviewer,
                        output=review_result_output,
                        name="reviewer"
                    ))
    
    return results