"""
Workflow manager for coordinating different workflow implementations.
"""
from typing import List, Dict, Any, Optional, Tuple
import asyncio

# Import shared data models
from shared.data_models import (
    TeamMember, TeamMemberResult, WorkflowStep, CodingTeamInput
)

# Import workflow implementations
from workflows.tdd.tdd_workflow import execute_tdd_workflow
from workflows.full.full_workflow import execute_full_workflow
from workflows.individual.individual_workflow import execute_individual_workflow
from workflows.monitoring import WorkflowExecutionTracer, WorkflowExecutionReport


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
    # Extract workflow type properly
    workflow_type = None
    
    # First check workflow_type field (new style)
    if hasattr(input_data, 'workflow_type') and input_data.workflow_type:
        workflow_type = input_data.workflow_type.lower()
    # Then check workflow field (legacy style with enum)
    elif hasattr(input_data, 'workflow') and input_data.workflow:
        # Handle enum value
        if hasattr(input_data.workflow, 'value'):
            workflow_type = input_data.workflow.value.replace('_workflow', '').lower()
        else:
            workflow_type = str(input_data.workflow).replace('_workflow', '').lower()
    
    # Validate workflow type
    if not workflow_type:
        raise ValueError("No workflow type specified in input data")
    
    # Normalize workflow type
    workflow_type = workflow_type.strip().lower()
    
    # Create tracer if not provided
    if tracer is None:
        tracer = WorkflowExecutionTracer(workflow_type)
    
    # Add input metadata to tracer
    tracer.add_metadata('input_requirements', input_data.requirements)
    tracer.add_metadata('workflow_type', workflow_type)
    
    # Add team members if available
    if hasattr(input_data, 'team_members') and input_data.team_members:
        team_member_names = []
        for member in input_data.team_members:
            if hasattr(member, 'name'):
                team_member_names.append(member.name)
            elif hasattr(member, 'value'):
                team_member_names.append(member.value)
            else:
                team_member_names.append(str(member))
        tracer.add_metadata('team_members', team_member_names)
    
    try:
        # Log workflow start
        print(f"🚀 Executing {workflow_type} workflow...")
        
        # Execute the appropriate workflow with monitoring
        if workflow_type == "tdd" or workflow_type == "tdd_workflow":
            results = await execute_tdd_workflow(input_data, tracer)
        elif workflow_type == "full" or workflow_type == "full_workflow":
            results = await execute_full_workflow(input_data, tracer)
        elif workflow_type in ["individual", "planning", "design", "test_writing", "implementation", "review"]:
            # For individual workflows, set the step type if not already set
            if workflow_type != "individual" and not input_data.step_type:
                input_data.step_type = workflow_type
            results = await execute_individual_workflow(input_data, tracer)
        else:
            error_msg = f"Unknown workflow type: {workflow_type}. Valid types are: tdd, full, individual, planning, design, test_writing, implementation, review"
            tracer.complete_execution(error=error_msg)
            raise ValueError(error_msg)
        
        # Ensure results is a list
        if not isinstance(results, list):
            results = [results] if results else []
        
        # Ensure all results are TeamMemberResult objects
        validated_results = []
        for result in results:
            if isinstance(result, TeamMemberResult):
                validated_results.append(result)
            elif isinstance(result, tuple) and len(result) == 2:
                # Handle (results, report) tuple from new workflow implementations
                if isinstance(result[0], list):
                    validated_results.extend(result[0])
                else:
                    validated_results.append(result[0])
            elif hasattr(result, 'output'):
                # Convert to TeamMemberResult if it has output attribute
                validated_results.append(TeamMemberResult(
                    team_member=TeamMember.planner,  # Default, should be overridden
                    output=str(result.output),
                    name="unknown"
                ))
            else:
                # Convert raw output to TeamMemberResult
                validated_results.append(TeamMemberResult(
                    team_member=TeamMember.planner,  # Default, should be overridden
                    output=str(result),
                    name="unknown"
                ))
        
        # Complete successful execution
        final_output = {
            'workflow_type': workflow_type,
            'results_count': len(validated_results),
            'team_members': [result.name for result in validated_results if hasattr(result, 'name')]
        }
        tracer.complete_execution(final_output=final_output)
        
        print(f"✅ {workflow_type} workflow completed successfully with {len(validated_results)} results")
        
        return validated_results, tracer.get_report()
        
    except asyncio.TimeoutError:
        error_msg = f"Workflow execution timed out for {workflow_type}"
        print(f"⏰ {error_msg}")
        tracer.complete_execution(error=error_msg)
        raise
        
    except Exception as e:
        # Complete execution with error
        error_msg = f"Workflow execution error in {workflow_type}: {str(e)}"
        print(f"❌ {error_msg}")
        tracer.complete_execution(error=error_msg)
        raise


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
    # Convert string team members to TeamMember enums
    member_enums = []
    if team_members:
        for member in team_members:
            try:
                # Try to find matching enum
                for tm in TeamMember:
                    if tm.value == member or tm.name.lower() == member.lower():
                        member_enums.append(tm)
                        break
            except:
                pass
    
    # Create input data
    input_data = CodingTeamInput(
        requirements=requirements,
        workflow_type=workflow_type,
        team_members=member_enums if member_enums else None
    )
    
    # Execute workflow
    results, _ = await execute_workflow(input_data)
    return results


# Utility functions for workflow management
def get_available_workflows() -> List[str]:
    """Get list of available workflow types."""
    return ["tdd", "full", "individual", "planning", "design", "test_writing", "implementation", "review"]


def get_workflow_description(workflow_type: str) -> str:
    """Get description of a workflow type."""
    descriptions = {
        "tdd": "Test-Driven Development workflow: Planning → Design → Test Writing → Implementation → Review",
        "full": "Full development workflow: Planning → Design → Implementation → Review",
        "individual": "Execute a single workflow step",
        "planning": "Execute only the planning phase",
        "design": "Execute only the design phase",
        "test_writing": "Execute only the test writing phase",
        "implementation": "Execute only the implementation phase",
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