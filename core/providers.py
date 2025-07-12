"""Provider classes for dependency injection."""

from typing import Dict, Any, List, Optional
from .interfaces import (
    IAgentRunner,
    IOutputHandler,
    IWorkflowExecutor,
    IWorkflowManager,
    IOrchestrator,
    AgentMessage,
    AgentResponse
)
from .container import get_container, injectable


class AgentRunnerAdapter(IAgentRunner):
    """Adapter for the agent runner functionality."""
    
    def __init__(self, orchestrator_agent):
        """Initialize with the actual orchestrator agent."""
        self._orchestrator_agent = orchestrator_agent
    
    def run_team_member_with_tracking(
        self,
        member_config: Dict[str, Any],
        messages: List[AgentMessage],
        verbose: bool = True
    ) -> AgentResponse:
        """Run a team member with message tracking."""
        # Convert AgentMessage objects to the format expected by the orchestrator
        message_dicts = []
        for msg in messages:
            msg_dict = {
                "role": msg.role,
                "content": msg.content
            }
            if msg.name:
                msg_dict["name"] = msg.name
            message_dicts.append(msg_dict)
        
        # Call the actual method
        result = self._orchestrator_agent.run_team_member_with_tracking(
            member_config,
            message_dicts,
            verbose
        )
        
        # Convert result to AgentResponse
        return AgentResponse(
            content=result.get("content", ""),
            messages=[
                AgentMessage(
                    role=msg.get("role"),
                    content=msg.get("content"),
                    name=msg.get("name")
                )
                for msg in result.get("messages", [])
            ],
            metadata=result.get("metadata"),
            success=result.get("success", True),
            error=result.get("error")
        )


class OutputHandlerAdapter(IOutputHandler):
    """Adapter for output handler functionality."""
    
    def __init__(self, orchestrator_agent):
        """Initialize with the actual orchestrator agent."""
        self._orchestrator_agent = orchestrator_agent
    
    def get_output_handler(self) -> Any:
        """Get the output handler instance."""
        return self._orchestrator_agent.get_output_handler()
    
    def save_report(self, report_data: Dict[str, Any], report_type: str) -> str:
        """Save a report and return the file path."""
        output_handler = self.get_output_handler()
        return output_handler.save_report(report_data, report_type)


class WorkflowExecutorAdapter(IWorkflowExecutor):
    """Adapter for workflow execution."""
    
    def __init__(self, workflow_manager):
        """Initialize with the actual workflow manager."""
        self._workflow_manager = workflow_manager
    
    def execute(
        self,
        workflow_type: str,
        request_data: Dict[str, Any],
        verbose: bool = True
    ) -> Dict[str, Any]:
        """Execute a workflow and return results."""
        return self._workflow_manager.execute_workflow(workflow_type, request_data)


@injectable(IOrchestrator)
class OrchestratorProvider(IOrchestrator):
    """Provider for orchestrator functionality."""
    
    def __init__(self):
        """Initialize the provider."""
        self._orchestrator_agent = None
        self._agent_runner = None
        self._output_handler = None
    
    def set_orchestrator_agent(self, orchestrator_agent):
        """Set the actual orchestrator agent instance."""
        self._orchestrator_agent = orchestrator_agent
        self._agent_runner = AgentRunnerAdapter(orchestrator_agent)
        self._output_handler = OutputHandlerAdapter(orchestrator_agent)
    
    def process_request(
        self,
        request_type: str,
        request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process a request through the orchestrator."""
        if not self._orchestrator_agent:
            raise RuntimeError("Orchestrator agent not initialized")
        
        return self._orchestrator_agent.process_request(request_type, request_data)
    
    def get_agent_runner(self) -> IAgentRunner:
        """Get the agent runner instance."""
        if not self._agent_runner:
            raise RuntimeError("Agent runner not initialized")
        return self._agent_runner
    
    def get_output_handler(self) -> IOutputHandler:
        """Get the output handler instance."""
        if not self._output_handler:
            raise RuntimeError("Output handler not initialized")
        return self._output_handler


@injectable(IWorkflowManager)
class WorkflowProvider(IWorkflowManager):
    """Provider for workflow management."""
    
    def __init__(self):
        """Initialize the provider."""
        self._workflow_manager = None
    
    def set_workflow_manager(self, workflow_manager):
        """Set the actual workflow manager instance."""
        self._workflow_manager = workflow_manager
    
    def get_available_workflows(self) -> List[str]:
        """Get list of available workflows."""
        if not self._workflow_manager:
            raise RuntimeError("Workflow manager not initialized")
        
        return self._workflow_manager.get_available_workflows()
    
    def execute_workflow(
        self,
        workflow_type: str,
        request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a specific workflow."""
        if not self._workflow_manager:
            raise RuntimeError("Workflow manager not initialized")
        
        return self._workflow_manager.execute_workflow(workflow_type, request_data)


class AgentProvider:
    """Provider for agent configurations and instances."""
    
    def __init__(self):
        """Initialize the provider."""
        self._agent_configs = {}
    
    def register_agent_config(self, agent_name: str, config: Dict[str, Any]):
        """Register an agent configuration."""
        self._agent_configs[agent_name] = config
    
    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """Get an agent configuration."""
        if agent_name not in self._agent_configs:
            raise KeyError(f"Agent configuration '{agent_name}' not found")
        return self._agent_configs[agent_name]
    
    def list_agents(self) -> List[str]:
        """List all registered agents."""
        return list(self._agent_configs.keys())