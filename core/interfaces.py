"""Interface definitions for dependency injection."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List, Tuple
from dataclasses import dataclass


@dataclass
class AgentMessage:
    """Message structure for agent communication."""
    role: str
    content: str
    name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AgentResponse:
    """Response structure from agent execution."""
    content: str
    messages: List[AgentMessage]
    metadata: Optional[Dict[str, Any]] = None
    success: bool = True
    error: Optional[str] = None


class IAgentRunner(ABC):
    """Interface for running team member agents."""
    
    @abstractmethod
    def run_team_member_with_tracking(
        self,
        member_config: Dict[str, Any],
        messages: List[AgentMessage],
        verbose: bool = True
    ) -> AgentResponse:
        """Run a team member with message tracking."""
        pass


class IOutputHandler(ABC):
    """Interface for handling output operations."""
    
    @abstractmethod
    def get_output_handler(self) -> Any:
        """Get the output handler instance."""
        pass
    
    @abstractmethod
    def save_report(self, report_data: Dict[str, Any], report_type: str) -> str:
        """Save a report and return the file path."""
        pass


class IWorkflowExecutor(ABC):
    """Interface for workflow execution."""
    
    @abstractmethod
    def execute(
        self,
        workflow_type: str,
        request_data: Dict[str, Any],
        verbose: bool = True
    ) -> Dict[str, Any]:
        """Execute a workflow and return results."""
        pass


class IWorkflowManager(ABC):
    """Interface for workflow management."""
    
    @abstractmethod
    def get_available_workflows(self) -> List[str]:
        """Get list of available workflows."""
        pass
    
    @abstractmethod
    def execute_workflow(
        self,
        workflow_type: str,
        request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a specific workflow."""
        pass


class IOrchestrator(ABC):
    """Interface for the main orchestrator."""
    
    @abstractmethod
    def process_request(
        self,
        request_type: str,
        request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process a request through the orchestrator."""
        pass
    
    @abstractmethod
    def get_agent_runner(self) -> IAgentRunner:
        """Get the agent runner instance."""
        pass
    
    @abstractmethod
    def get_output_handler(self) -> IOutputHandler:
        """Get the output handler instance."""
        pass