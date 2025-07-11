"""
Parent System Compatibility Models

This module provides compatibility with the parent workflow system's data models.
It allows Flagship to work both standalone and as part of the larger system.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any


class TeamMember(Enum):
    """Team member types for compatibility with parent system"""
    planner = "planner_agent"
    designer = "designer_agent" 
    coder = "coder_agent"
    test_writer = "test_writer_agent"
    reviewer = "reviewer_agent"
    executor = "executor_agent"


@dataclass
class TeamMemberResult:
    """Result from a team member - compatible with parent system"""
    team_member: TeamMember
    output: str
    name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if not self.name and self.team_member:
            self.name = self.team_member.value.replace('_agent', '')


# Type aliases for easier migration
CodingTeamInput = Dict[str, Any]  # Simplified for Flagship use
WorkflowExecutionTracer = Any  # Optional tracer from parent system
WorkflowExecutionReport = Any  # Optional report from parent system