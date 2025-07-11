"""Phase Manager for TDD workflow - manages phase transitions and validation"""

from datetime import datetime
from typing import Dict, Optional, Tuple, List, Any
from .models import TDDPhase, TDDCycle, PhaseResult


class PhaseManager:
    """Manages TDD phase transitions and cycle tracking"""
    
    def __init__(self):
        self.active_cycles: Dict[str, TDDCycle] = {}
        self.completed_cycles: List[TDDCycle] = []
        
        # Define valid phase transitions
        self.valid_transitions = {
            TDDPhase.RED: [TDDPhase.YELLOW],     # RED can only go to YELLOW
            TDDPhase.YELLOW: [TDDPhase.GREEN],    # YELLOW can only go to GREEN
            TDDPhase.GREEN: [TDDPhase.YELLOW, TDDPhase.COMPLETE],  # GREEN can go back to YELLOW or COMPLETE
            TDDPhase.COMPLETE: []  # COMPLETE is terminal
        }
        
        # Define phase validation rules
        self.phase_validators = {
            TDDPhase.RED: self._validate_red_phase,
            TDDPhase.YELLOW: self._validate_yellow_phase,
            TDDPhase.GREEN: self._validate_green_phase
        }
    
    def start_cycle(self, feature_id: str, feature_context: Dict = None) -> TDDCycle:
        """Start a new TDD cycle for a feature"""
        feature_context = feature_context or {}
        
        cycle = TDDCycle(
            feature_id=feature_id,
            feature_description=feature_context.get("description", ""),
            current_phase=TDDPhase.RED
        )
        
        # Record initial phase entry
        initial_result = PhaseResult(
            phase=TDDPhase.RED,
            success=False,  # Not yet executed
            attempts=1,
            duration_seconds=0.0,
            metadata={"action": "phase_started"}
        )
        cycle.phase_history.append(initial_result)
        
        self.active_cycles[feature_id] = cycle
        return cycle
    
    def transition_phase(self, feature_id: str, context: Dict) -> Tuple[TDDPhase, bool]:
        """
        Attempt to transition to the next phase
        Returns: (new_phase, success)
        """
        if feature_id not in self.active_cycles:
            return TDDPhase.RED, False
        
        cycle = self.active_cycles[feature_id]
        current_phase = cycle.current_phase
        
        # Validate current phase completion
        if current_phase in self.phase_validators:
            is_valid, validation_errors = self.phase_validators[current_phase](cycle, context)
            if not is_valid:
                print(f"❌ Phase validation failed: {', '.join(validation_errors)}")
                return current_phase, False
        
        # Determine next phase
        next_phase = self._determine_next_phase(current_phase, context)
        
        # Check if transition is valid
        if next_phase not in self.valid_transitions.get(current_phase, []):
            print(f"❌ Invalid transition: {current_phase.value} → {next_phase.value}")
            return current_phase, False
        
        # Perform transition
        cycle.current_phase = next_phase
        print(f"✅ Phase transition: {current_phase.value} → {next_phase.value}")
        
        # If transitioning to COMPLETE, mark cycle as complete
        if next_phase == TDDPhase.COMPLETE:
            cycle.is_complete = True
            cycle.end_time = datetime.now()
        
        return next_phase, True
    
    def retry_current_phase(self, feature_id: str, retry_context: Dict) -> bool:
        """Retry the current phase with updated context"""
        if feature_id not in self.active_cycles:
            return False
        
        cycle = self.active_cycles[feature_id]
        current_phase = cycle.current_phase
        
        # Find the current phase result and increment attempts
        for result in reversed(cycle.phase_history):
            if result.phase == current_phase:
                result.attempts += 1
                if "error" in retry_context:
                    result.errors.append(retry_context["error"])
                break
        
        return True
    
    def record_phase_result(self, feature_id: str, result: PhaseResult):
        """Record the result of a phase execution"""
        if feature_id not in self.active_cycles:
            return
        
        cycle = self.active_cycles[feature_id]
        cycle.phase_history.append(result)
        
        # Update cycle data based on phase
        if result.phase == TDDPhase.RED and "tests" in result.agent_outputs:
            cycle.generated_tests = result.agent_outputs["tests"]
        elif result.phase == TDDPhase.YELLOW and "code" in result.agent_outputs:
            cycle.generated_code = result.agent_outputs["code"]
    
    def complete_cycle(self, feature_id: str, success: bool) -> Optional[TDDCycle]:
        """Complete a TDD cycle and move it to completed list"""
        if feature_id not in self.active_cycles:
            return None
        
        cycle = self.active_cycles[feature_id]
        cycle.is_complete = True
        cycle.end_time = datetime.now()
        
        if success:
            cycle.current_phase = TDDPhase.COMPLETE
        
        # Move to completed list
        self.completed_cycles.append(cycle)
        del self.active_cycles[feature_id]
        
        return cycle
    
    def get_cycle(self, feature_id: str) -> Optional[TDDCycle]:
        """Get an active cycle by feature ID"""
        return self.active_cycles.get(feature_id)
    
    def _determine_next_phase(self, current_phase: TDDPhase, context: Dict) -> TDDPhase:
        """Determine the next phase based on current phase and context"""
        if current_phase == TDDPhase.RED:
            return TDDPhase.YELLOW
        elif current_phase == TDDPhase.YELLOW:
            return TDDPhase.GREEN
        elif current_phase == TDDPhase.GREEN:
            # Check if all tests pass
            if context.get("all_tests_pass", False):
                return TDDPhase.COMPLETE
            else:
                return TDDPhase.YELLOW  # Go back to fix code
        else:
            return current_phase
    
    def _validate_red_phase(self, cycle: TDDCycle, context: Dict) -> Tuple[bool, List[str]]:
        """Validate RED phase completion"""
        errors = []
        
        # Check if tests were written
        if not cycle.generated_tests:
            errors.append("No tests were generated")
        
        # Check if tests actually fail (they should in RED phase)
        if context.get("tests_pass", False):
            errors.append("Tests should fail in RED phase (TDD principle)")
        
        # Check for syntax errors
        if context.get("has_syntax_errors", False):
            errors.append("Tests contain syntax errors")
        
        return len(errors) == 0, errors
    
    def _validate_yellow_phase(self, cycle: TDDCycle, context: Dict) -> Tuple[bool, List[str]]:
        """Validate YELLOW phase completion"""
        errors = []
        
        # Check if code was written
        if not cycle.generated_code:
            errors.append("No implementation code was generated")
        
        # Check for syntax errors
        if context.get("has_syntax_errors", False):
            errors.append("Implementation contains syntax errors")
        
        return len(errors) == 0, errors
    
    def _validate_green_phase(self, cycle: TDDCycle, context: Dict) -> Tuple[bool, List[str]]:
        """Validate GREEN phase completion"""
        errors = []
        
        # Check if tests were executed
        if "test_results" not in context:
            errors.append("Tests were not executed")
        
        # No specific validation for GREEN - the test results determine next step
        return len(errors) == 0, errors
    
    def get_phase_summary(self, feature_id: str) -> Dict[str, Any]:
        """Get a summary of phase execution for a feature"""
        cycle = self.active_cycles.get(feature_id) or next(
            (c for c in self.completed_cycles if c.feature_id == feature_id), None
        )
        
        if not cycle:
            return {}
        
        summary = {
            "feature_id": feature_id,
            "current_phase": cycle.current_phase.value,
            "is_complete": cycle.is_complete,
            "phase_attempts": {}
        }
        
        # Count attempts per phase
        for phase in TDDPhase:
            attempts = cycle.get_total_attempts(phase)
            if attempts > 0:
                summary["phase_attempts"][phase.value] = attempts
        
        # Add timing info
        if cycle.end_time:
            duration = (cycle.end_time - cycle.start_time).total_seconds()
            summary["total_duration_seconds"] = duration
        
        return summary