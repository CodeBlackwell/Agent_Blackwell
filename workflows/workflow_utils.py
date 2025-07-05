"""
Utility functions for workflow implementations.
"""
from workflows.workflow_config import MAX_REVIEW_RETRIES
from workflows.monitoring import WorkflowExecutionTracer, ReviewDecision
from workflows.agent_output_handler import get_output_handler
from typing import Optional

async def review_output(content: str, context: str = "", max_retries: int = MAX_REVIEW_RETRIES, 
                       tracer: Optional[WorkflowExecutionTracer] = None,
                       target_agent: Optional[str] = None) -> tuple[bool, str]:
    """
    Review output using the reviewer agent with comprehensive tracking.
    
    Args:
        content: The content to review
        context: Additional context for the review
        max_retries: Maximum number of review retries
        tracer: Optional tracer for monitoring review interactions
        target_agent: The agent whose output is being reviewed
        
    Returns:
        Tuple of (approved: bool, feedback: str)
    """
    # Import run_team_member dynamically to avoid circular imports
    from orchestrator.orchestrator_agent import run_team_member_with_tracking
    
    review_prompt = f"""
    Please review the following output:
    
    Content: {content}
    Context: {context}
    
    Respond with either:
    - "APPROVED" if the output meets requirements
    - "REVISION NEEDED: [specific feedback]" if changes are required
    """
    
    retry_count = 0
    
    # Get output handler for review notifications
    output_handler = get_output_handler()
    
    # Notify review start
    if output_handler:
        output_handler.on_review_start(context or "output", target_agent or "unknown")
    
    try:
        review_result = await run_team_member_with_tracking("reviewer_agent", review_prompt, f"review_{context}")
        
        # Extract the actual response text
        review_response = ""
        if review_result and len(review_result) > 0:
            if hasattr(review_result[0], 'parts') and len(review_result[0].parts) > 0:
                review_response = review_result[0].parts[0].content
            else:
                review_response = str(review_result[0])
        
        if "APPROVED" in review_response.upper():
            # Record successful review
            if tracer:
                tracer.record_review(
                    reviewer_agent="reviewer_agent",
                    reviewed_content=content[:200] + "..." if len(content) > 200 else content,
                    decision=ReviewDecision.APPROVED,
                    feedback="Approved by reviewer",
                    retry_count=retry_count,
                    target_agent=target_agent
                )
            
            # Notify review complete
            if output_handler:
                output_handler.on_review_complete(True, "Approved by reviewer")
                
            return True, "Approved by reviewer"
            
        elif "REVISION NEEDED" in review_response.upper():
            feedback = review_response.split("REVISION NEEDED:", 1)[-1].strip()
            
            # Record revision request
            if tracer:
                tracer.record_review(
                    reviewer_agent="reviewer_agent",
                    reviewed_content=content[:200] + "..." if len(content) > 200 else content,
                    decision=ReviewDecision.REVISION_NEEDED,
                    feedback=feedback,
                    retry_count=retry_count,
                    target_agent=target_agent
                )
            
            # Notify review complete
            if output_handler:
                output_handler.on_review_complete(False, feedback)
                
            return False, feedback
            
        else:
            # If unclear response, treat as revision needed
            feedback = f"Review unclear: {review_response}"
            
            if tracer:
                tracer.record_review(
                    reviewer_agent="reviewer_agent",
                    reviewed_content=content[:200] + "..." if len(content) > 200 else content,
                    decision=ReviewDecision.REVISION_NEEDED,
                    feedback=feedback,
                    retry_count=retry_count,
                    target_agent=target_agent
                )
            return False, feedback
            
    except Exception as e:
        # On error, auto-approve to prevent blocking
        error_feedback = f"Auto-approved due to review error: {str(e)}"
        
        if tracer:
            tracer.record_review(
                reviewer_agent="reviewer_agent",
                reviewed_content=content[:200] + "..." if len(content) > 200 else content,
                decision=ReviewDecision.AUTO_APPROVED,
                feedback=error_feedback,
                retry_count=retry_count,
                auto_approved=True,
                target_agent=target_agent
            )
        return True, error_feedback
    
    # Fallback auto-approval (shouldn't reach here normally)
    fallback_feedback = "Auto-approved after max retries"
    if tracer:
        tracer.record_review(
            reviewer_agent="reviewer_agent",
            reviewed_content=content[:200] + "..." if len(content) > 200 else content,
            decision=ReviewDecision.AUTO_APPROVED,
            feedback=fallback_feedback,
            retry_count=max_retries,
            auto_approved=True,
            target_agent=target_agent
        )
    return True, fallback_feedback
