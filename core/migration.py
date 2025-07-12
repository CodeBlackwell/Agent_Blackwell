"""Migration helpers for converting to dependency injection."""

from typing import Dict, Any, List
from .container import get_container
from .interfaces import IAgentRunner, IOutputHandler, IOrchestrator, IWorkflowManager


def get_agent_runner() -> IAgentRunner:
    """Get the agent runner from the DI container."""
    container = get_container()
    orchestrator = container.resolve(IOrchestrator)
    return orchestrator.get_agent_runner()


def get_output_handler() -> IOutputHandler:
    """Get the output handler from the DI container."""
    container = get_container()
    orchestrator = container.resolve(IOrchestrator)
    return orchestrator.get_output_handler()


async def run_team_member_with_tracking(
    member_config: Any,  # Can be dict or string
    messages: Any = None,  # Can be list or string
    verbose: bool = True
) -> Dict[str, Any]:
    """Compatibility wrapper for run_team_member_with_tracking."""
    # Handle the case where this is called with agent_name, requirements, context
    # (the old signature used in individual workflow)
    if isinstance(member_config, str) and isinstance(messages, str):
        # This is the old signature: agent_name, requirements, context
        agent_name = member_config
        requirements = messages
        context = verbose if isinstance(verbose, str) else "workflow"
        
        # Use the orchestrator client
        from .orchestrator_client import call_agent_via_orchestrator
        
        try:
            # Since this function is now async, we can await directly
            result = await call_agent_via_orchestrator(agent_name, requirements, context)
            return result
                
        except Exception as e:
            raise RuntimeError(f"Error calling orchestrator: {str(e)}")
    
    # Otherwise try to use the DI system (original implementation)
    try:
        agent_runner = get_agent_runner()
        
        # Convert dict messages to AgentMessage objects
        from .interfaces import AgentMessage
        agent_messages = [
            AgentMessage(
                role=msg.get("role"),
                content=msg.get("content"),
                name=msg.get("name")
            )
            for msg in messages
        ]
        
        # Run the agent
        response = agent_runner.run_team_member_with_tracking(
            member_config,
            agent_messages,
            verbose
        )
        
        # Convert response back to dict format
        return {
            "content": response.content,
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "name": msg.name
                }
                for msg in response.messages
            ],
            "metadata": response.metadata,
            "success": response.success,
            "error": response.error
        }
    except RuntimeError as e:
        if "not initialized" in str(e):
            # Fallback to direct HTTP call
            raise RuntimeError("Agent runner not initialized and fallback not available for dict-based call")
        raise


def execute_workflow(workflow_type: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Compatibility wrapper for execute_workflow."""
    container = get_container()
    workflow_manager = container.resolve(IWorkflowManager)
    return workflow_manager.execute_workflow(workflow_type, request_data)


# Export compatibility functions that workflows can import
__all__ = [
    'get_agent_runner',
    'get_output_handler',
    'run_team_member_with_tracking',
    'execute_workflow'
]