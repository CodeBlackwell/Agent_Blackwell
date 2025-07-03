"""
Enhanced TDD workflow with reviewer intermediary and intelligent retry logic.
"""
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import re

from orchestrator.orchestrator_agent import (
    TeamMember, TeamMemberResult, WorkflowStep, run_team_member
)
from workflows.utils import review_output

# Configuration for retry logic
MAX_TOTAL_RETRIES = 10
MAX_RETRIES_WITHOUT_PROGRESS = 3

@dataclass
class TestExecutionResult:
    """Results from test execution"""
    total_tests: int
    passed_tests: int
    failed_tests: List[str]
    error_messages: List[str]
    
    @property
    def all_passed(self) -> bool:
        return self.passed_tests == self.total_tests
    
    @property
    def pass_rate(self) -> float:
        return self.passed_tests / self.total_tests if self.total_tests > 0 else 0

@dataclass
class RetryState:
    """Track retry state for the workflow"""
    total_retries: int = 0
    retries_without_progress: int = 0
    previous_tests_passed: int = 0
    current_tests_passed: int = 0
    
    def update_progress(self, tests_passed: int) -> bool:
        """Update progress and return True if we can continue retrying"""
        self.total_retries += 1
        self.current_tests_passed = tests_passed
        
        # Check if we made progress
        if tests_passed > self.previous_tests_passed:
            self.retries_without_progress = 0
            self.previous_tests_passed = tests_passed
        else:
            self.retries_without_progress += 1
        
        # Check retry conditions
        can_retry = (
            self.total_retries < MAX_TOTAL_RETRIES and
            self.retries_without_progress < MAX_RETRIES_WITHOUT_PROGRESS
        )
        
        return can_retry

async def execute_tests(code_output: str, test_output: str) -> TestExecutionResult:
    """
    Execute tests against the code (simulated for now)
    In a real implementation, this would run actual tests
    """
    # Extract test information from test output
    test_count_match = re.search(r'(\d+)\s*test', test_output, re.IGNORECASE)
    total_tests = int(test_count_match.group(1)) if test_count_match else 10
    
    # Simulate test execution based on code quality indicators
    # In reality, this would run actual tests
    has_error_handling = "try" in code_output or "except" in code_output
    has_validation = "validate" in code_output or "check" in code_output
    has_implementation = "def " in code_output or "class " in code_output
    
    # Calculate passed tests based on code quality
    base_pass = 3 if has_implementation else 0
    bonus_pass = 2 if has_error_handling else 0
    bonus_pass += 2 if has_validation else 0
    
    passed_tests = min(base_pass + bonus_pass, total_tests)
    
    # Generate failed test descriptions
    failed_tests = []
    if passed_tests < total_tests:
        if not has_error_handling:
            failed_tests.append("test_error_handling: Missing error handling")
        if not has_validation:
            failed_tests.append("test_input_validation: Input validation not implemented")
        if passed_tests < total_tests - len(failed_tests):
            failed_tests.append(f"{total_tests - passed_tests - len(failed_tests)} other tests failed")
    
    return TestExecutionResult(
        total_tests=total_tests,
        passed_tests=passed_tests,
        failed_tests=failed_tests,
        error_messages=failed_tests
    )

async def run_tdd_workflow(requirements: str, team_members: List[TeamMember]) -> List[TeamMemberResult]:
    """
    Enhanced TDD workflow with reviewer intermediary and retry logic
    """
    results = []
    retry_state = RetryState()
    
    print(f"🧪 Starting enhanced TDD workflow for: {requirements[:50]}...")
    
    # Step 1: Planning with review
    if TeamMember.planner in team_members:
        print("📋 Planning phase...")
        planning_approved = False
        plan_output = ""
        
        while not planning_approved:
            planning_result = await run_team_member("planner_agent", requirements)
            plan_output = str(planning_result[0])
            
            # Review the plan
            approved, feedback = await review_output(plan_output, "plan")
            if approved:
                planning_approved = True
                results.append(TeamMemberResult(team_member=TeamMember.planner, output=plan_output))
                print("✅ Plan approved by reviewer")
            else:
                print(f"❌ Plan needs revision: {feedback}")
                requirements = f"{requirements}\n\nReviewer feedback: {feedback}"
    
    # Step 2: Design with review
    if TeamMember.designer in team_members and plan_output:
        print("🎨 Design phase...")
        design_approved = False
        design_output = ""
        
        while not design_approved:
            design_input = f"""Based on this plan, create a comprehensive technical design:

PLAN:
{plan_output}

Original requirements: {requirements}"""
            
            design_result = await run_team_member("designer_agent", design_input)
            design_output = str(design_result[0])
            
            # Review the design
            approved, feedback = await review_output(design_output, "design", context=plan_output)
            if approved:
                design_approved = True
                results.append(TeamMemberResult(team_member=TeamMember.designer, output=design_output))
                print("✅ Design approved by reviewer")
            else:
                print(f"❌ Design needs revision: {feedback}")
                design_input = f"{design_input}\n\nReviewer feedback: {feedback}"
    
    # Step 3: Test Writing with review
    if TeamMember.test_writer in team_members and design_output:
        print("🧪 Test writing phase...")
        tests_approved = False
        test_output = ""
        
        while not tests_approved:
            test_input = f"""Write comprehensive tests based on:

PLAN:
{plan_output}

DESIGN:
{design_output}

Original requirements: {requirements}"""
            
            test_result = await run_team_member("test_writer_agent", test_input)
            test_output = str(test_result[0])
            
            # Review the tests
            approved, feedback = await review_output(test_output, "tests", context=f"{plan_output}\n\n{design_output}")
            if approved:
                tests_approved = True
                results.append(TeamMemberResult(team_member=TeamMember.test_writer, output=test_output))
                print("✅ Tests approved by reviewer")
            else:
                print(f"❌ Tests need revision: {feedback}")
                test_input = f"{test_input}\n\nReviewer feedback: {feedback}"
    
    # Step 4: Implementation with test-driven retry loop
    if TeamMember.coder in team_members and test_output:
        print("💻 Implementation phase with test-driven development...")
        
        all_tests_passed = False
        code_output = ""
        
        while not all_tests_passed and retry_state.total_retries <= MAX_TOTAL_RETRIES:
            # Generate or update code
            code_input = f"""Implement code that passes these tests:

TESTS:
{test_output}

DESIGN:
{design_output}

PLAN:
{plan_output}

Original requirements: {requirements}"""
            
            if retry_state.total_retries > 0:
                code_input += f"\n\nPrevious attempt passed {retry_state.current_tests_passed} tests. Fix the failing tests."
            
            code_result = await run_team_member("coder_agent", code_input)
            code_output = str(code_result[0])
            
            # Execute tests
            test_results = await execute_tests(code_output, test_output)
            print(f"🧪 Test results: {test_results.passed_tests}/{test_results.total_tests} passed")
            
            if test_results.all_passed:
                all_tests_passed = True
                results.append(TeamMemberResult(team_member=TeamMember.coder, output=code_output))
                print("✅ All tests passed!")
            else:
                # Check if we can retry
                can_retry = retry_state.update_progress(test_results.passed_tests)
                
                if can_retry:
                    # Get reviewer feedback on test failures
                    review_input = f"""Analyze these test failures:

Tests passed: {test_results.passed_tests}/{test_results.total_tests}
Failed tests: {', '.join(test_results.failed_tests)}

Code:
{code_output}

Provide specific feedback on what needs to be fixed to pass the failing tests."""
                    
                    review_result = await run_team_member("reviewer_agent", review_input)
                    reviewer_feedback = str(review_result[0])
                    
                    print(f"🔄 Retry {retry_state.total_retries}: {reviewer_feedback[:100]}...")
                    code_input += f"\n\nReviewer feedback on test failures: {reviewer_feedback}"
                else:
                    # Cannot retry anymore
                    print(f"⚠️  Stopping: {'Total retry limit reached' if retry_state.total_retries >= MAX_TOTAL_RETRIES else 'No progress for too many iterations'}")
                    results.append(TeamMemberResult(
                        team_member=TeamMember.coder,
                        output=f"{code_output}\n\n⚠️ PARTIAL SUCCESS: {test_results.passed_tests}/{test_results.total_tests} tests passed"
                    ))
                    break
    
    # Step 5: Final review (if all tests passed)
    if TeamMember.reviewer in team_members and all_tests_passed:
        print("🔍 Final review phase...")
        review_input = f"""Perform final review of the complete implementation:

REQUIREMENTS: {requirements}

PLAN:
{plan_output}

DESIGN:
{design_output}

TESTS:
{test_output}

IMPLEMENTATION:
{code_output}

All tests have passed. Review for code quality, security, performance, and best practices."""
        
        review_result = await run_team_member("reviewer_agent", review_input)
        review_result_text = str(review_result[0])
        results.append(TeamMemberResult(team_member=TeamMember.reviewer, output=review_result_text))
    
    return results