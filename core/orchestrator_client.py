"""Client for communicating with the orchestrator agent via ACP protocol."""

import asyncio
from typing import Dict, Any, List
from acp_sdk.client import Client
from acp_sdk import Message
from acp_sdk.models import MessagePart


async def call_agent_via_orchestrator(agent_name: str, requirements: str, context: str = "") -> Dict[str, Any]:
    """
    Call an agent through the orchestrator using the ACP protocol.
    
    Args:
        agent_name: Name of the agent to call (e.g., 'planner_agent')
        requirements: The requirements/input for the agent
        context: Additional context for the agent
        
    Returns:
        Dict containing the agent's response
    """
    # Map external names to internal wrapper names
    agent_name_mapping = {
        "planner_agent": "planner_agent_wrapper",
        "designer_agent": "designer_agent_wrapper",
        "coder_agent": "coder_agent_wrapper",
        "test_writer_agent": "test_writer_agent_wrapper",
        "reviewer_agent": "reviewer_agent_wrapper",
        "executor_agent": "executor_agent_wrapper",
        "feature_coder_agent": "feature_coder_agent_wrapper",
        "validator_agent": "validator_agent_wrapper",
        "feature_reviewer_agent": "feature_reviewer_agent_wrapper"
    }
    
    internal_agent_name = agent_name_mapping.get(agent_name, agent_name)
    
    # Combine requirements and context into input
    if context:
        input_text = f"{requirements}\n\nContext: {context}"
    else:
        input_text = requirements
    
    # Connect to orchestrator on port 8080
    async with Client(base_url="http://localhost:8080") as client:
        try:
            # Call the agent
            run = await client.run_sync(
                agent=internal_agent_name,
                input=[Message(parts=[MessagePart(content=input_text, content_type="text/plain")])]
            )
            
            # Extract output
            output_text = ""
            if run.output and len(run.output) > 0:
                for message in run.output:
                    if hasattr(message, 'parts'):
                        for part in message.parts:
                            if hasattr(part, 'content'):
                                output_text += part.content
            
            # Return in the expected format
            return {
                "content": output_text,
                "messages": [],
                "success": True,
                "metadata": {
                    "agent": agent_name,
                    "context": context
                }
            }
            
        except Exception as e:
            return {
                "content": f"Error calling agent {agent_name}: {str(e)}",
                "messages": [],
                "success": False,
                "error": str(e)
            }


# Compatibility wrapper to match the expected signature
async def run_team_member_with_tracking(agent_name: str, requirements: str, context: str) -> Dict[str, Any]:
    """
    Compatibility wrapper for run_team_member_with_tracking.
    
    This matches the signature used by the individual workflow.
    """
    return await call_agent_via_orchestrator(agent_name, requirements, context)