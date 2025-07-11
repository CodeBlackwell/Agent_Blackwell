"""
Parent System Adapter for Flagship TDD Orchestrator

This module provides integration with the parent workflow system,
allowing Flagship to be used as part of the larger ecosystem.
"""

from typing import List, Tuple, Optional, Any
import asyncio
from pathlib import Path

# Import Flagship components
from workflows.tdd_orchestrator import (
    TDDOrchestrator,
    TDDFeature,
    TDDOrchestratorConfig,
    TDDPhase
)

# Import compatibility models
from models.parent_compatibility import TeamMemberResult, TeamMember


async def execute_tdd_workflow_for_parent(
    input_data: Any,
    tracer: Optional[Any] = None
) -> Tuple[List[TeamMemberResult], Any]:
    """
    Execute TDD workflow using Flagship orchestrator for parent system
    
    Args:
        input_data: Parent system's CodingTeamInput
        tracer: Optional parent system's WorkflowExecutionTracer
        
    Returns:
        Tuple of (results list, execution report)
    """
    # Extract configuration from input
    config = TDDOrchestratorConfig(
        max_phase_retries=getattr(input_data, 'max_retries', 3),
        timeout_seconds=getattr(input_data, 'timeout_seconds', 300),
        require_review_approval=False,
        verbose_output=True
    )
    
    # Extract run_team_member function if available
    run_team_member_func = None
    if hasattr(input_data, "_run_team_member_func"):
        run_team_member_func = input_data._run_team_member_func
    
    # Create orchestrator
    orchestrator = TDDOrchestrator(
        config=config,
        run_team_member_func=run_team_member_func
    )
    
    # Convert requirements to TDD feature
    feature = TDDFeature(
        id=f"feature_{hash(input_data.requirements) % 10000}",
        description=input_data.requirements,
        test_criteria=[]
    )
    
    # Start workflow tracing if provided
    workflow_id = None
    if tracer:
        workflow_id = tracer.start_workflow("tdd_workflow", {
            "requirements": input_data.requirements
        })
    
    try:
        # Execute the feature
        result = await orchestrator.execute_feature(feature)
        
        # Convert results to parent system format
        team_results = []
        
        # Add test writer result
        if result.final_tests:
            team_results.append(TeamMemberResult(
                team_member=TeamMember.test_writer,
                output=result.final_tests
            ))
        
        # Add coder result
        if result.final_code:
            team_results.append(TeamMemberResult(
                team_member=TeamMember.coder,
                output=result.final_code
            ))
        
        # Add summary result
        summary = f"""TDD Implementation Complete:
- Feature: {result.feature_description}
- Success: {result.success}
- Cycles: {len(result.cycles)}
- Total Attempts: {result.get_total_attempts()}
"""
        
        team_results.append(TeamMemberResult(
            team_member=TeamMember.reviewer,
            output=summary
        ))
        
        # Complete workflow tracing
        if tracer and workflow_id:
            tracer.end_workflow(workflow_id, {
                "success": result.success,
                "cycles": len(result.cycles)
            })
            report = tracer.get_report()
        else:
            # Create a simple report
            report = {
                "workflow_id": "tdd_workflow",
                "workflow_type": "tdd",
                "duration_seconds": result.total_duration_seconds,
                "success": result.success,
                "error": None
            }
        
        return team_results, report
        
    except Exception as e:
        # Handle errors
        if tracer and workflow_id:
            tracer.end_workflow(workflow_id, {"error": str(e)}, error=str(e))
            report = tracer.get_report()
        else:
            report = {
                "workflow_id": "tdd_workflow",
                "workflow_type": "tdd",
                "duration_seconds": 0,
                "success": False,
                "error": str(e)
            }
        
        # Return error results
        error_result = TeamMemberResult(
            team_member=TeamMember.planner,
            output=f"TDD Workflow Error: {str(e)}"
        )
        
        return [error_result], report


# Re-export for compatibility
__all__ = [
    "execute_tdd_workflow_for_parent",
    "TDDOrchestrator",
    "TDDFeature", 
    "TDDOrchestratorConfig",
    "TDDPhase"
]