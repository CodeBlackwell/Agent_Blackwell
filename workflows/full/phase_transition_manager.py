"""
Phase transition manager for smooth agent handoffs in full workflow.
"""
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import json


class TransitionStatus(Enum):
    """Status of a phase transition."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress" 
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class TransitionValidation:
    """Validation result for a phase transition."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


@dataclass
class PhaseTransition:
    """Represents a transition between workflow phases."""
    from_phase: str
    to_phase: str
    status: TransitionStatus = TransitionStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    validation_result: Optional[TransitionValidation] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class PhaseTransitionManager:
    """Manages transitions between workflow phases."""
    
    def __init__(self):
        self.transitions: List[PhaseTransition] = []
        self.phase_dependencies = {
            "designer": ["planner"],
            "coder": ["designer", "planner"],
            "reviewer": ["coder"],
            "executor": ["coder"]
        }
        self.transition_validators = {
            "planner_to_designer": self._validate_planner_to_designer,
            "designer_to_coder": self._validate_designer_to_coder,
            "coder_to_reviewer": self._validate_coder_to_reviewer,
            "coder_to_executor": self._validate_coder_to_executor
        }
        
    def start_transition(self, from_phase: str, to_phase: str, input_data: Dict[str, Any]) -> PhaseTransition:
        """Start a new phase transition."""
        transition = PhaseTransition(
            from_phase=from_phase,
            to_phase=to_phase,
            status=TransitionStatus.IN_PROGRESS,
            start_time=datetime.now(),
            input_data=input_data
        )
        
        # Validate dependencies
        if not self._check_dependencies(to_phase):
            transition.status = TransitionStatus.FAILED
            transition.metadata["error"] = f"Missing dependencies for {to_phase}"
            
        self.transitions.append(transition)
        return transition
        
    def complete_transition(self, transition: PhaseTransition, output_data: Dict[str, Any]) -> bool:
        """Complete a phase transition."""
        transition.end_time = datetime.now()
        transition.output_data = output_data
        
        # Validate the transition
        validation_key = f"{transition.from_phase}_to_{transition.to_phase}"
        if validation_key in self.transition_validators:
            validation = self.transition_validators[validation_key](
                transition.input_data,
                output_data
            )
            transition.validation_result = validation
            
            if validation.is_valid:
                transition.status = TransitionStatus.COMPLETED
                return True
            else:
                transition.status = TransitionStatus.FAILED
                return False
        else:
            # No specific validator, assume valid
            transition.status = TransitionStatus.COMPLETED
            return True
            
    def rollback_transition(self, transition: PhaseTransition):
        """Rollback a failed transition."""
        transition.status = TransitionStatus.ROLLED_BACK
        transition.metadata["rollback_time"] = datetime.now().isoformat()
        
    def get_phase_output(self, phase: str) -> Optional[Dict[str, Any]]:
        """Get the output from a completed phase."""
        for transition in reversed(self.transitions):
            if transition.from_phase == phase and transition.status == TransitionStatus.COMPLETED:
                return transition.output_data
        return None
        
    def _check_dependencies(self, phase: str) -> bool:
        """Check if all dependencies for a phase are satisfied."""
        if phase not in self.phase_dependencies:
            return True
            
        required_phases = self.phase_dependencies[phase]
        completed_phases = {
            t.from_phase for t in self.transitions 
            if t.status == TransitionStatus.COMPLETED
        }
        
        return all(req in completed_phases for req in required_phases)
        
    def _validate_planner_to_designer(self, input_data: Dict[str, Any], output_data: Dict[str, Any]) -> TransitionValidation:
        """Validate transition from planner to designer."""
        errors = []
        warnings = []
        suggestions = []
        
        # Check if plan output exists
        plan_output = output_data.get("plan_output", "")
        if not plan_output:
            errors.append("No plan output found")
        elif len(plan_output) < 100:
            warnings.append("Plan output seems too short")
            suggestions.append("Consider adding more detail to the plan")
            
        # Check for required plan components
        required_components = ["objectives", "approach", "deliverables"]
        for component in required_components:
            if component.lower() not in plan_output.lower():
                warnings.append(f"Plan may be missing {component}")
                
        return TransitionValidation(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
        
    def _validate_designer_to_coder(self, input_data: Dict[str, Any], output_data: Dict[str, Any]) -> TransitionValidation:
        """Validate transition from designer to coder."""
        errors = []
        warnings = []
        suggestions = []
        
        design_output = output_data.get("design_output", "")
        if not design_output:
            errors.append("No design output found")
        else:
            # Check for design elements
            design_elements = ["architecture", "components", "interfaces", "data"]
            missing_elements = []
            for element in design_elements:
                if element.lower() not in design_output.lower():
                    missing_elements.append(element)
                    
            if missing_elements:
                warnings.append(f"Design may be missing: {', '.join(missing_elements)}")
                suggestions.append("Ensure all architectural components are documented")
                
        return TransitionValidation(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
        
    def _validate_coder_to_reviewer(self, input_data: Dict[str, Any], output_data: Dict[str, Any]) -> TransitionValidation:
        """Validate transition from coder to reviewer."""
        errors = []
        warnings = []
        suggestions = []
        
        code_output = output_data.get("code_output", "")
        if not code_output:
            errors.append("No code output found")
        else:
            # Basic code validation
            if len(code_output) < 50:
                warnings.append("Code output seems too short")
                
            # Check for common code patterns
            if "def " not in code_output and "class " not in code_output and "function " not in code_output:
                warnings.append("No function or class definitions found")
                suggestions.append("Ensure code contains proper structure")
                
        # Check execution metrics if available
        metrics = output_data.get("execution_metrics", {})
        if metrics:
            success_rate = metrics.get("success_rate", 0)
            if success_rate < 50:
                warnings.append(f"Low success rate: {success_rate}%")
                suggestions.append("Consider reviewing failed features before proceeding")
                
        return TransitionValidation(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
        
    def _validate_coder_to_executor(self, input_data: Dict[str, Any], output_data: Dict[str, Any]) -> TransitionValidation:
        """Validate transition from coder to executor."""
        errors = []
        warnings = []
        suggestions = []
        
        code_output = output_data.get("code_output", "")
        if not code_output:
            errors.append("No code to execute")
        else:
            # Check for executable patterns
            if "__main__" not in code_output and "if __name__" not in code_output:
                warnings.append("No main entry point detected")
                suggestions.append("Consider adding a main entry point for execution")
                
            # Check for potentially dangerous operations
            dangerous_patterns = ["os.system", "subprocess", "eval", "exec"]
            for pattern in dangerous_patterns:
                if pattern in code_output:
                    warnings.append(f"Potentially dangerous operation detected: {pattern}")
                    suggestions.append("Review security implications before execution")
                    
        return TransitionValidation(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
        
    def get_transition_report(self) -> Dict[str, Any]:
        """Generate a report of all transitions."""
        report = {
            "total_transitions": len(self.transitions),
            "completed": len([t for t in self.transitions if t.status == TransitionStatus.COMPLETED]),
            "failed": len([t for t in self.transitions if t.status == TransitionStatus.FAILED]),
            "rolled_back": len([t for t in self.transitions if t.status == TransitionStatus.ROLLED_BACK]),
            "transitions": []
        }
        
        for transition in self.transitions:
            duration = None
            if transition.start_time and transition.end_time:
                duration = (transition.end_time - transition.start_time).total_seconds()
                
            transition_info = {
                "from": transition.from_phase,
                "to": transition.to_phase,
                "status": transition.status.value,
                "duration_seconds": duration,
                "validation": {
                    "is_valid": transition.validation_result.is_valid if transition.validation_result else None,
                    "errors": transition.validation_result.errors if transition.validation_result else [],
                    "warnings": transition.validation_result.warnings if transition.validation_result else []
                } if transition.validation_result else None
            }
            report["transitions"].append(transition_info)
            
        return report


class TransitionOrchestrator:
    """Orchestrates smooth transitions between phases."""
    
    def __init__(self, transition_manager: PhaseTransitionManager):
        self.transition_manager = transition_manager
        self.transition_hooks = {
            "pre_transition": [],
            "post_transition": [],
            "on_failure": []
        }
        
    def register_hook(self, hook_type: str, hook_fn):
        """Register a transition hook."""
        if hook_type in self.transition_hooks:
            self.transition_hooks[hook_type].append(hook_fn)
            
    async def execute_transition(
        self,
        from_phase: str,
        to_phase: str,
        phase_executor,
        input_data: Dict[str, Any]
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Execute a phase transition with hooks."""
        
        # Pre-transition hooks
        for hook in self.transition_hooks["pre_transition"]:
            await hook(from_phase, to_phase, input_data)
            
        # Start transition
        transition = self.transition_manager.start_transition(from_phase, to_phase, input_data)
        
        try:
            # Execute the phase
            result = await phase_executor(to_phase, input_data)
            
            # Complete transition
            output_data = {"output": result} if isinstance(result, str) else result
            success = self.transition_manager.complete_transition(transition, output_data)
            
            if success:
                # Post-transition hooks
                for hook in self.transition_hooks["post_transition"]:
                    await hook(from_phase, to_phase, output_data)
                    
                return True, output_data
            else:
                # Handle validation failure
                validation = transition.validation_result
                print(f"⚠️ Transition validation failed: {validation.errors}")
                
                # On-failure hooks
                for hook in self.transition_hooks["on_failure"]:
                    await hook(from_phase, to_phase, validation)
                    
                return False, None
                
        except Exception as e:
            # Handle execution failure
            self.transition_manager.rollback_transition(transition)
            
            # On-failure hooks
            for hook in self.transition_hooks["on_failure"]:
                await hook(from_phase, to_phase, str(e))
                
            raise