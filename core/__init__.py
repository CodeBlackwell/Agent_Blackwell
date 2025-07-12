"""Core module for dependency injection and interfaces."""

from .interfaces import (
    IOrchestrator,
    IWorkflowExecutor,
    IAgentRunner,
    IOutputHandler,
    IWorkflowManager
)
from .container import DIContainer, get_container
from .providers import (
    OrchestratorProvider,
    WorkflowProvider,
    AgentProvider
)

__all__ = [
    'IOrchestrator',
    'IWorkflowExecutor',
    'IAgentRunner',
    'IOutputHandler',
    'IWorkflowManager',
    'DIContainer',
    'get_container',
    'OrchestratorProvider',
    'WorkflowProvider',
    'AgentProvider'
]