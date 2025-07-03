"""
TDD Workflow Implementation

This module implements the Test-Driven Development workflow with comprehensive monitoring.
"""
import asyncio
import sys
import importlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

# Add the project root to the Python path FIRST before any local imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Now import shared data models
from shared.data_models import (
    TeamMember, WorkflowStep, CodingTeamInput, TeamMemberResult
)

# Import orchestrator function
from orchestrator.orchestrator_agent import run_team_member

# Import monitoring components
from workflows.monitoring import WorkflowExecutionTracer, WorkflowExecutionReport, StepStatus, ReviewDecision

# Import configuration
from workflows.workflow_config import MAX_REVIEW_RETRIES

# Ensure utils module is properly loaded and import review_output
import workflows.utils as utils_module
review_output = utils_module.review_output

async def execute_tdd_workflow(input_data: CodingTeamInput, tracer: Optional[WorkflowExecutionTracer] = None) -> Tuple[List[TeamMemberResult], WorkflowExecutionReport]:
    """
    Execute the TDD workflow with comprehensive monitoring.
    
    Args:
        input_data: The input data containing requirements and workflow configuration
        tracer: Optional tracer for monitoring execution (creates new one if not provided)
        
    Returns:
        Tuple of (team member results, execution report)
    """
    # Create tracer if not provided
    if tracer is None:
        tracer = WorkflowExecutionTracer(
            workflow_type="TDD",
            execution_id=f"tdd_{int(asyncio.get_event_loop().time())}"
        )
    
    # Initialize results list
    results = []
    
    try:
        # Planning phase
        step_id = tracer.start_step("planning", "planner_agent", {"requirements": input_data.requirements})
        planning_result = await run_team_member(
            "planner_agent",
            input_data.requirements
        )
        planning_output = str(planning_result)
        results.append(TeamMemberResult(
            team_member=TeamMember.planner,
            output=planning_output,
            name="planner"
        ))
        tracer.complete_step(step_id, {"output": planning_output[:200] + "..."})
        
        # Review planning
        approved, feedback = await review_output(
            planning_output, 
            "planning", 
            tracer=tracer,
            target_agent="planner_agent"
        )
        
        # Handle planning revisions if needed
        retry_count = 0
        while not approved and retry_count < input_data.max_retries:
            tracer.record_retry(
                attempt_number=retry_count + 1,
                reason=f"Planning revision needed: {feedback}"
            )
            
            # Retry planning with feedback
            step_id = tracer.start_step(f"planning_retry_{retry_count+1}", "planner_agent", {"feedback": feedback})
            planning_result = await run_team_member(
                "planner_agent",
                f"{input_data.requirements}\n\nFeedback from review: {feedback}"
            )
            planning_output = str(planning_result)
            results.append(TeamMemberResult(
                team_member=TeamMember.planner,
                output=planning_output,
                name="planner"
            ))
            tracer.complete_step(step_id, {"output": planning_output[:200] + "..."})
            
            # Review revised planning
            approved, feedback = await review_output(
                planning_output, 
                "planning", 
                tracer=tracer,
                target_agent="planner_agent"
            )
            retry_count += 1
        
        # Design phase
        step_id = tracer.start_step("design", "designer_agent", {
            "plan_input": planning_output[:200] + "...",
            "requirements": input_data.requirements
        })
        design_input = f"Plan:\n{planning_output}\n\nRequirements: {input_data.requirements}"
        design_result = await run_team_member("designer_agent", design_input)
        design_output = str(design_result)
        results.append(TeamMemberResult(
            team_member=TeamMember.designer,
            output=design_output,
            name="designer"
        ))
        tracer.complete_step(step_id, {"output": design_output[:200] + "..."})
        
        # Review design
        approved, feedback = await review_output(
            design_output, 
            "design", 
            tracer=tracer,
            target_agent="designer_agent"
        )
        
        # Test writing phase
        step_id = tracer.start_step("test_writing", "test_writer_agent", {
            "plan_input": planning_output[:200] + "...",
            "design_input": design_output[:200] + "..."
        })
        test_input = f"Requirements: {input_data.requirements}\n\nPlan: {planning_output}\n\nDesign: {design_output}"
        test_result = await run_team_member("test_writer_agent", test_input)
        test_output = str(test_result)
        results.append(TeamMemberResult(
            team_member=TeamMember.test_writer,
            output=test_output,
            name="test_writer"
        ))
        tracer.complete_step(step_id, {"output": test_output[:200] + "..."})
        
        # Review tests
        approved, feedback = await review_output(
            test_output, 
            "test_writing", 
            tracer=tracer,
            target_agent="test_writer_agent"
        )
        
        # Coding phase
        step_id = tracer.start_step("coding", "coder_agent", {
            "test_input": test_output[:200] + "...",
            "design_input": design_output[:200] + "..."
        })
        coding_input = f"Requirements: {input_data.requirements}\n\nPlan: {planning_output}\n\nDesign: {design_output}\n\nTests: {test_output}"
        code_result = await run_team_member("coder_agent", coding_input)
        code_output = str(code_result)
        results.append(TeamMemberResult(
            team_member=TeamMember.coder,
            output=code_output,
            name="coder"
        ))
        tracer.complete_step(step_id, {"output": code_output[:200] + "..."})
        
        # Final review
        step_id = tracer.start_step("final_review", "reviewer_agent", {
            "code_input": code_output[:200] + "...",
            "context": "TDD workflow final review"
        })
        review_input = f"Requirements: {input_data.requirements}\n\nCode: {code_output}\n\nTests: {test_output}"
        review_result = await run_team_member("reviewer_agent", review_input)
        review_output = str(review_result)
        results.append(TeamMemberResult(
            team_member=TeamMember.reviewer,
            output=review_output,
            name="reviewer"
        ))
        tracer.complete_step(step_id, {"output": review_output[:200] + "..."})
        
        # Complete workflow execution
        tracer.complete_execution(final_output={
            "workflow": "TDD",
            "results_count": len(results),
            "success": True
        })
        
    except Exception as e:
        # Handle exceptions and complete workflow with error
        error_msg = f"TDD workflow error: {str(e)}"
        tracer.complete_execution(error=error_msg)
        raise
    
    # Return results and execution report
    return results, tracer.get_report()


# Legacy function for backward compatibility
async def run_tdd_workflow(requirements: str, tracer: Optional[WorkflowExecutionTracer] = None) -> List[TeamMemberResult]:
    """
    Legacy wrapper for backward compatibility.
    """
    input_data = CodingTeamInput(
        requirements=requirements,
        workflow_type="TDD",
        step_type=None,
        max_retries=3,
        timeout_seconds=600
    )
    
    results, _ = await execute_tdd_workflow(input_data, tracer)
    return results