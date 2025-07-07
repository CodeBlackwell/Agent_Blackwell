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

# Remove direct import of run_team_member - will import dynamically in functions
# from orchestrator.orchestrator_agent import run_team_member

# Import monitoring components
from workflows.monitoring import WorkflowExecutionTracer, WorkflowExecutionReport, StepStatus, ReviewDecision

# Import configuration
from workflows.workflow_config import MAX_REVIEW_RETRIES
from workflows.tdd.tdd_config import WORKFLOW_CONFIG, TEST_CONFIG

# Import output handler
from workflows.agent_output_handler import get_output_handler

# Import executor components
from agents.executor.session_utils import generate_session_id

# Import TDD components
from workflows.tdd.tdd_cycle_manager import TDDCycleManager, TDDPhase
from workflows.tdd.test_executor import TestExecutor

# Import logger
from workflows.logger import workflow_logger as logger

# Import CodeSaver for session management
from workflows.mvp_incremental.code_saver import CodeSaver



async def execute_tdd_workflow(input_data: CodingTeamInput, tracer: Optional[WorkflowExecutionTracer] = None) -> Tuple[List[TeamMemberResult], WorkflowExecutionReport]:
    """
    Execute the TDD workflow with comprehensive monitoring.
    
    Args:
        input_data: The input data containing requirements and workflow configuration
        tracer: Optional tracer for monitoring execution (creates new one if not provided)
        
    Returns:
        Tuple of (team member results, execution report)
    """
    # Import utils module for review_output function
    import workflows.workflow_utils as utils_module
    # Correctly reference the async review_output function
    review_output = utils_module.review_output
    # Import run_team_member dynamically to avoid circular imports
    from orchestrator.orchestrator_agent import run_team_member_with_tracking
    
    # Create tracer if not provided
    if tracer is None:
        tracer = WorkflowExecutionTracer(
            workflow_type="TDD",
            execution_id=f"tdd_{int(asyncio.get_event_loop().time())}"
        )
    
    # Initialize results list
    results = []
    
    # Import session config
    from workflows.tdd.tdd_config import SESSION_CONFIG
    
    # Initialize CodeSaver for session management
    code_saver = CodeSaver()
    session_name = None
    project_path = None
    
    # Create session directory if configured
    if SESSION_CONFIG.get("use_single_directory", True):
        # Extract project name from requirements if possible
        req_lower = input_data.requirements.lower()
        if "calculator" in req_lower:
            session_name = "calculator"
        elif "todo" in req_lower:
            session_name = "todo_app"
        elif "string" in req_lower and "util" in req_lower:
            session_name = "string_utils"
        else:
            session_name = SESSION_CONFIG.get("session_name_prefix", "tdd")
        
        # Create the session directory
        project_path = code_saver.create_session_directory(session_name)
        logger.info(f"Created TDD session directory: {project_path}")
    
    try:
        # Planning phase
        step_id = tracer.start_step("planning", "planner_agent", {"requirements": input_data.requirements})
        planning_result = await run_team_member_with_tracking(
            "planner_agent",
            input_data.requirements,
            "tdd_planning"
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
            # Get output handler for retry notification
            output_handler = get_output_handler()
            if output_handler:
                output_handler.on_retry("planner_agent", retry_count + 1, f"Planning revision needed: {feedback}")
            
            tracer.record_retry(
                attempt_number=retry_count + 1,
                reason=f"Planning revision needed: {feedback}"
            )
            
            # Retry planning with feedback
            step_id = tracer.start_step(f"planning_retry_{retry_count+1}", "planner_agent", {"feedback": feedback})
            planning_result = await run_team_member_with_tracking(
                "planner_agent",
                f"{input_data.requirements}\n\nFeedback from review: {feedback}",
                f"tdd_planning_retry_{retry_count+1}"
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
        design_result = await run_team_member_with_tracking("designer_agent", design_input, "tdd_design")
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
        test_result = await run_team_member_with_tracking("test_writer_agent", test_input, "tdd_test_writing")
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
        
        # TDD Cycle: RED-GREEN-REFACTOR
        if TEST_CONFIG.get("execute_real_tests", True) and TEST_CONFIG.get("use_tdd_cycle", True):
            # Use proper TDD cycle with test execution
            output_handler = get_output_handler()
            logger.info("🔄 Starting TDD Red-Green-Refactor cycle")
            
            # Initialize TDD cycle manager
            tdd_manager = TDDCycleManager(
                max_iterations=TEST_CONFIG.get("max_iterations", 5),
                require_test_failure=TEST_CONFIG.get("test_before_code", True)
            )
            
            # Set the project path if available
            if project_path and hasattr(tdd_manager, 'file_manager'):
                from workflows.tdd.file_manager import ProjectInfo
                tdd_manager.file_manager.current_project = ProjectInfo(
                    project_name=session_name or "tdd_project",
                    project_path=project_path,
                    files={},
                    timestamp=code_saver.current_session_path.name.split('_')[0] if code_saver.current_session_path else ""
                )
            
            # Execute TDD cycle
            tdd_step_id = tracer.start_step("tdd_cycle", "tdd_cycle_manager", {
                "test_output": test_output[:200] + "...",
                "requirements": input_data.requirements
            })
            
            try:
                # Run TDD cycle with test execution
                cycle_result = await tdd_manager.execute_tdd_cycle(
                    requirements=input_data.requirements,
                    test_code=test_output,
                    existing_code={}  # No existing code for new project
                )
                
                # Use the implementation from TDD cycle
                code_output = cycle_result.implementation_code
                
                # Add TDD cycle metrics to tracer
                tracer.complete_step(tdd_step_id, {
                    "success": cycle_result.success,
                    "iterations": cycle_result.iterations,
                    "initial_failures": cycle_result.initial_test_result.failed_tests,
                    "final_passes": cycle_result.final_test_result.passed_tests,
                    "all_tests_passing": cycle_result.final_test_result.all_passing
                })
                
                # Log TDD results
                status_msg = f"TDD cycle completed: {cycle_result.final_test_result.passed_tests}/{cycle_result.final_test_result.total_tests} tests passing"
                if cycle_result.final_test_result.coverage_percent:
                    status_msg += f" (Coverage: {cycle_result.final_test_result.coverage_percent}%)"
                logger.info(f"✅ {status_msg}")
                
                # If not all tests are passing, log warnings
                if not cycle_result.success:
                    logger.warning(f"TDD cycle completed with failures: {cycle_result.final_test_result.failed_tests} tests still failing")
                
            except Exception as e:
                # Fallback to standard coding if TDD cycle fails
                logger.error(f"TDD cycle failed: {str(e)}")
                tracer.complete_step(tdd_step_id, {"error": str(e)}, error=str(e))
                
                # Use standard coding approach with TDD mindset
                step_id = tracer.start_step("coding_fallback", "coder_agent", {
                    "reason": "TDD cycle failed, using standard approach"
                })
                
                # Create TDD-focused context even for fallback
                coding_input = f"""Using Test-Driven Development approach.

REQUIREMENTS:
{input_data.requirements}

PLAN:
{planning_output}

DESIGN:
{design_output}

TESTS TO PASS:
{test_output}

Please implement the minimal code needed to make all the tests pass."""
                
                code_result = await run_team_member_with_tracking("coder_agent", coding_input, "tdd_coding_fallback")
                code_output = str(code_result)
                tracer.complete_step(step_id, {"output": code_output[:200] + "..."})
        else:
            # Standard coding phase (backward compatibility)
            step_id = tracer.start_step("coding", "coder_agent", {
                "test_input": test_output[:200] + "...",
                "design_input": design_output[:200] + "..."
            })
            coding_input = f"Requirements: {input_data.requirements}\n\nPlan: {planning_output}\n\nDesign: {design_output}\n\nTests: {test_output}"
            code_result = await run_team_member_with_tracking("coder_agent", coding_input, "tdd_coding")
            code_output = str(code_result)
            tracer.complete_step(step_id, {"output": code_output[:200] + "..."})
        
        # Add code result
        results.append(TeamMemberResult(
            team_member=TeamMember.coder,
            output=code_output,
            name="coder"
        ))
        
        # Step 4.5: Execute tests and code
        session_id = generate_session_id(input_data.requirements)
        
        if TeamMember.executor in input_data.team_members:
            print("🐳 Executing tests and code...")
            step_id = tracer.start_step("execution", "executor_agent", {
                "session_id": session_id,
                "code": code_output[:200] + "...",
                "tests": test_output[:200] + "..."
            })
            
            # Prepare execution input with session ID
            execution_input = f"""SESSION_ID: {session_id}

Execute the following code and tests:

{code_output}

{test_output}
"""
            
            execution_result = await run_team_member_with_tracking("executor_agent", execution_input, "tdd_execution")
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
            
            # Include execution results in review
            review_input = f"""Requirements: {input_data.requirements}

Code: {code_output}

Tests: {test_output}

Execution Results:
{execution_output}

Please review the code, tests, AND execution results."""
        else:
            review_input = f"Requirements: {input_data.requirements}\n\nCode: {code_output}\n\nTests: {test_output}"
        
        # Final review - FIX: Use review_result_output instead of review_output
        step_id = tracer.start_step("final_review", "reviewer_agent", {
            "code_input": code_output[:200] + "...",
            "context": "TDD workflow final review"
        })
        # review_input is already set conditionally above based on whether executor is present
        review_result = await run_team_member_with_tracking("reviewer_agent", review_input, "tdd_final_review")
        review_result_output = str(review_result)  # Convert result to string
        results.append(TeamMemberResult(
            team_member=TeamMember.reviewer,
            output=review_result_output,  # Use the string output
            name="reviewer"
        ))
        tracer.complete_step(step_id, {"output": review_result_output[:200] + "..."})  # Use the string output
        
        # Save all generated code to session directory if configured
        if SESSION_CONFIG.get("use_single_directory", True) and code_saver.current_session_path:
            try:
                # Parse files from code output
                from workflows.tdd.file_manager import TDDFileManager
                file_manager = TDDFileManager()
                
                # Parse implementation files from code output
                impl_files = file_manager.parse_files(code_output, extract_location=False)
                
                # Parse test files from test output
                test_files = file_manager.parse_files(test_output, extract_location=False)
                
                # Combine all files
                all_files = {}
                all_files.update(impl_files)
                all_files.update(test_files)
                
                # Save all files to the session directory
                if all_files:
                    saved_paths = code_saver.save_code_files(all_files, overwrite=True)
                    logger.info(f"Saved {len(saved_paths)} files to session directory")
                    
                    # Save metadata if configured
                    if SESSION_CONFIG.get("save_metadata", True):
                        metadata = {
                            "workflow_type": "TDD",
                            "requirements": input_data.requirements,
                            "project_name": session_name or "tdd_project",
                            "total_iterations": cycle_result.iterations if 'cycle_result' in locals() else 1,
                            "test_results": {
                                "passed": cycle_result.final_test_result.passed_tests if 'cycle_result' in locals() else 0,
                                "total": cycle_result.final_test_result.total_tests if 'cycle_result' in locals() else 0
                            }
                        }
                        code_saver.save_metadata(metadata)
                        
                    # Create README if we have project info
                    if session_name:
                        features = [f"TDD implementation of {session_name}"]
                        if 'cycle_result' in locals() and cycle_result.success:
                            features.append(f"All {cycle_result.final_test_result.total_tests} tests passing")
                        
                        code_saver.create_readme(
                            project_name=session_name,
                            description=f"Test-Driven Development implementation based on: {input_data.requirements[:100]}",
                            features=features,
                            setup_instructions=["1. Install dependencies", "2. Run tests with pytest", "3. Run the application"]
                        )
                        
                    logger.info(f"✅ TDD workflow completed. Project saved to: {code_saver.current_session_path}")
                    
            except Exception as save_error:
                logger.error(f"Error saving files to session directory: {str(save_error)}")
                # Don't fail the workflow if saving fails
        
        # Complete workflow execution
        tracer.complete_execution(final_output={
            "workflow": "TDD",
            "results_count": len(results),
            "success": True,
            "project_path": str(code_saver.current_session_path) if code_saver.current_session_path else None
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