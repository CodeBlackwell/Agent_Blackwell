"""TDD-specific models for the orchestrator"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Dict, List, Optional, Any


class TDDPhase(Enum):
    """TDD workflow phases"""
    RED = "RED"        # Write failing tests
    YELLOW = "YELLOW"  # Write minimal code to pass
    GREEN = "GREEN"    # All tests passing
    COMPLETE = "COMPLETE"  # Feature complete


@dataclass
class TDDFeature:
    """Represents a feature to be implemented using TDD"""
    id: str
    description: str
    test_criteria: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PhaseResult:
    """Result from executing a TDD phase"""
    phase: TDDPhase
    success: bool
    attempts: int
    duration_seconds: float
    agent_outputs: Dict[str, str] = field(default_factory=dict)
    test_results: Optional[Dict[str, Any]] = None
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TDDCycle:
    """Tracks a single TDD cycle for a feature"""
    feature_id: str
    feature_description: str
    current_phase: TDDPhase
    phase_history: List[PhaseResult] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    generated_tests: str = ""
    generated_code: str = ""
    is_complete: bool = False
    
    def get_phase_result(self, phase: TDDPhase) -> Optional[PhaseResult]:
        """Get the most recent result for a specific phase"""
        for result in reversed(self.phase_history):
            if result.phase == phase:
                return result
        return None
    
    def get_total_attempts(self, phase: TDDPhase) -> int:
        """Get total attempts for a specific phase"""
        return sum(1 for r in self.phase_history if r.phase == phase)


@dataclass
class TDDOrchestratorConfig:
    """Configuration for TDD Orchestrator"""
    max_phase_retries: int = 3
    max_total_retries: int = 10
    timeout_seconds: int = 300
    require_review_approval: bool = True
    verbose_output: bool = True
    auto_fix_syntax_errors: bool = True
    test_framework: str = "pytest"
    
    # Phase-specific timeouts
    phase_timeouts: Dict[str, int] = field(default_factory=lambda: {
        "RED": 60,
        "YELLOW": 120,
        "GREEN": 30
    })
    
    # Retry strategies
    retry_strategies: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        "syntax_error": {"max_attempts": 2, "delay_seconds": 1},
        "test_failure": {"max_attempts": 3, "delay_seconds": 2},
        "import_error": {"max_attempts": 2, "delay_seconds": 1}
    })


@dataclass
class FeatureResult:
    """Final result of implementing a feature"""
    feature_id: str
    feature_description: str
    success: bool
    cycles: List[TDDCycle]
    total_duration_seconds: float
    phase_metrics: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    final_tests: str = ""
    final_code: str = ""
    test_coverage: Optional[float] = None
    
    def get_total_attempts(self) -> int:
        """Get total attempts across all cycles"""
        return sum(len(cycle.phase_history) for cycle in self.cycles)


@dataclass
class AgentContext:
    """Context passed to agents during invocation"""
    phase: TDDPhase
    feature_id: str
    feature_description: str
    attempt_number: int
    previous_attempts: List[Dict[str, Any]]
    phase_context: Dict[str, Any]
    global_context: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for agent input"""
        return {
            "phase": self.phase.value,
            "feature_id": self.feature_id,
            "feature_description": self.feature_description,
            "attempt_number": self.attempt_number,
            "previous_attempts": self.previous_attempts,
            "phase_context": self.phase_context,
            "global_context": self.global_context
        }


@dataclass
class RetryDecision:
    """Decision on whether to retry a phase"""
    should_retry: bool
    reason: str
    suggestions: List[str] = field(default_factory=list)
    delay_seconds: int = 0


@dataclass
class MetricsSnapshot:
    """Snapshot of metrics at a point in time"""
    timestamp: datetime
    active_features: int
    completed_features: int
    failed_features: int
    total_phases_executed: int
    success_rate: float
    average_cycle_time: float
    phase_distribution: Dict[str, int] = field(default_factory=dict)