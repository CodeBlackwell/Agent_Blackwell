"""
Full workflow implementation with comprehensive monitoring.
"""
from typing import List
from workflows.monitoring import WorkflowExecutionTracer
from orchestrator.orchestrator_agent import (
    TeamMember, TeamMemberResult, WorkflowStep, run_team_member
)
from workflows.utils import review_output
from workflows.workflow_config import MAX_REVIEW_RETRIES

async def run_full_workflow(requirements: str, team_members: List[str], tracer: WorkflowExecutionTracer) -> List[TeamMemberResult]:
    """
    Run full workflow: planner -> designer -> coder -> reviewer
    
    Args:
        requirements: The project requirements
        team_members: Team members to involve in the process
        
    Returns:
        List of team member results
    """
    results = []
    max_retries = MAX_REVIEW_RETRIES
    
    print(f"🔄 Starting full workflow for: {requirements[:50]}...")
    
    # Step 1: Planning with review
    if "planner" in team_members:
        print("📋 Planning phase...")
        step_id = tracer.start_step("planning", "planner_agent", {"requirements": requirements})
        
        planning_approved = False
        plan_output = ""
        planning_retries = 0
        
        while not planning_approved and planning_retries < max_retries:
            try:
                planning_result = await run_team_member("planner_agent", requirements)
                plan_output = str(planning_result)
                
                # Review the plan with monitoring
                approved, feedback = await review_output(
                    plan_output, 
                    "Planning phase output", 
                    tracer=tracer,
                    target_agent="planner_agent"
                )
                
                if approved:
                    planning_approved = True
                    tracer.complete_step(step_id, {"plan": plan_output, "approved": True})
                    results.append(TeamMemberResult(name="planner", output=plan_output))
                    print("✅ Plan approved by reviewer")
                else:
                    print(f"❌ Plan needs revision: {feedback}")
                    tracer.record_retry(
                        attempt_number=planning_retries + 1,
                        reason="Plan revision needed",
                        previous_error=feedback,
                        changes_made="Incorporating reviewer feedback"
                    )
                    requirements = f"{requirements}\n\nReviewer feedback: {feedback}"
                    planning_retries += 1
                    
            except Exception as e:
                error_msg = f"Planning step failed: {str(e)}"
                tracer.complete_step(step_id, error=error_msg)
                print(f"❌ Planning failed: {error_msg}")
                break
        
        if not planning_approved:
            tracer.complete_step(step_id, error="Planning failed after max retries")
        
        # Step 2: Design with review (using plan as input)
        if "designer" in team_members and planning_approved:
            print("🎨 Design phase...")
            step_id = tracer.start_step("design", "designer_agent", {
                "plan_input": plan_output,
                "requirements": requirements
            })
            
            design_approved = False
            design_output = ""
            design_retries = 0
            
            while not design_approved and design_retries < max_retries:
                try:
                    design_input = f"""You are the designer for this project. Here is the detailed plan:

{plan_output}

Based on this plan, create a comprehensive technical design. Do NOT ask for more details - use the plan above to extract all technical requirements and create concrete designs.

Original requirements: {requirements}

Create the technical architecture, database schemas, API endpoints, and component designs."""
                    
                    design_result = await run_team_member("designer_agent", design_input)
                    design_output = str(design_result)
                    
                    # Review the design with monitoring
                    approved, feedback = await review_output(
                        design_output, 
                        "Design phase output", 
                        tracer=tracer,
                        target_agent="designer_agent"
                    )
                    
                    if approved:
                        design_approved = True
                        tracer.complete_step(step_id, {"design": design_output, "approved": True})
                        results.append(TeamMemberResult(name="designer", output=design_output))
                        print("✅ Design approved by reviewer")
                    else:
                        print(f"❌ Design needs revision: {feedback}")
                        tracer.record_retry(
                            attempt_number=design_retries + 1,
                            reason="Design revision needed",
                            previous_error=feedback,
                            changes_made="Incorporating reviewer feedback"
                        )
                        design_input = f"{design_input}\n\nReviewer feedback: {feedback}"
                        design_retries += 1
                        
                except Exception as e:
                    error_msg = f"Design step failed: {str(e)}"
                    tracer.complete_step(step_id, error=error_msg)
                    print(f"❌ Design failed: {error_msg}")
                    break
            
            if not design_approved:
                tracer.complete_step(step_id, error="Design failed after max retries")
            
            # Step 3: Implementation with review (using plan and design as input)
            if "coder" in team_members and design_approved:
                print("💻 Implementation phase...")
                step_id = tracer.start_step("implementation", "coder_agent", {
                    "plan_input": plan_output,
                    "design_input": design_output,
                    "requirements": requirements
                })
                
                implementation_approved = False
                code_output = ""
                implementation_retries = 0
                
                while not implementation_approved and implementation_retries < max_retries:
                    try:
                        code_input = f"""You are the developer for this project. Here are the specifications:

PLAN:
{plan_output}

DESIGN:
{design_output}

Based on these specifications, implement working code that follows the design. Do NOT ask for more details - use the above information to create a complete implementation.

Original requirements: {requirements}

Write complete, working code with proper documentation."""
                        
                        code_result = await run_team_member("coder_agent", code_input)
                        code_output = str(code_result)
                        
                        # Review the implementation with monitoring
                        approved, feedback = await review_output(
                            code_output, 
                            "Implementation phase output", 
                            tracer=tracer,
                            target_agent="coder_agent"
                        )
                        
                        if approved:
                            implementation_approved = True
                            tracer.complete_step(step_id, {"implementation": code_output, "approved": True})
                            results.append(TeamMemberResult(name="coder", output=code_output))
                            print("✅ Implementation approved by reviewer")
                        else:
                            print(f"❌ Implementation needs revision: {feedback}")
                            tracer.record_retry(
                                attempt_number=implementation_retries + 1,
                                reason="Implementation revision needed",
                                previous_error=feedback,
                                changes_made="Incorporating reviewer feedback"
                            )
                            code_input = f"{code_input}\n\nReviewer feedback: {feedback}"
                            implementation_retries += 1
                            
                    except Exception as e:
                        error_msg = f"Implementation step failed: {str(e)}"
                        tracer.complete_step(step_id, error=error_msg)
                        print(f"❌ Implementation failed: {error_msg}")
                        break
                
                if not implementation_approved:
                    tracer.complete_step(step_id, error="Implementation failed after max retries")
                
                # Step 4: Final Review (using implementation as input)
                if "reviewer" in team_members and implementation_approved:
                    print("🔍 Final review phase...")
                    step_id = tracer.start_step("final_review", "reviewer_agent", {
                        "code_input": code_output,
                        "context": "Full workflow final review"
                    })
                    
                    try:
                        review_input = f"""You are conducting a final review of this implementation. Here is the complete context:

ORIGINAL REQUIREMENTS: {requirements}

PLAN:
{plan_output}

DESIGN:
{design_output}

IMPLEMENTATION:
{code_output}

Provide a comprehensive final review of this implementation, focusing on code quality, security, performance, and adherence to the design. Include any recommendations for future improvements."""
                        
                        review_result = await run_team_member("reviewer_agent", review_input)
                        review_result_text = str(review_result)
                        
                        tracer.complete_step(step_id, {"final_review": review_result_text})
                        results.append(TeamMemberResult(name="reviewer", output=review_result_text))
                        
                    except Exception as e:
                        error_msg = f"Final review step failed: {str(e)}"
                        tracer.complete_step(step_id, error=error_msg)
                        print(f"❌ Final review failed: {error_msg}")
    
    return results
