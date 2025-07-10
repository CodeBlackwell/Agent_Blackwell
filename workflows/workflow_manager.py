"""
Workflow manager for coordinating different workflow implementations.
"""
from typing import List, Optional, Tuple
import asyncio
import traceback
import importlib

# Import verification function
def verify_imports():
    """Verify all imports are working correctly and print diagnostics"""
    print("\n===== WORKFLOW IMPORT VERIFICATION =====")
    
    # Try to get debug logger if available
    debug_logger = None
    try:
        from demos.lib.debug_logger import get_debug_logger
        debug_logger = get_debug_logger()
    except:
        pass
    
    import_checks = {
        "shared.data_models": ["TeamMember", "TeamMemberResult", "CodingTeamInput", "WorkflowStep"],
        "workflows.tdd.tdd_workflow": ["execute_tdd_workflow"],
        "workflows.full.full_workflow": ["execute_full_workflow"],
        "workflows.individual.individual_workflow": ["execute_individual_workflow"],
        "workflows.incremental.incremental_workflow": ["execute_incremental_workflow"],
        "workflows.mvp_incremental.mvp_incremental": ["execute_mvp_incremental_workflow"],
        "workflows.monitoring": ["WorkflowExecutionTracer", "WorkflowExecutionReport"]
    }
    
    all_imports_successful = True
    
    for module_name, items in import_checks.items():
        try:
            module = importlib.import_module(module_name)
            print(f"✅ Successfully imported {module_name}")
            
            # Check if each expected item exists in the module
            items_found = []
            for item in items:
                if hasattr(module, item):
                    print(f"  ✅ Found {item} in {module_name}")
                    items_found.append(item)
                else:
                    print(f"  ❌ ERROR: {item} not found in {module_name}")
                    all_imports_successful = False
            
            # Log to debug logger if available
            if debug_logger:
                debug_logger.log_import_verification(
                    module_name, items, True, 
                    error=None if len(items_found) == len(items) else f"Missing items: {set(items) - set(items_found)}"
                )
                    
        except Exception as e:
            print(f"❌ ERROR importing {module_name}: {str(e)}")
            all_imports_successful = False
            
            # Log to debug logger if available
            if debug_logger:
                debug_logger.log_import_verification(
                    module_name, items, False, error=str(e)
                )
    
    if all_imports_successful:
        print("✅ All imports verified successfully")
    else:
        print("❌ Some imports failed - workflow may not function correctly")
    
    return all_imports_successful

# Run import verification
verify_imports()

# Import shared data models
from shared.data_models import (
    TeamMember, 
    TeamMemberResult, 
    CodingTeamInput
)

# Import workflow implementations
from workflows.tdd.tdd_workflow import execute_tdd_workflow
from workflows.full.full_workflow import execute_full_workflow
from workflows.individual.individual_workflow import execute_individual_workflow
from workflows.incremental.incremental_workflow import execute_incremental_workflow
from workflows.mvp_incremental.mvp_incremental import execute_mvp_incremental_workflow
from workflows.mvp_incremental.mvp_incremental_tdd import execute_mvp_incremental_tdd_workflow
from workflows.monitoring import WorkflowExecutionTracer, WorkflowExecutionReport

# Import Docker manager for cleanup
from agents.executor.docker_manager import DockerEnvironmentManager


async def execute_workflow(input_data: CodingTeamInput, 
                          tracer: Optional[WorkflowExecutionTracer] = None) -> Tuple[List[TeamMemberResult], WorkflowExecutionReport]:
    """
    Execute a workflow based on the specified type with comprehensive monitoring.
    
    Args:
        input_data: The input data containing workflow type and requirements
        tracer: Optional tracer for monitoring execution (creates new one if not provided)
        
    Returns:
        Tuple of (team member results, execution report)
    """
    import logging
    logger = logging.getLogger("workflow_manager")
    
    logger.info("\n===== WORKFLOW EXECUTION STARTED =====")
    logger.info(f"Input type: {type(input_data).__name__}")
    logger.info(f"Requirements preview: {input_data.requirements[:200]}..." if len(input_data.requirements) > 200 else f"Requirements: {input_data.requirements}")
    
    # Extract workflow type properly
    workflow_type = None
    
    # First check workflow_type field (new style)
    if hasattr(input_data, 'workflow_type') and input_data.workflow_type:
        workflow_type = input_data.workflow_type.lower()
        logger.info(f"🎯 Workflow type: {workflow_type}")
    # Then check workflow field (legacy style with enum)
    elif hasattr(input_data, 'workflow') and input_data.workflow:
        # Handle enum value
        if hasattr(input_data.workflow, 'value'):
            workflow_type = input_data.workflow.value.replace('_workflow', '').lower()
            logger.info(f"🎯 Workflow type (enum): {workflow_type}")
        else:
            workflow_type = str(input_data.workflow).replace('_workflow', '').lower()
            logger.info(f"🎯 Workflow type (string): {workflow_type}")
    
    # Validate workflow type
    if not workflow_type:
        logger.error("❌ No workflow type specified in input data")
        raise ValueError("No workflow type specified in input data")
    
    # Normalize workflow type
    workflow_type = workflow_type.strip().lower()
    logger.info(f"📋 Normalized workflow: {workflow_type}")
    
    # Create tracer if not provided
    if tracer is None:
        logger.info("📊 Creating new execution tracer")
        tracer = WorkflowExecutionTracer(workflow_type)
    else:
        logger.info("📊 Using provided execution tracer")
    
    # Add input metadata to tracer
    logger.info(f"📝 Adding metadata to tracer")
    tracer.add_metadata('input_requirements', input_data.requirements)
    tracer.add_metadata('workflow_type', workflow_type)
    
    # Add team members if available
    if hasattr(input_data, 'team_members') and input_data.team_members:
        logger.info(f"👥 Processing team members: {len(input_data.team_members)}")
        team_member_names = []
        for member in input_data.team_members:
            if hasattr(member, 'name'):
                team_member_names.append(member.name)
            elif hasattr(member, 'value'):
                team_member_names.append(member.value)
            else:
                team_member_names.append(str(member))
        tracer.add_metadata('team_members', team_member_names)
        logger.info(f"👥 Team: {', '.join(team_member_names)}")
    
    try:
        # Log workflow start
        logger.info(f"🚀 Executing {workflow_type} workflow...")
        
        # Execute the appropriate workflow with monitoring
        if workflow_type == "tdd" or workflow_type == "tdd_workflow":
            logger.info(f"🧪 Executing TDD (Test-Driven Development) workflow")
            results = await execute_tdd_workflow(input_data, tracer)
            logger.info(f"✅ TDD workflow completed successfully")
        elif workflow_type == "full" or workflow_type == "full_workflow":
            logger.info(f"📋 Executing full workflow")
            results = await execute_full_workflow(input_data, tracer)
            logger.info(f"✅ Full workflow completed successfully")
        elif workflow_type == "incremental" or workflow_type == "incremental_workflow":
            logger.info(f"🔄 Executing incremental workflow")
            results = await execute_incremental_workflow(input_data, tracer)
            logger.info(f"✅ Incremental workflow completed successfully")
        elif workflow_type == "mvp_incremental" or workflow_type == "mvp_incremental_workflow":
            logger.info(f"🎯 Executing MVP incremental workflow")
            results = await execute_mvp_incremental_workflow(input_data, tracer)
            logger.info(f"✅ MVP incremental workflow completed successfully")
        elif workflow_type == "mvp_incremental_tdd" or workflow_type == "mvp_tdd":
            logger.info(f"🧪 Executing MVP incremental TDD workflow")
            results = await execute_mvp_incremental_tdd_workflow(input_data, tracer)
            logger.info(f"✅ MVP incremental TDD workflow completed successfully")
        elif workflow_type in ["individual", "planning", "design", "test_writing", "implementation", "review"]:
            # For individual workflows, set the step type if not already set
            if workflow_type != "individual" and not input_data.step_type:
                logger.info(f"🎯 Setting step type to '{workflow_type}' for individual workflow")
                input_data.step_type = workflow_type
            logger.info(f"👤 Executing individual workflow: {input_data.step_type or workflow_type}")
            results = await execute_individual_workflow(input_data, tracer)
            logger.info(f"✅ Individual workflow completed successfully")
        else:
            error_msg = f"Unknown workflow type: {workflow_type}. Valid types are: tdd, full, incremental, mvp_incremental, mvp_incremental_tdd, mvp_tdd, flagship, individual, planning, design, test_writing, implementation, review"
            logger.error(f"❌ {error_msg}")
            tracer.complete_execution(error=error_msg)
            raise ValueError(error_msg)
        
        logger.info(f"📈 Processing workflow results...")
        
        # Ensure results is a list
        if not isinstance(results, list):
            logger.info(f"🔄 Converting single result to list")
            results = [results] if results else []
        
        # Ensure all results are TeamMemberResult objects
        validated_results = []
        logger.info(f"📦 Processing {len(results)} results")
        for i, result in enumerate(results):
            if isinstance(result, TeamMemberResult):
                print(f"DEBUG: Result {i} is already TeamMemberResult")
                validated_results.append(result)
            elif isinstance(result, tuple) and len(result) == 2:
                # Handle (results, report) tuple from new workflow implementations
                print(f"DEBUG: Result {i} is a tuple")
                if isinstance(result[0], list):
                    print(f"DEBUG: Result {i}[0] is a list with {len(result[0])} items")
                    validated_results.extend(result[0])
                else:
                    print(f"DEBUG: Adding single result {i}[0]")
                    validated_results.append(result[0])
            elif hasattr(result, 'output'):
                # Convert to TeamMemberResult if it has output attribute
                print(f"DEBUG: Converting result {i} with output attribute")
                validated_results.append(TeamMemberResult(
                    team_member=TeamMember.planner,  # Default, should be overridden
                    output=str(result.output),
                    name="unknown"
                ))
            else:
                # Convert raw output to TeamMemberResult
                print(f"DEBUG: Converting raw result {i}")
                validated_results.append(TeamMemberResult(
                    team_member=TeamMember.planner,  # Default, should be overridden
                    output=str(result),
                    name="unknown"
                ))
        
        print(f"DEBUG: Processed {len(validated_results)} validated results")
        
        # Extract proof of execution data from executor results
        proof_path = None
        proof_data = None
        
        for result in validated_results:
            if hasattr(result, 'name') and result.name == 'executor' and hasattr(result, 'output'):
                output_str = str(result.output)
                
                # Look for proof document path in output
                if "Proof of Execution Document:" in output_str:
                    lines = output_str.split('\n')
                    for line in lines:
                        if "Proof of Execution Document:" in line:
                            proof_path = line.split("Proof of Execution Document:")[-1].strip()
                            break
                
                # Extract session ID to find proof if path not found
                if not proof_path and "SESSION_ID:" in output_str:
                    import re
                    session_match = re.search(r'SESSION_ID:\s*(\S+)', output_str)
                    if session_match:
                        session_id = session_match.group(1)
                        from workflows.workflow_config import GENERATED_CODE_PATH
                        import os
                        potential_path = os.path.join(GENERATED_CODE_PATH, session_id, "proof_of_execution.json")
                        if os.path.exists(potential_path):
                            proof_path = potential_path
                
                # Read proof data if we have a path
                if proof_path:
                    try:
                        import json
                        import os
                        if os.path.exists(proof_path):
                            with open(proof_path, 'r') as f:
                                proof_entries = json.load(f)
                                # Extract key information from proof entries
                                proof_data = {
                                    'session_id': None,
                                    'container_id': None,
                                    'execution_success': False,
                                    'stages': [],
                                    'total_duration': 0
                                }
                                
                                for entry in proof_entries:
                                    stage = entry.get('stage', '')
                                    proof_data['stages'].append({
                                        'stage': stage,
                                        'timestamp': entry.get('timestamp'),
                                        'status': entry.get('status')
                                    })
                                    
                                    if stage == 'executor_initialization':
                                        proof_data['session_id'] = entry.get('details', {}).get('session_id')
                                    elif stage == 'docker_setup':
                                        proof_data['container_id'] = entry.get('details', {}).get('container_id')
                                    elif stage == 'code_execution':
                                        proof_data['execution_success'] = entry.get('details', {}).get('overall_success', False)
                                
                                print(f"DEBUG: Successfully extracted proof data from {proof_path}")
                    except Exception as e:
                        print(f"DEBUG: Failed to read proof data: {str(e)}")
                
                break  # Found executor result, no need to continue
        
        # Update tracer report with proof data
        if proof_path or proof_data:
            tracer.report.proof_of_execution_path = proof_path
            tracer.report.proof_of_execution_data = proof_data
            print(f"DEBUG: Added proof of execution data to report")
        
        # Complete successful execution
        final_output = {
            'workflow_type': workflow_type,
            'results_count': len(validated_results),
            'team_members': [result.name for result in validated_results if hasattr(result, 'name')]
        }
        
        # Add proof info to final output if available
        if proof_path:
            final_output['proof_of_execution_path'] = proof_path
        if proof_data:
            final_output['execution_verified'] = proof_data.get('execution_success', False)
            
        print(f"DEBUG: Final output metadata: {final_output}")
        tracer.complete_execution(final_output=final_output)
        
        # Generate report
        report = tracer.get_report()
        print(f"DEBUG: Generated execution report")
        
        # Docker container cleanup
        session_id_for_cleanup = None
        
        # Try to get session ID from proof data first
        if proof_data and proof_data.get('session_id'):
            session_id_for_cleanup = proof_data.get('session_id')
        # Otherwise try to extract from executor output
        elif validated_results:
            for result in validated_results:
                if hasattr(result, 'name') and result.name == 'executor' and hasattr(result, 'output'):
                    import re
                    session_match = re.search(r'SESSION_ID:\s*(\S+)', str(result.output))
                    if session_match:
                        session_id_for_cleanup = session_match.group(1)
                        break
        
        # Perform cleanup if we have a session ID
        if session_id_for_cleanup:
            try:
                print(f"\n🧹 Initiating Docker cleanup for session: {session_id_for_cleanup}")
                docker_manager = DockerEnvironmentManager(session_id_for_cleanup)
                await docker_manager.initialize()
                await docker_manager.cleanup_session(session_id_for_cleanup)
                print(f"✅ Docker cleanup completed for session: {session_id_for_cleanup}")
            except Exception as cleanup_error:
                print(f"⚠️  Docker cleanup failed: {str(cleanup_error)}")
                # Don't fail the workflow due to cleanup errors
        
        return validated_results, report
        
    except asyncio.TimeoutError:
        error_msg = f"Workflow execution timed out for {workflow_type}"
        print(f" ERROR: {error_msg}")
        tracer.complete_execution(error=error_msg)
        raise
        
    except Exception as e:
        print(f"ERROR in execute_workflow: {str(e)}")
        print(f"ERROR traceback: {traceback.format_exc()}")
        if tracer:
            tracer.complete_execution(error=str(e))
        raise
    
    finally:
        # Ensure Docker cleanup happens even on errors
        # This is a backup cleanup in case the main cleanup didn't run
        try:
            # Only run if we haven't already cleaned up
            if 'session_id_for_cleanup' not in locals() or not session_id_for_cleanup:
                # Try to find any executor sessions from tracer
                if hasattr(tracer, 'execution_id'):
                    print(f"\n🧹 Running backup Docker cleanup for execution: {tracer.execution_id}")
                    docker_manager = DockerEnvironmentManager(tracer.execution_id)
                    await docker_manager.initialize()
                    await docker_manager.cleanup_session(tracer.execution_id)
        except Exception as cleanup_error:
            print(f"⚠️  Backup Docker cleanup failed: {str(cleanup_error)}")
            # Silent fail - don't break workflow due to cleanup


# Legacy support functions
async def run_workflow(workflow_type: str, requirements: str, 
                      team_members: Optional[List[str]] = None) -> List[TeamMemberResult]:
    """
    Legacy function for backward compatibility.
    
    Args:
        workflow_type: Type of workflow to execute
        requirements: Project requirements
        team_members: Optional list of team members
        
    Returns:
        List of team member results
    """
    print("\n===== WORKFLOW DEBUG: Starting run_workflow =====")
    print(f"workflow_type: {workflow_type}")
    print(f"requirements: {requirements[:100]}...")  # Show first 100 chars
    print(f"team_members: {team_members}")
    
    # Convert string team members to TeamMember enums
    member_enums = []
    if team_members:
        print(f"DEBUG: Converting {len(team_members)} team members to enums")
        for member in team_members:
            try:
                # Try to find matching enum
                found = False
                for tm in TeamMember:
                    if tm.value == member or tm.name.lower() == member.lower():
                        member_enums.append(tm)
                        print(f"DEBUG: Converted '{member}' to enum {tm}")
                        found = True
                        break
                if not found:
                    print(f"DEBUG: Could not convert '{member}' to enum")
            except Exception as e:
                print(f"DEBUG: Error converting '{member}' to enum: {str(e)}")
    
    print(f"DEBUG: Final member_enums: {member_enums}")
    
    # Create input data
    input_data = CodingTeamInput(
        requirements=requirements,
        workflow_type=workflow_type,
        team_members=member_enums if member_enums else None
    )
    print(f"DEBUG: Created CodingTeamInput, attributes: {dir(input_data)}")
    
    # Execute workflow
    print(f"DEBUG: Calling execute_workflow")
    try:
        results, _ = await execute_workflow(input_data)
        print(f"DEBUG: execute_workflow completed, got {len(results)} results")
        return results
    except Exception as e:
        print(f"ERROR in run_workflow: {str(e)}")
        print(f"ERROR traceback: {traceback.format_exc()}")
        raise


# Utility functions for workflow management
def get_available_workflows() -> List[str]:
    """Get list of available workflow types."""
    return ["tdd", "full", "incremental", "mvp_incremental", "mvp_incremental_tdd", "mvp_tdd", "individual", "planning", "design", "test_writing", "implementation", "review", "execution"]


def get_workflow_description(workflow_type: str) -> str:
    """Get description of a workflow type."""
    descriptions = {
        "tdd": "Test-Driven Development workflow: Planning → Design → Test Writing → Implementation → Execution → Review",
        "full": "Full development workflow: Planning → Design → Implementation → Execution → Review",
        "incremental": "Incremental feature-based workflow: Planning → Design → Incremental Implementation → Review",
        "mvp_incremental": "MVP Incremental workflow: Planning → Design → Feature-by-Feature Implementation with Validation",
        "mvp_incremental_tdd": "MVP Incremental TDD workflow: Planning → Design → For each feature: (Write Tests → Run Tests → Implement → Validate)",
        "mvp_tdd": "Alias for mvp_incremental_tdd",
        "individual": "Execute a single workflow step",
        "planning": "Execute only the planning phase",
        "design": "Execute only the design phase",
        "test_writing": "Execute only the test writing phase",
        "implementation": "Execute only the implementation phase",
        "execution": "Execute only the code execution phase with Docker container",
        "review": "Execute only the review phase"
    }
    return descriptions.get(workflow_type, f"Unknown workflow type: {workflow_type}")


def validate_workflow_input(input_data: CodingTeamInput) -> Tuple[bool, Optional[str]]:
    """
    Validate workflow input data.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not input_data.requirements:
        return False, "Requirements cannot be empty"
    
    # Extract workflow type
    workflow_type = None
    if hasattr(input_data, 'workflow_type') and input_data.workflow_type:
        workflow_type = input_data.workflow_type
    elif hasattr(input_data, 'workflow') and input_data.workflow:
        if hasattr(input_data.workflow, 'value'):
            workflow_type = input_data.workflow.value.replace('_workflow', '')
    
    if not workflow_type:
        return False, "No workflow type specified"
    
    # Validate workflow type
    valid_workflows = get_available_workflows()
    if workflow_type.lower() not in valid_workflows:
        return False, f"Invalid workflow type: {workflow_type}. Valid types are: {', '.join(valid_workflows)}"
    
    # Validate team members if specified
    if hasattr(input_data, 'team_members') and input_data.team_members:
        for member in input_data.team_members:
            if not isinstance(member, TeamMember):
                return False, f"Invalid team member: {member}. Must be a TeamMember enum"
    
    return True, None