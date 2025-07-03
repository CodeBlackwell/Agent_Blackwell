"""
Utility functions for workflow implementations.
"""
from typing import Tuple

from orchestrator.orchestrator_agent import run_team_member
from agents.reviewer.reviewer_config import (
    MAX_REVIEW_RETRIES, 
    AUTO_APPROVE_AFTER_MAX_RETRIES,
    REVIEW_PROMPT_TEMPLATE,
    AUTO_APPROVAL_MESSAGE_TEMPLATE
)

async def review_output(output: str, stage: str, context: str = "", max_retries: int = MAX_REVIEW_RETRIES, current_retry: int = 0) -> Tuple[bool, str]:
    """
    Review the output from any agent and provide feedback
    
    Args:
        output: The output to review
        stage: The stage of the workflow (e.g., "plan", "design", "implementation")
        context: Additional context to provide to the reviewer
        max_retries: Maximum number of review attempts before auto-approving
        current_retry: Current retry attempt number
    
    Returns:
        (approved, feedback) tuple where approved is a boolean and feedback is a string
    """
    # Auto-approve after max retries if enabled
    if AUTO_APPROVE_AFTER_MAX_RETRIES and current_retry >= max_retries:
        return True, AUTO_APPROVAL_MESSAGE_TEMPLATE.format(max_retries=max_retries, stage=stage)
    
    # Use the template from config
    review_input = REVIEW_PROMPT_TEMPLATE.format(
        stage=stage,
        output=output,
        context=context
    )
    
    review_result = await run_team_member("reviewer_agent", review_input)
    review_output = str(review_result[0])
    
    # Parse reviewer response
    approved = "APPROVED:" in review_output
    feedback = review_output.split(":", 1)[1].strip() if ":" in review_output else review_output
    
    return approved, feedback
