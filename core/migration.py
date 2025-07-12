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


def run_team_member_with_tracking(
    member_config: Dict[str, Any],
    messages: List[Dict[str, Any]],
    verbose: bool = True
) -> Dict[str, Any]:
    """Compatibility wrapper for run_team_member_with_tracking."""
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