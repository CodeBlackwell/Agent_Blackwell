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
from workflows.incremental.feature_orchestrator import run_incremental_coding_phase
# Import executor components
from agents.executor.session_utils import generate_session_id

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
        # Execute the workflow - include executor if it's in input_data.team_members
        team_members = ["planner", "designer", "coder", "reviewer"]
        if TeamMember.executor in input_data.team_members:
            team_members.append("executor")
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
    # Import run_team_member dynamically using dependency injection to avoid circular imports
    from core.migration import run_team_member_with_tracking

    # Import review_output from the renamed workflow_utils.py file
    from workflows import workflow_utils
    # Use the review_output function from the module
    review_output = workflow_utils.review_output
    
    results = []
    max_retries = MAX_REVIEW_RETRIES
    
    print(f"🔄 Starting full workflow for: {requirements[:50]}...")
    
    # Step 1: Planning
    if "planner" in team_members:
        print("📋 Planning phase...")
        step_id = tracer.start_step("planning", "planner_agent", {"requirements": requirements})
        
        planning_result = await run_team_member_with_tracking("planner_agent", requirements, "full_planning")
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
            design_result = await run_team_member_with_tracking("designer_agent", design_input, "full_design")
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
                step_id = tracer.start_step("implementation", "incremental_coding", {
                    "plan_input": plan_output[:200] + "...",
                    "design_input": design_output[:200] + "...",
                    "requirements": requirements
                })
                
                # Use incremental feature orchestrator instead of direct coder_agent call
                try:
                    code_output, execution_metrics = await run_incremental_coding_phase(
                        designer_output=design_output,
                        requirements=requirements,
                        tests=None,  # No tests in full workflow
                        tracer=tracer,
                        max_retries=3
                    )
                    
                    # Add execution metrics to tracer
                    tracer.add_metadata("incremental_execution_metrics", execution_metrics)
                    
                    # Log feature execution stats
                    print(f"✅ Completed {execution_metrics['completed_features']}/{execution_metrics['total_features']} features")
                    print(f"📊 Success rate: {execution_metrics['success_rate']:.1f}%")
                    
                    # Add coder result to results list
                    tracer.complete_step(step_id, {
                        "output": code_output[:200] + "...",
                        "features_completed": execution_metrics['completed_features'],
                        "total_features": execution_metrics['total_features']
                    })
                    
                    # The incremental orchestrator already returns a TeamMemberResult for the coder
                    # so we don't need to create one here, just add it to our results list
                    coder_result = TeamMemberResult(
                        team_member=TeamMember.coder,
                        output=code_output,
                        name="coder"
                    )
                    results.append(coder_result)
                    
                    # Execute tests and code if executor is in team members
                    if "executor" in team_members:
                        print("🐳 Executing code in Docker container...")
                        session_id = generate_session_id(input_data.requirements)
                        
                        step_id = tracer.start_step("execution", "executor_agent", {
                            "session_id": session_id,
                            "code": code_output[:200] + "..."
                        })
                        
                        # Prepare execution input with session ID
                        execution_input = f"""SESSION_ID: {session_id}

Execute the following code:

{code_output}
"""
                        
                        execution_result = await run_team_member_with_tracking("executor_agent", execution_input, "full_execution")
                        execution_output = str(execution_result)
                        
                        # Extract proof of execution details
                        from agents.executor.proof_reader import extract_proof_from_executor_output
                        proof_details = extract_proof_from_executor_output(execution_output, session_id)
                        
                        # Append proof details to execution output
                        if proof_details and "No proof of execution found" not in proof_details:
                            execution_output += f"\n\n{proof_details}"
                        
                        tracer.complete_step(step_id, {"output": execution_output[:200] + "..."})
                        
                        # Add execution results to the results list
                        results.append(TeamMemberResult(
                            team_member=TeamMember.executor,
                            output=execution_output,
                            name="executor"
                        ))
                    
                except Exception as e:
                    error_msg = f"Incremental coding phase error: {str(e)}"
                    print(f"❌ {error_msg}")
                    tracer.complete_step(step_id, {"error": error_msg}, error=error_msg)
                    # Fall back to standard coder implementation
                    print("⚠️ Falling back to standard implementation...")
                    
                    code_input = f"Plan:\n{plan_output}\n\nDesign:\n{design_output}\n\nRequirements: {requirements}"
                    code_result = await run_team_member_with_tracking("coder_agent", code_input, "full_coding")
                    code_output = str(code_result)
                    
                    results.append(TeamMemberResult(
                        team_member=TeamMember.coder,
                        output=code_output,
                        name="coder"
                    ))
                    
                    # Execute tests and code in fallback path if executor is in team members
                    if "executor" in team_members:
                        print("🐳 Executing code in Docker container (fallback path)...")
                        session_id = generate_session_id(input_data.requirements)
                        
                        step_id = tracer.start_step("execution_fallback", "executor_agent", {
                            "session_id": session_id,
                            "code": code_output[:200] + "..."
                        })
                        
                        # Prepare execution input with session ID
                        execution_input = f"""SESSION_ID: {session_id}

Execute the following code:

{code_output}
"""
                        
                        execution_result = await run_team_member_with_tracking("executor_agent", execution_input, "full_execution_fallback")
                        execution_output = str(execution_result)
                        
                        # Extract proof of execution details
                        from agents.executor.proof_reader import extract_proof_from_executor_output
                        proof_details = extract_proof_from_executor_output(execution_output, session_id)
                        
                        # Append proof details to execution output
                        if proof_details and "No proof of execution found" not in proof_details:
                            execution_output += f"\n\n{proof_details}"
                        
                        tracer.complete_step(step_id, {"output": execution_output[:200] + "..."})
                        
                        # Add execution results to the results list
                        results.append(TeamMemberResult(
                            team_member=TeamMember.executor,
                            output=execution_output,
                            name="executor"
                        ))
                
                # Step 4: Final Review
                if "reviewer" in team_members:
                    print("🔍 Final review phase...")
                    step_id = tracer.start_step("final_review", "reviewer_agent", {
                        "code_input": code_output[:200] + "...",
                        "context": "Full workflow final review"
                    })
                    
                    review_input = f"Requirements: {requirements}\n\nPlan:\n{plan_output}\n\nDesign:\n{design_output}\n\nImplementation:\n{code_output}"
                    review_result = await run_team_member_with_tracking("reviewer_agent", review_input, "full_final_review")
                    review_result_output = str(review_result)
                    
                    tracer.complete_step(step_id, {"output": review_result_output[:200] + "..."})
                    results.append(TeamMemberResult(
                        team_member=TeamMember.reviewer,
                        output=review_result_output,
                        name="reviewer"
                    ))
    
    return results