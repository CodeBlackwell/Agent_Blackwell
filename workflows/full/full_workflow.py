"""
Full workflow implementation.
"""
from typing import List

from orchestrator.orchestrator_agent import (
    TeamMember, TeamMemberResult, WorkflowStep, run_team_member
)

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
    
    print(f"🔄 Starting full workflow for: {requirements[:50]}...")
    
    # Step 1: Planning
    if TeamMember.planner in team_members:
        print("📋 Planning phase...")
        planning_result = await run_team_member("planner_agent", requirements)
        plan_output = str(planning_result[0])
        results.append(TeamMemberResult(team_member=TeamMember.planner, output=plan_output))
        
        # Step 2: Design (using plan as input)
        if TeamMember.designer in team_members:
            print("🎨 Design phase...")
            design_input = f"""You are the designer for this project. Here is the detailed plan:

{plan_output}

Based on this plan, create a comprehensive technical design. Do NOT ask for more details - use the plan above to extract all technical requirements and create concrete designs.

Original requirements: {requirements}

Create the technical architecture, database schemas, API endpoints, and component designs."""
            design_result = await run_team_member("designer_agent", design_input)
            design_output = str(design_result[0])
            results.append(TeamMemberResult(team_member=TeamMember.designer, output=design_output))
            
            # Step 3: Implementation (using plan and design as input)
            if TeamMember.coder in team_members:
                print("💻 Implementation phase...")
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
                results.append(TeamMemberResult(team_member=TeamMember.coder, output=code_output))
                
                # Step 4: Review (using implementation as input)
                if TeamMember.reviewer in team_members:
                    print("🔍 Review phase...")
                    review_input = f"""You are reviewing this implementation. Here is the complete context:

ORIGINAL REQUIREMENTS: {requirements}

PLAN:
{plan_output}

DESIGN:
{design_output}

IMPLEMENTATION TO REVIEW:
{code_output}

Review this implementation for code quality, security, performance, and adherence to the design. Provide specific feedback and recommendations."""
                    review_result = await run_team_member("reviewer_agent", review_input)
                    review_output = str(review_result[0])
                    results.append(TeamMemberResult(team_member=TeamMember.reviewer, output=review_output))
    
    return results
