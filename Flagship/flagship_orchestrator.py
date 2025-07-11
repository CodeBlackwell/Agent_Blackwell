"""Flagship Orchestrator - Enhanced version with requirements analysis and architecture planning"""

# Add path setup before imports
import sys
from pathlib import Path
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# For backward compatibility, also export the original if needed
from flagship_orchestrator_original import FlagshipOrchestrator as FlagshipOrchestratorOriginal

# Import the enhanced orchestrator conditionally
try:
    from flagship_orchestrator_enhanced import FlagshipOrchestratorEnhanced
    _enhanced_available = True
except ImportError:
    _enhanced_available = False
    FlagshipOrchestratorEnhanced = None

# Use enhanced by default (with fallback to original if import fails)
if _enhanced_available and FlagshipOrchestratorEnhanced:
    FlagshipOrchestrator = FlagshipOrchestratorEnhanced
else:
    FlagshipOrchestrator = FlagshipOrchestratorOriginal

# Re-export key types that might be imported from this module
from models.flagship_models import (
    TDDPhase, TDDWorkflowState, PhaseTransition, PhaseResult,
    TDDWorkflowConfig, TestStatus, TestResult, AgentType
)

__all__ = [
    'FlagshipOrchestrator',
    'FlagshipOrchestratorOriginal',
    'TDDPhase',
    'TDDWorkflowState', 
    'PhaseTransition',
    'PhaseResult',
    'TDDWorkflowConfig',
    'TestStatus',
    'TestResult',
    'AgentType'
]

# Add a flag to control which orchestrator to use
USE_ENHANCED_ORCHESTRATOR = True

def get_orchestrator(*args, **kwargs):
    """Factory function to get the appropriate orchestrator"""
    if USE_ENHANCED_ORCHESTRATOR:
        return FlagshipOrchestrator(*args, **kwargs)
    else:
        return FlagshipOrchestratorOriginal(*args, **kwargs)