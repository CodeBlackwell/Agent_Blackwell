"""
Full workflow implementation.
"""
from typing import List

from orchestrator.orchestrator_agent import (
    TeamMember, TeamMemberResult, WorkflowStep, run_team_member
)
from workflows.utils import review_output
from workflows.workflow_config import MAX_REVIEW_RETRIES

async def run_full_workflow(requirements: str, team_members: List[TeamMember]) -> List[TeamMemberResult]:
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
    if TeamMember.planner in team_members:
        print("📋 Planning phase...")
        planning_approved = False
        plan_output = ""
        planning_retries = 0
        
        while not planning_approved:
            planning_result = await run_team_member("planner_agent", requirements)
            plan_output = str(planning_result[0])
            
            # Review the plan
            approved, feedback = await review_output(plan_output, "plan", max_retries=max_retries, current_retry=planning_retries)
            if approved:
                planning_approved = True
                results.append(TeamMemberResult(team_member=TeamMember.planner, output=plan_output))
                print("✅ Plan approved by reviewer")
            else:
                print(f"❌ Plan needs revision: {feedback}")
                planning_input = f"{requirements}\n\nReviewer feedback: {feedback}"
                planning_retries += 1
        
        # Step 2: Design with review (using plan as input)
        if TeamMember.designer in team_members:
            print("🎨 Design phase...")
            design_approved = False
            design_output = ""
            design_retries = 0
            
            while not design_approved:
                design_input = f"""You are the designer for this project. Here is the detailed plan:

{plan_output}

Based on this plan, create a comprehensive technical design. Do NOT ask for more details - use the plan above to extract all technical requirements and create concrete designs.

Original requirements: {requirements}

Create the technical architecture, database schemas, API endpoints, and component designs."""
                
                design_result = await run_team_member("designer_agent", design_input)
                design_output = str(design_result[0])
                
                # Review the design
                approved, feedback = await review_output(design_output, "design", context=plan_output, max_retries=max_retries, current_retry=design_retries)
                if approved:
                    design_approved = True
                    results.append(TeamMemberResult(team_member=TeamMember.designer, output=design_output))
                    print("✅ Design approved by reviewer")
                else:
                    print(f"❌ Design needs revision: {feedback}")
                    design_input = f"{design_input}\n\nReviewer feedback: {feedback}"
                    design_retries += 1
            
            # Step 3: Implementation with review (using plan and design as input)
            if TeamMember.coder in team_members:
                print("💻 Implementation phase...")
                implementation_approved = False
                code_output = ""
                implementation_retries = 0
                
                while not implementation_approved:
                    code_input = f"""You are the developer for this project. Here are the specifications:

PLAN:
{plan_output}

DESIGN:
{design_output}

Based on these specifications, implement working code that follows the design. Do NOT ask for more details - use the above information to create a complete implementation.

Original requirements: {requirements}

Write complete, working code with proper documentation."""
                    
                    code_result = await run_team_member("coder_agent", code_input)
                    code_output = str(code_result[0])
                    
                    # Review the implementation
                    approved, feedback = await review_output(code_output, "implementation", context=f"{plan_output}\n\n{design_output}", max_retries=max_retries, current_retry=implementation_retries)
                    if approved:
                        implementation_approved = True
                        results.append(TeamMemberResult(team_member=TeamMember.coder, output=code_output))
                        print("✅ Implementation approved by reviewer")
                    else:
                        print(f"❌ Implementation needs revision: {feedback}")
                        code_input = f"{code_input}\n\nReviewer feedback: {feedback}"
                        implementation_retries += 1
                
                # Step 4: Final Review (using implementation as input)
                if TeamMember.reviewer in team_members:
                    print("🔍 Final review phase...")
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
                    review_result_text = str(review_result[0])
                    results.append(TeamMemberResult(team_member=TeamMember.reviewer, output=review_result_text))
    
    return results
