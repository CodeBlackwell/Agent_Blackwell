"""
Incremental feature-based development workflow.
Follows the pattern: Planning → Design → Incremental Implementation → Review
"""
import sys
import os
# Add the parent directory to the path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from typing import List, Optional

from shared.data_models import (
    CodingTeamInput, 
    TeamMemberResult, 
    TeamMember
)
# Dynamic imports to avoid circular dependency - moved inside function
from workflows.monitoring import WorkflowExecutionTracer
from .feature_orchestrator import FeatureOrchestrator, extract_content_from_message


async def execute_incremental_workflow(
    input_data: CodingTeamInput, 
    tracer: Optional[WorkflowExecutionTracer] = None
) -> List[TeamMemberResult]:
    """
    Execute the incremental feature-based development workflow.
    
    This workflow breaks down development into smaller features and implements
    them incrementally with validation after each feature.
    
    Args:
        input_data: The coding team input containing requirements
        tracer: Optional workflow execution tracer
        
    Returns:
        List of team member results
    """
    # Dynamic imports using dependency injection to avoid circular dependency
    from core.migration import run_team_member_with_tracking, get_output_handler
    
    if not tracer:
        tracer = WorkflowExecutionTracer("incremental")
    
    print("\n🚀 Starting Incremental Development Workflow...")
    print("=" * 60)
    
    results = []
    
    # Step 1: Planning
    planning_step_id = tracer.start_step("planning", "planner_agent", {
        "requirements": input_data.requirements
    })
    
    planning_result = await run_team_member_with_tracking(
        "planner_agent",
        input_data.requirements,
        "incremental_planning"
    )
    # Extract the actual content from the Message object
    planning_output = extract_content_from_message(planning_result)
    planner_result = TeamMemberResult(
        team_member=TeamMember.planner,
        output=planning_output,
        name="planner"
    )
    results.append(planner_result)
    
    tracer.complete_step(planning_step_id, {
        "output_length": len(planner_result.output),
        "status": "completed"
    })
    
    # Step 2: Design
    design_step_id = tracer.start_step("design", "designer_agent", {
        "plan": planner_result.output
    })
    
    design_result = await run_team_member_with_tracking(
        "designer_agent",
        f"Based on this plan, create a detailed technical design:\n\n{planner_result.output}",
        "incremental_design"
    )
    # Extract the actual content from the Message object
    design_output = extract_content_from_message(design_result)
    designer_result = TeamMemberResult(
        team_member=TeamMember.designer,
        output=design_output,
        name="designer"
    )
    results.append(designer_result)
    
    tracer.complete_step(design_step_id, {
        "output_length": len(designer_result.output),
        "status": "completed"
    })
    
    # Step 3: Incremental Implementation
    impl_step_id = tracer.start_step("implementation", "incremental_coding", {
        "design": designer_result.output
    })
    
    try:
        # Create feature orchestrator
        orchestrator = FeatureOrchestrator(tracer)
        
        # Execute incremental development
        team_results, final_codebase, execution_summary = await orchestrator.execute_incremental_development(
            designer_output=designer_result.output,
            requirements=input_data.requirements,
            tests=None,  # No pre-written tests for incremental workflow
            max_retries=3
        )
        
        # Add orchestrator results
        if team_results:
            results.extend(team_results)
        
        # Create a consolidated result for the incremental implementation
        # Aggregate all generated files into a comprehensive output
        aggregated_output = "# Generated Code Files\n\n"
        for filename, content in sorted(final_codebase.items()):
            aggregated_output += f"## {filename}\n\n```python\n{content}\n```\n\n"
        
        # Add execution summary
        if execution_summary:
            aggregated_output += "\n## Execution Summary\n\n"
            aggregated_output += f"- Total Features: {execution_summary.get('total_features', 0)}\n"
            aggregated_output += f"- Completed Features: {execution_summary.get('completed_features', 0)}\n"
            aggregated_output += f"- Success Rate: {execution_summary.get('success_rate', 0):.1f}%\n"
            aggregated_output += f"- Files Created: {execution_summary.get('files_created', 0)}\n"
        
        coder_result = TeamMemberResult(
            team_member=TeamMember.coder,
            output=aggregated_output if final_codebase else "# No implementation generated",
            name="incremental_coder"
        )
        results.append(coder_result)
        
        tracer.complete_step(impl_step_id, {
            "status": "completed",
            "features_implemented": execution_summary.get("features_implemented", 0),
            "total_features": execution_summary.get("total_features", 0),
            "execution_metrics": execution_summary
        })
        
    except Exception as e:
        tracer.complete_step(impl_step_id, {
            "status": "failed",
            "error": str(e)
        }, error=str(e))
        raise
    
    # Step 4: Review
    review_step_id = tracer.start_step("review", "reviewer_agent", {
        "implementation": coder_result.output
    })
    
    review_result = await run_team_member_with_tracking(
        "reviewer_agent",
        f"Review this incremental implementation:\n\n{coder_result.output}",
        "incremental_review"
    )
    # Extract the actual content from the Message object
    review_output = extract_content_from_message(review_result)
    reviewer_result = TeamMemberResult(
        team_member=TeamMember.reviewer,
        output=review_output,
        name="reviewer"
    )
    results.append(reviewer_result)
    
    tracer.complete_step(review_step_id, {
        "output_length": len(reviewer_result.output),
        "status": "completed"
    })
    
    print("\n✅ Incremental Development Workflow completed!")
    print("=" * 60)
    
    return results