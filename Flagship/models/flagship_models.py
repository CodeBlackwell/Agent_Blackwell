"""Data models for flagship TDD orchestrator"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Dict, List, Optional, Any


class TDDPhase(Enum):
    """TDD workflow phases"""
    RED = "RED"        # Write failing tests
    YELLOW = "YELLOW"  # Write minimal code to pass
    GREEN = "GREEN"    # All tests passing
    REFACTOR = "REFACTOR"  # Optional refactoring phase


class AgentType(Enum):
    """Types of agents in the TDD workflow"""
    TEST_WRITER = "test_writer_flagship"
    CODER = "coder_flagship"
    TEST_RUNNER = "test_runner_flagship"
    ORCHESTRATOR = "flagship_orchestrator"


class TestStatus(Enum):
    """Status of test execution"""
    NOT_RUN = auto()
    PASSED = auto()
    FAILED = auto()
    ERROR = auto()
    SKIPPED = auto()


@dataclass
class AgentMessage:
    """Message passed between agents"""
    from_agent: AgentType
    to_agent: AgentType
    phase: TDDPhase
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class TestResult:
    """Result of a single test execution"""
    test_name: str
    status: TestStatus
    error_message: Optional[str] = None
    duration_ms: float = 0.0
    stdout: Optional[str] = None
    stderr: Optional[str] = None


@dataclass
class PhaseResult:
    """Result of a TDD phase execution"""
    phase: TDDPhase
    success: bool
    agent: AgentType
    output: str
    test_results: List[TestResult] = field(default_factory=list)
    duration_seconds: float = 0.0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PhaseTransition:
    """Represents a transition between TDD phases"""
    from_phase: TDDPhase
    to_phase: TDDPhase
    validation_passed: bool
    reason: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TDDWorkflowState:
    """Tracks the current state of the TDD workflow"""
    current_phase: TDDPhase
    phase_history: List[PhaseTransition] = field(default_factory=list)
    phase_results: List[PhaseResult] = field(default_factory=list)
    requirements: str = ""
    generated_tests: List[str] = field(default_factory=list)
    generated_code: List[str] = field(default_factory=list)
    all_tests_passing: bool = False
    iteration_count: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    
    def add_phase_result(self, result: PhaseResult):
        """Add a phase result to the workflow state"""
        self.phase_results.append(result)
    
    def add_transition(self, transition: PhaseTransition):
        """Record a phase transition"""
        self.phase_history.append(transition)
        self.current_phase = transition.to_phase
    
    def get_phase_results(self, phase: TDDPhase) -> List[PhaseResult]:
        """Get all results for a specific phase"""
        return [r for r in self.phase_results if r.phase == phase]
    
    def get_latest_phase_result(self, phase: TDDPhase) -> Optional[PhaseResult]:
        """Get the most recent result for a specific phase"""
        results = self.get_phase_results(phase)
        return results[-1] if results else None
    
    def get_test_summary(self) -> Dict[str, int]:
        """Get summary of test results"""
        summary = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "error": 0,
            "skipped": 0
        }
        
        latest_green = self.get_latest_phase_result(TDDPhase.GREEN)
        if latest_green and latest_green.test_results:
            for test in latest_green.test_results:
                summary["total"] += 1
                if test.status == TestStatus.PASSED:
                    summary["passed"] += 1
                elif test.status == TestStatus.FAILED:
                    summary["failed"] += 1
                elif test.status == TestStatus.ERROR:
                    summary["error"] += 1
                elif test.status == TestStatus.SKIPPED:
                    summary["skipped"] += 1
        
        return summary


@dataclass
class TDDWorkflowConfig:
    """Configuration for the TDD workflow"""
    max_iterations: int = 5
    timeout_seconds: int = 300
    auto_refactor: bool = False
    verbose_output: bool = True
    test_framework: str = "pytest"
    test_directory: str = "generated/tests"
    code_directory: str = "generated/src"
    coverage_threshold: float = 80.0
    strict_tdd: bool = True  # If True, code must fail tests before implementation