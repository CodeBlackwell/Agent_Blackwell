"""
TDD Phase Tracker for Operation Red Yellow

This module implements the core RED-YELLOW-GREEN phase tracking system for
mandatory Test-Driven Development in the MVP Incremental Workflow.

Phase Definitions:
- RED: Tests written and confirmed to fail (no implementation exists)
- YELLOW: Tests pass but code awaits review
- GREEN: Tests pass AND code is reviewed/approved
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field


class TDDPhase(Enum):
    """TDD phases for the RED-YELLOW-GREEN cycle"""
    RED = "RED"      # Tests fail - no implementation
    YELLOW = "YELLOW" # Tests pass - awaiting review
    GREEN = "GREEN"   # Tests pass and code reviewed
    
    def get_emoji(self) -> str:
        """Get visual indicator for the phase"""
        return {
            TDDPhase.RED: "🔴",
            TDDPhase.YELLOW: "🟡", 
            TDDPhase.GREEN: "🟢"
        }[self]
    
    def get_description(self) -> str:
        """Get human-readable description of the phase"""
        return {
            TDDPhase.RED: "Tests written and failing (no implementation)",
            TDDPhase.YELLOW: "Tests passing (awaiting review)",
            TDDPhase.GREEN: "Tests passing and code approved"
        }[self]


@dataclass
class PhaseTransition:
    """Records a phase transition event"""
    from_phase: Optional[TDDPhase]
    to_phase: TDDPhase
    timestamp: datetime = field(default_factory=datetime.now)
    reason: str = ""
    metadata: Dict = field(default_factory=dict)


class InvalidPhaseTransition(Exception):
    """Raised when an invalid phase transition is attempted"""
    pass


class TDDPhaseTracker:
    """
    Tracks TDD phases for features in the workflow.
    Enforces strict RED → YELLOW → GREEN progression.
    """
    
    # Valid phase transitions
    VALID_TRANSITIONS = {
        None: [TDDPhase.RED],  # Can only start with RED
        TDDPhase.RED: [TDDPhase.YELLOW],  # RED can only go to YELLOW
        TDDPhase.YELLOW: [TDDPhase.GREEN, TDDPhase.RED],  # YELLOW can go to GREEN or back to RED
        TDDPhase.GREEN: []  # GREEN is terminal (feature complete)
    }
    
    def __init__(self):
        """Initialize the phase tracker"""
        self._feature_phases: Dict[str, TDDPhase] = {}
        self._phase_history: Dict[str, List[PhaseTransition]] = {}
        self._feature_metadata: Dict[str, Dict] = {}
    
    def start_feature(self, feature_id: str, metadata: Optional[Dict] = None) -> None:
        """
        Start tracking a new feature. Must begin in RED phase.
        
        Args:
            feature_id: Unique identifier for the feature
            metadata: Optional metadata about the feature
        """
        if feature_id in self._feature_phases:
            raise ValueError(f"Feature {feature_id} is already being tracked")
        
        # Features must start in RED phase
        self._feature_phases[feature_id] = TDDPhase.RED
        self._phase_history[feature_id] = [
            PhaseTransition(
                from_phase=None,
                to_phase=TDDPhase.RED,
                reason="Feature started - tests must be written first"
            )
        ]
        self._feature_metadata[feature_id] = metadata or {}
    
    def transition_to(self, feature_id: str, new_phase: TDDPhase, 
                     reason: str = "", metadata: Optional[Dict] = None) -> None:
        """
        Transition a feature to a new phase.
        
        Args:
            feature_id: Feature to transition
            new_phase: Target phase
            reason: Reason for the transition
            metadata: Optional transition metadata
            
        Raises:
            InvalidPhaseTransition: If the transition is not allowed
        """
        if feature_id not in self._feature_phases:
            raise ValueError(f"Feature {feature_id} is not being tracked")
        
        current_phase = self._feature_phases[feature_id]
        
        # Validate transition
        if not self.validate_transition(current_phase, new_phase):
            raise InvalidPhaseTransition(
                f"Cannot transition from {current_phase.value} to {new_phase.value}. "
                f"Valid transitions: {[p.value for p in self.VALID_TRANSITIONS[current_phase]]}"
            )
        
        # Record transition
        transition = PhaseTransition(
            from_phase=current_phase,
            to_phase=new_phase,
            reason=reason,
            metadata=metadata or {}
        )
        
        self._feature_phases[feature_id] = new_phase
        self._phase_history[feature_id].append(transition)
    
    def validate_transition(self, from_phase: Optional[TDDPhase], 
                          to_phase: TDDPhase) -> bool:
        """
        Check if a phase transition is valid.
        
        Args:
            from_phase: Current phase (None if starting)
            to_phase: Target phase
            
        Returns:
            True if transition is valid, False otherwise
        """
        return to_phase in self.VALID_TRANSITIONS.get(from_phase, [])
    
    def get_current_phase(self, feature_id: str) -> Optional[TDDPhase]:
        """Get the current phase for a feature"""
        return self._feature_phases.get(feature_id)
    
    def get_phase_history(self, feature_id: str) -> List[PhaseTransition]:
        """Get the complete phase history for a feature"""
        return self._phase_history.get(feature_id, [])
    
    def is_feature_complete(self, feature_id: str) -> bool:
        """Check if a feature has reached GREEN phase"""
        return self.get_current_phase(feature_id) == TDDPhase.GREEN
    
    def get_all_features(self) -> Dict[str, TDDPhase]:
        """Get current phases for all tracked features"""
        return self._feature_phases.copy()
    
    def get_features_in_phase(self, phase: TDDPhase) -> List[str]:
        """Get all features currently in a specific phase"""
        return [
            feature_id 
            for feature_id, current_phase in self._feature_phases.items()
            if current_phase == phase
        ]
    
    def get_visual_status(self, feature_id: str) -> str:
        """Get a visual representation of the feature's current phase"""
        phase = self.get_current_phase(feature_id)
        if not phase:
            return "❓ Not tracked"
        
        return f"{phase.get_emoji()} {phase.value}: {phase.get_description()}"
    
    def get_summary_report(self) -> str:
        """Generate a summary report of all features and their phases"""
        if not self._feature_phases:
            return "No features being tracked"
        
        lines = ["TDD Phase Tracker Summary", "=" * 50]
        
        # Count features by phase
        phase_counts = {phase: 0 for phase in TDDPhase}
        for current_phase in self._feature_phases.values():
            phase_counts[current_phase] += 1
        
        # Overall statistics
        lines.append("\nOverall Statistics:")
        for phase in TDDPhase:
            count = phase_counts[phase]
            if count > 0:
                lines.append(f"  {phase.get_emoji()} {phase.value}: {count} features")
        
        # Feature details
        lines.append("\nFeature Details:")
        for feature_id, phase in sorted(self._feature_phases.items()):
            lines.append(f"  {feature_id}: {self.get_visual_status(feature_id)}")
            
            # Show last transition
            history = self.get_phase_history(feature_id)
            if len(history) > 1:
                last_transition = history[-1]
                time_str = last_transition.timestamp.strftime("%H:%M:%S")
                lines.append(f"    Last transition: {time_str} - {last_transition.reason}")
        
        return "\n".join(lines)
    
    def get_phase_duration(self, feature_id: str, phase: TDDPhase) -> Optional[float]:
        """
        Get the duration (in seconds) a feature spent in a specific phase.
        
        Args:
            feature_id: Feature to check
            phase: Phase to measure
            
        Returns:
            Duration in seconds, or None if feature never entered this phase
        """
        history = self.get_phase_history(feature_id)
        if not history:
            return None
        
        phase_start = None
        phase_end = None
        
        for i, transition in enumerate(history):
            if transition.to_phase == phase:
                phase_start = transition.timestamp
            elif phase_start and transition.from_phase == phase:
                phase_end = transition.timestamp
                break
        
        # If still in this phase
        if phase_start and not phase_end and self.get_current_phase(feature_id) == phase:
            phase_end = datetime.now()
        
        if phase_start and phase_end:
            return (phase_end - phase_start).total_seconds()
        
        return None
    
    def enforce_red_phase_start(self, feature_id: str) -> None:
        """
        Enforce that a feature starts in RED phase.
        This is called when starting implementation to ensure TDD compliance.
        
        Raises:
            InvalidPhaseTransition: If feature is not in RED phase
        """
        current_phase = self.get_current_phase(feature_id)
        if current_phase != TDDPhase.RED:
            if current_phase is None:
                raise InvalidPhaseTransition(
                    f"Feature {feature_id} must start with RED phase (write tests first)"
                )
            else:
                raise InvalidPhaseTransition(
                    f"Feature {feature_id} is in {current_phase.value} phase. "
                    "Cannot start implementation without being in RED phase."
                )
    
    def get_phase_distribution(self) -> Dict[TDDPhase, int]:
        """
        Get the distribution of features across phases.
        
        Returns:
            Dictionary mapping each phase to the count of features in that phase
        """
        distribution = {phase: 0 for phase in TDDPhase}
        for phase in self._feature_phases.values():
            distribution[phase] += 1
        return distribution
    
    def get_summary(self) -> Dict[str, any]:
        """
        Get a summary of the tracker state.
        
        Returns:
            Dictionary with summary information including total transitions
        """
        total_transitions = sum(len(history) for history in self._phase_history.values())
        return {
            "total_transitions": total_transitions,
            "total_features": len(self._feature_phases),
            "phase_distribution": self.get_phase_distribution(),
            "features_by_phase": {
                phase.value: self.get_features_in_phase(phase)
                for phase in TDDPhase
            }
        }