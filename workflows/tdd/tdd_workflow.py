"""
TDD workflow implementation.
"""
from typing import List

from orchestrator.orchestrator_agent import (
    TeamMember, TeamMemberResult, WorkflowStep, run_team_member
)

async def run_tdd_workflow(requirements: str, team_members: List[TeamMember]) -> List[TeamMemberResult]:
    """
    Run TDD workflow: planner -> designer -> test_writer -> coder -> reviewer
    
    Args:
        requirements: The project requirements
        team_members: Team members to involve in the process
        
    Returns:
        List of team member results
    """
    results = []
    
    print(f"🧪 Starting TDD workflow for: {requirements[:50]}...")
    
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
            
            # Step 3: Test Writing (using plan and design as input)
            if TeamMember.test_writer in team_members:
                print("🧪 Test writing phase...")
                test_input = f"""You are the test writer for this project. Here is the plan and design:

PLAN:
{plan_output}

DESIGN:
{design_output}

Based on this plan and design, write comprehensive business-value focused tests. Do NOT ask for more details - extract the business requirements from the above information and create test scenarios.

Original requirements: {requirements}

Write Given-When-Then test scenarios that validate business outcomes."""
                test_result = await run_team_member("test_writer_agent", test_input)
                test_output = str(test_result[0])
                results.append(TeamMemberResult(team_member=TeamMember.test_writer, output=test_output))
                
                # Step 4: Implementation (using tests to guide development)
                if TeamMember.coder in team_members:
                    print("💻 Implementation phase (TDD-guided)...")
                    code_input = f"""You are the developer for this project. Here are the specifications:

PLAN:
{plan_output}

DESIGN:
{design_output}

TESTS TO SATISFY:
{test_output}

Based on these specifications, implement working code that satisfies the tests and follows the design. Do NOT ask for more details - use the above information to create a complete implementation.

Original requirements: {requirements}

Write complete, working code with proper documentation."""
                    code_result = await run_team_member("coder_agent", code_input)
                    code_output = str(code_result[0])
                    results.append(TeamMemberResult(team_member=TeamMember.coder, output=code_output))
                    
                    # Step 5: Review (using implementation as input)
                    if TeamMember.reviewer in team_members:
                        print("🔍 Review phase...")
                        review_input = f"""You are reviewing this TDD implementation. Here is the complete context:

ORIGINAL REQUIREMENTS: {requirements}

TESTS THAT SHOULD BE SATISFIED:
{test_output}

IMPLEMENTATION TO REVIEW:
{code_output}

Review this implementation for code quality, security, performance, and adherence to the tests. Provide specific feedback and recommendations."""
                        review_result = await run_team_member("reviewer_agent", review_input)
                        review_output = str(review_result[0])
                        results.append(TeamMemberResult(team_member=TeamMember.reviewer, output=review_output))
    
    return results
