"""
Utility functions for workflow implementations.
"""
from typing import Tuple

from orchestrator.orchestrator_agent import run_team_member

async def review_output(output: str, stage: str, context: str = "") -> Tuple[bool, str]:
    """
    Review the output from any agent and provide feedback
    
    Args:
        output: The output to review
        stage: The stage of the workflow (e.g., "plan", "design", "implementation")
        context: Additional context to provide to the reviewer
    
    Returns:
        (approved, feedback) tuple where approved is a boolean and feedback is a string
    """
    review_input = f"""Review this {stage} output:

{output}

Context: {context}

Evaluate if this {stage} is complete, correct, and ready for the next stage.
If approved, respond with "APPROVED:" followed by a brief summary.
If revision needed, respond with "REVISION NEEDED:" followed by specific feedback on what needs to be fixed."""
    
    review_result = await run_team_member("reviewer_agent", review_input)
    review_output = str(review_result[0])
    
    # Parse reviewer response
    approved = "APPROVED:" in review_output
    feedback = review_output.split(":", 1)[1].strip() if ":" in review_output else review_output
    
    return approved, feedback
