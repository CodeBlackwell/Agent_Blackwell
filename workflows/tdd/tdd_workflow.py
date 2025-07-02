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
                
                # Step 4: Implementation (TDD-guided)
    if TeamMember.coder in team_members:
        print("💻 Implementation phase (TDD-guided)...")
        code_result = await run_team_member("coder_agent", code_input)
        code_output = str(code_result[0])
        results.append(TeamMemberResult(team_member=TeamMember.coder, output=code_output))
        
        # Extract project path from coder output
        project_path = extract_project_path(code_output)
        
        if project_path:
            # Step 4.5: Test Execution
            print("🧪 Running tests...")
            from orchestrator.test_runner_tool import TestRunnerTool
            
            test_runner = TestRunnerTool()
            test_result = await test_runner._run(
                TestExecutionInput(project_path=project_path),
                None,
                None
            )
            
            test_summary = f"""
TEST EXECUTION RESULTS:
{test_result.get_text_content()}

Project Path: {project_path}
"""
            results.append(TeamMemberResult(
                team_member=TeamMember.coder,  # Or create a new "test_runner" member
                output=test_summary
            ))
            
            # If tests fail, could loop back to coder
            if not test_result.result.success:
                print("❌ Tests failed, sending feedback to coder...")
                fix_input = f"""Tests failed. Please fix the implementation:
                
{test_summary}

Previous implementation:
{code_output}

Fix the code to make all tests pass."""
                
                fix_result = await run_team_member("coder_agent", fix_input)
                fix_output = str(fix_result[0])
                results.append(TeamMemberResult(
                    team_member=TeamMember.coder,
                    output=f"FIX ATTEMPT:\n{fix_output}"
                ))
        
        # Step 5: Review (include test results)
        if TeamMember.reviewer in team_members:
            review_input = f"""{review_input}

TEST RESULTS:
{test_summary if project_path else "No tests were executed"}"""
            # ... continue with review ...

def extract_project_path(coder_output: str) -> Optional[str]:
    """Extract project path from coder output"""
    import re
    # Look for path patterns in output
    path_match = re.search(r'Location: (.+?)(?:\n|$)', coder_output)
    if path_match:
        return path_match.group(1).strip()
    
    # Fallback: look for generated directory pattern
    gen_match = re.search(r'orchestrator/generated/(.+?)(?:\n|$)', coder_output)
    if gen_match:
        return f"orchestrator/generated/{gen_match.group(1)}"
    
    return None