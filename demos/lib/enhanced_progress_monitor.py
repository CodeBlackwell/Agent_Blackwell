"""
Enhanced Progress Monitor that provides detailed context for debug logging
"""
from typing import Optional, Dict, Any, List
from workflows.mvp_incremental.progress_monitor import ProgressMonitor, StepStatus
from demos.lib.debug_logger import get_debug_logger


class EnhancedProgressMonitor(ProgressMonitor):
    """Progress monitor that logs detailed phase context to debug logger"""
    
    def __init__(self, workflow_type: str = "mvp_incremental"):
        super().__init__()
        self.workflow_type = workflow_type
        self.phase_number = 0
        self.feature_contexts = []
        self.current_features = []
        
        # Phase context mappings
        self.phase_contexts = {
            "Planning": self._get_planning_context,
            "Design": self._get_design_context,
            "TDD Implementation": self._get_implementation_context,
            "Integration Verification": self._get_verification_context
        }
    
    def start_phase(self, phase_name: str):
        """Start a new phase with context logging"""
        super().start_phase(phase_name)
        self.phase_number += 1
        
        # Get context for this phase
        context = self._get_phase_context(phase_name)
        
        # Log to debug logger if available
        debug_logger = get_debug_logger()
        if debug_logger:
            debug_logger.log_phase(
                phase_name, 
                self.phase_number, 
                "started", 
                context=context
            )
    
    def complete_phase(self, phase_name: str, duration: float):
        """Complete a phase with context logging"""
        # Get context for this phase
        context = self._get_phase_context(phase_name)
        
        # Log to debug logger if available
        debug_logger = get_debug_logger()
        if debug_logger:
            debug_logger.log_phase(
                phase_name,
                self.phase_number,
                "completed",
                duration=duration,
                context=context
            )
    
    def add_feature_info(self, features: List[Dict[str, Any]]):
        """Add feature information for context"""
        self.current_features = features
        self.feature_contexts = [f.get("title", f.get("name", "Feature")) for f in features]
    
    def _get_phase_context(self, phase_name: str) -> str:
        """Get contextual information for a phase"""
        context_func = self.phase_contexts.get(phase_name)
        if context_func:
            return context_func()
        return ""
    
    def _get_planning_context(self) -> str:
        """Context for planning phase"""
        if "todo" in self.workflow_type.lower():
            return "TODO API with CRUD operations and statistics"
        elif "blog" in self.workflow_type.lower():
            return "Blog API with posts, comments, and search"
        elif "auth" in self.workflow_type.lower():
            return "Authentication API with JWT tokens"
        return "API requirements analysis and task breakdown"
    
    def _get_design_context(self) -> str:
        """Context for design phase"""
        if "todo" in self.workflow_type.lower():
            return "FastAPI structure, Todo model, endpoint specifications"
        elif "blog" in self.workflow_type.lower():
            return "Post/Comment models, relationships, search design"
        elif "auth" in self.workflow_type.lower():
            return "User model, JWT flow, security architecture"
        return "System architecture and component design"
    
    def _get_implementation_context(self) -> str:
        """Context for implementation phase"""
        if self.feature_contexts:
            # Show first few features being implemented
            features_str = ", ".join(self.feature_contexts[:3])
            if len(self.feature_contexts) > 3:
                features_str += f" (+{len(self.feature_contexts) - 3} more)"
            return f"Features: {features_str}"
        return "Implementing features using TDD (RED→YELLOW→GREEN)"
    
    def _get_verification_context(self) -> str:
        """Context for verification phase"""
        return "Running tests, checking integration, validating API endpoints"
    
    def start_feature(self, feature_id: str, feature_name: str, feature_number: int):
        """Override to log feature-specific context"""
        super().start_feature(feature_id, feature_name, feature_number)
        
        # Log feature start with context
        debug_logger = get_debug_logger()
        if debug_logger:
            debug_logger.log_system_event(
                "feature_start",
                f"Starting feature {feature_number}: {feature_name}",
                {
                    "feature_id": feature_id,
                    "feature_name": feature_name,
                    "feature_number": feature_number,
                    "phase": self.current_phase
                }
            )
    
    def complete_feature(self, feature_id: str, success: bool = True):
        """Override to log feature completion with context"""
        feature_info = self.features.get(feature_id)
        if feature_info:
            super().complete_feature(feature_id, success)
            
            # Log feature completion
            debug_logger = get_debug_logger()
            if debug_logger:
                debug_logger.log_system_event(
                    "feature_complete",
                    f"Completed feature: {feature_info.name}",
                    {
                        "feature_id": feature_id,
                        "feature_name": feature_info.name,
                        "success": success,
                        "duration": feature_info.duration_seconds,
                        "phase": self.current_phase
                    }
                )