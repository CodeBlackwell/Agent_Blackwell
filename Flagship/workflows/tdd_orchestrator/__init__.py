"""TDD Orchestrator Module - Self-contained TDD workflow management"""

from .orchestrator import TDDOrchestrator
from .models import (
    TDDPhase,
    TDDFeature,
    TDDOrchestratorConfig,
    FeatureResult,
    PhaseResult,
    TDDCycle,
    AgentContext,
    RetryDecision,
    MetricsSnapshot
)
from .phase_manager import PhaseManager
from .agent_coordinator import AgentCoordinator
from .retry_coordinator import RetryCoordinator
from .metrics_collector import MetricsCollector

__all__ = [
    # Main orchestrator
    "TDDOrchestrator",
    
    # Models
    "TDDPhase",
    "TDDFeature", 
    "TDDOrchestratorConfig",
    "FeatureResult",
    "PhaseResult",
    "TDDCycle",
    "AgentContext",
    "RetryDecision",
    "MetricsSnapshot",
    
    # Components
    "PhaseManager",
    "AgentCoordinator",
    "RetryCoordinator",
    "MetricsCollector"
]

# Version info
__version__ = "1.0.0"
__author__ = "Flagship TDD Team"