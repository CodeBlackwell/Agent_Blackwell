"""
Shared data models for the multi-agent workflow system.
This module contains common data classes used across orchestrator, workflows, and tests
to avoid circular import issues.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime


class TeamMember(Enum):
    """Enumeration of available team members"""
    PLANNER = "planner_agent"
    DESIGNER = "designer_agent" 
    CODER = "coder_agent"
    TEST_WRITER = "test_writer_agent"
    REVIEWER = "reviewer_agent"


class WorkflowStep(Enum):
    """Enumeration of workflow steps"""
    PLANNING = "planning"
    DESIGN = "design"
    CODING = "coding"
    TESTING = "testing"
    REVIEW = "review"


@dataclass
class TeamMemberResult:
    """Result from a team member execution"""
    team_member: TeamMember
    output: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time: Optional[float] = None
    error: Optional[str] = None


@dataclass
class CodingTeamInput:
    """Input data for the coding team workflow"""
    requirements: str
    workflow_type: str = "full"  # "tdd", "full", or "individual"
    step_type: Optional[str] = None  # For individual workflows
    context: Dict[str, Any] = field(default_factory=dict)
    max_retries: int = 3
    timeout_seconds: int = 300


@dataclass
class CodingTeamResult:
    """Result from the coding team workflow execution"""
    success: bool
    results: List[TeamMemberResult]
    execution_time: float
    workflow_type: str
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Enhanced monitoring fields
    monitoring_report: Optional[str] = None
    execution_tracer: Optional[Any] = None  # WorkflowExecutionTracer instance


@dataclass
class TestStepResult:
    """Result from a single test step"""
    name: str
    start_time: float
    end_time: Optional[float] = None
    success: bool = False
    error: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration(self) -> float:
        """Calculate step duration"""
        if self.end_time is None:
            return 0.0
        return self.end_time - self.start_time
    
    @property
    def status_emoji(self) -> str:
        """Get status emoji for display"""
        if self.end_time is None:
            return "⏳"
        return "✅" if self.success else "❌"
