"""Centralized exception types and error handling framework."""

from typing import Optional, Dict, Any, List
from enum import Enum
import traceback
from datetime import datetime


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification."""
    CONFIGURATION = "configuration"
    VALIDATION = "validation"
    WORKFLOW = "workflow"
    AGENT = "agent"
    COMMUNICATION = "communication"
    TIMEOUT = "timeout"
    RESOURCE = "resource"
    EXTERNAL_API = "external_api"
    FILE_SYSTEM = "file_system"
    UNKNOWN = "unknown"


class BaseOrchestratorError(Exception):
    """Base exception class for all orchestrator errors."""
    
    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        details: Optional[Dict[str, Any]] = None,
        recoverable: bool = True
    ):
        """Initialize the error."""
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.details = details or {}
        self.recoverable = recoverable
        self.timestamp = datetime.utcnow()
        self.traceback = traceback.format_exc()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for logging/serialization."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "category": self.category.value,
            "severity": self.severity.value,
            "details": self.details,
            "recoverable": self.recoverable,
            "timestamp": self.timestamp.isoformat(),
            "traceback": self.traceback
        }


# Configuration Errors
class ConfigurationError(BaseOrchestratorError):
    """Raised when there's a configuration issue."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            category=ErrorCategory.CONFIGURATION,
            severity=ErrorSeverity.HIGH,
            details=details,
            recoverable=False
        )


class ValidationError(BaseOrchestratorError):
    """Raised when validation fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.MEDIUM,
            details=details,
            recoverable=True
        )


# Workflow Errors
class WorkflowError(BaseOrchestratorError):
    """Base class for workflow-related errors."""
    
    def __init__(
        self,
        message: str,
        workflow_type: str,
        phase: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details.update({
            "workflow_type": workflow_type,
            "phase": phase
        })
        super().__init__(
            message=message,
            category=ErrorCategory.WORKFLOW,
            severity=ErrorSeverity.MEDIUM,
            details=details,
            recoverable=True
        )


class WorkflowTimeoutError(WorkflowError):
    """Raised when a workflow times out."""
    
    def __init__(
        self,
        workflow_type: str,
        phase: Optional[str] = None,
        timeout_seconds: Optional[int] = None
    ):
        message = f"Workflow '{workflow_type}' timed out"
        if phase:
            message += f" during phase '{phase}'"
        
        super().__init__(
            message=message,
            workflow_type=workflow_type,
            phase=phase,
            details={"timeout_seconds": timeout_seconds}
        )
        self.severity = ErrorSeverity.HIGH


# Agent Errors
class AgentError(BaseOrchestratorError):
    """Base class for agent-related errors."""
    
    def __init__(
        self,
        message: str,
        agent_name: str,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details["agent_name"] = agent_name
        super().__init__(
            message=message,
            category=ErrorCategory.AGENT,
            severity=ErrorSeverity.MEDIUM,
            details=details,
            recoverable=True
        )


class AgentTimeoutError(AgentError):
    """Raised when an agent times out."""
    
    def __init__(self, agent_name: str, timeout_seconds: Optional[int] = None):
        super().__init__(
            message=f"Agent '{agent_name}' timed out",
            agent_name=agent_name,
            details={"timeout_seconds": timeout_seconds}
        )
        self.severity = ErrorSeverity.HIGH


class AgentCommunicationError(AgentError):
    """Raised when agent communication fails."""
    
    def __init__(self, agent_name: str, reason: str):
        super().__init__(
            message=f"Communication with agent '{agent_name}' failed: {reason}",
            agent_name=agent_name,
            details={"reason": reason}
        )


# External API Errors
class ExternalAPIError(BaseOrchestratorError):
    """Raised when external API calls fail."""
    
    def __init__(
        self,
        message: str,
        api_name: str,
        status_code: Optional[int] = None,
        response: Optional[str] = None
    ):
        details = {
            "api_name": api_name,
            "status_code": status_code,
            "response": response
        }
        super().__init__(
            message=message,
            category=ErrorCategory.EXTERNAL_API,
            severity=ErrorSeverity.HIGH,
            details=details,
            recoverable=True
        )


# Resource Errors
class ResourceError(BaseOrchestratorError):
    """Raised when resource limits are exceeded."""
    
    def __init__(
        self,
        message: str,
        resource_type: str,
        current_usage: Optional[Any] = None,
        limit: Optional[Any] = None
    ):
        details = {
            "resource_type": resource_type,
            "current_usage": current_usage,
            "limit": limit
        }
        super().__init__(
            message=message,
            category=ErrorCategory.RESOURCE,
            severity=ErrorSeverity.CRITICAL,
            details=details,
            recoverable=False
        )


# File System Errors
class FileSystemError(BaseOrchestratorError):
    """Raised when file system operations fail."""
    
    def __init__(
        self,
        message: str,
        path: str,
        operation: str,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details.update({
            "path": path,
            "operation": operation
        })
        super().__init__(
            message=message,
            category=ErrorCategory.FILE_SYSTEM,
            severity=ErrorSeverity.MEDIUM,
            details=details,
            recoverable=True
        )


# Error Recovery Strategies
class ErrorRecoveryStrategy:
    """Base class for error recovery strategies."""
    
    @staticmethod
    def can_handle(error: BaseOrchestratorError) -> bool:
        """Check if this strategy can handle the given error."""
        raise NotImplementedError
    
    @staticmethod
    def recover(error: BaseOrchestratorError) -> Dict[str, Any]:
        """Attempt to recover from the error."""
        raise NotImplementedError


class RetryStrategy(ErrorRecoveryStrategy):
    """Retry strategy for recoverable errors."""
    
    @staticmethod
    def can_handle(error: BaseOrchestratorError) -> bool:
        """Check if error is recoverable through retry."""
        return error.recoverable and error.category in [
            ErrorCategory.TIMEOUT,
            ErrorCategory.EXTERNAL_API,
            ErrorCategory.COMMUNICATION
        ]
    
    @staticmethod
    def recover(error: BaseOrchestratorError, max_retries: int = 3) -> Dict[str, Any]:
        """Return retry configuration."""
        return {
            "strategy": "retry",
            "max_attempts": max_retries,
            "backoff_seconds": 5,
            "exponential_backoff": True
        }


class FallbackStrategy(ErrorRecoveryStrategy):
    """Fallback strategy for workflow errors."""
    
    @staticmethod
    def can_handle(error: BaseOrchestratorError) -> bool:
        """Check if error can be handled with fallback."""
        return error.category == ErrorCategory.WORKFLOW and error.recoverable
    
    @staticmethod
    def recover(error: BaseOrchestratorError) -> Dict[str, Any]:
        """Return fallback configuration."""
        return {
            "strategy": "fallback",
            "fallback_workflow": "individual",
            "skip_failed_phase": True
        }


class ErrorHandler:
    """Central error handler for the orchestrator."""
    
    def __init__(self):
        """Initialize error handler."""
        self.strategies: List[ErrorRecoveryStrategy] = [
            RetryStrategy(),
            FallbackStrategy()
        ]
        self.error_history: List[BaseOrchestratorError] = []
    
    def handle_error(self, error: BaseOrchestratorError) -> Optional[Dict[str, Any]]:
        """Handle an error and return recovery options if available."""
        # Log error to history
        self.error_history.append(error)
        
        # Find applicable recovery strategy
        for strategy in self.strategies:
            if strategy.can_handle(error):
                return strategy.recover(error)
        
        # No recovery strategy available
        return None
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of errors."""
        if not self.error_history:
            return {"total_errors": 0, "errors_by_category": {}}
        
        errors_by_category = {}
        for error in self.error_history:
            category = error.category.value
            if category not in errors_by_category:
                errors_by_category[category] = 0
            errors_by_category[category] += 1
        
        return {
            "total_errors": len(self.error_history),
            "errors_by_category": errors_by_category,
            "recent_errors": [
                error.to_dict() for error in self.error_history[-5:]
            ]
        }
    
    def clear_history(self):
        """Clear error history."""
        self.error_history.clear()


# Global error handler instance
_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """Get global error handler instance."""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler