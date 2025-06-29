"""
Centralized Pydantic schema definitions for every autonomous‑agent prompt template
used throughout the Job Pipeline. Each model enumerates the variables that can be
injected into its corresponding template as context‑aware placeholders.

Guiding principles
------------------
1. **Explicitness over Implicitness** – every value consumed by a prompt must be
defined here so that validation failures are caught at compilation time, not at
runtime.
2. **Loose coupling** – only include information the agent actually needs at its
stage of the pipeline; upstream artefacts are passed via dedicated fields such
as `previous_outputs` rather than through gigantic context blobs.
3. **Reasonable defaults** – to keep developer ergonomics high, most fields
default to an empty string, empty list, or sensible primitive so a minimal
object can be instantiated quickly during experimentation.
"""

from __future__ import annotations

from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Shared Enums and Types
# ---------------------------------------------------------------------------

class PipelineStageStatus(str, Enum):
    """Status enum for pipeline stages."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"

class PriorityLevel(str, Enum):
    """Priority level for tasks and features."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

# ---------------------------------------------------------------------------
# Planner
# ---------------------------------------------------------------------------

class PlannerSchema(BaseModel):
    """Variable set for the *Planning Agent* template."""

    job_request: str = Field("", description="Verbatim user request or problem statement.")
    prior_context: str = Field(
        "", description="Accumulated background knowledge relevant to planning.")
    business_objective: str = Field(
        "", description="Higher‑level goal the user ultimately wants to achieve.")
    constraints: str = Field(
        "", description="Budget, time, technology, or policy constraints explicitly stated by the user.")
    risk_tolerance: str = Field(
        "", description="Qualitative sense of how aggressive/conservative the plan can be.")
    available_agents: List[str] = Field(default_factory=list, 
        description="List of available specialist agents that can be incorporated in the plan.")
    current_time: Optional[str] = Field(None, 
        description="Current timestamp for time-sensitive planning.")
    reference_architecture: str = Field("", 
        description="System architecture reference documents for context.")

# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

class OrchestratorSchema(BaseModel):
    """Variable set for the *Orchestrator Agent* template."""

    pipeline_description: str = Field("", description="Human‑readable summary of the active pipeline.")
    job_request: str = Field("", description="Original user request (echo).")
    context: str = Field("", description="Global contextual data shared across agents.")
    state_snapshot: str = Field(
        "", description="JSON string of current StateManager snapshot (pipelines & stages).")
    last_event: str = Field("", description="Most recent event or status change to react to.")
    stage_dependencies: Dict[str, List[str]] = Field(default_factory=dict,
        description="Map of stage names to their dependency stage names.")
    agent_capabilities: Dict[str, List[str]] = Field(default_factory=dict,
        description="Map of agent names to their capability descriptions.")
    execution_metrics: Dict[str, Any] = Field(default_factory=dict,
        description="Performance metrics and resource utilization of different stages.")
    error_context: str = Field("", description="Details about any error encountered in the pipeline.")

# ---------------------------------------------------------------------------
# Pipeline Analysis
# ---------------------------------------------------------------------------

class PipelineAnalysisSchema(BaseModel):
    """Schema for analyzing a feature pipeline execution strategy."""
    
    pipeline_json: str = Field("", description="JSON representation of the feature pipeline.")
    feature_name: str = Field("", description="Name of the feature being analyzed.")
    execution_strategy: Optional[str] = Field(None, description="Current execution strategy if any.")
    resource_constraints: Dict[str, Any] = Field(default_factory=dict, 
        description="Resource constraints for execution.")
    dependencies_resolved: bool = Field(True, description="Whether all dependencies are resolved.")
    stage_priorities: Dict[str, PriorityLevel] = Field(default_factory=dict, 
        description="Priority levels for different stages.")
    expected_timeline: Dict[str, Union[int, float]] = Field(default_factory=dict,
        description="Expected time estimations for stages in minutes.")

# ---------------------------------------------------------------------------
# Specification
# ---------------------------------------------------------------------------

class SpecificationSchema(BaseModel):
    """Variable set for the *Specification Agent* template."""

    feature_name: str = ""
    feature_description: str = ""
    user_stories: List[str] = Field(default_factory=list)
    architectural_constraints: str = ""
    non_functional_requirements: str = ""
    reference_implementations: List[str] = Field(default_factory=list, 
        description="Links or citations for RAG look‑ups.")
    previous_outputs: str = Field(
        "", description="Upstream planner/orchestrator artefacts relevant to this feature.")
    api_requirements: Dict[str, Any] = Field(default_factory=dict,
        description="API specifications including endpoints, methods, and data structures.")
    database_schema: str = Field("", description="Database schema requirements if applicable.")
    integration_points: List[Dict[str, str]] = Field(default_factory=list,
        description="Integration points with other systems or components.")
    compliance_requirements: List[str] = Field(default_factory=list,
        description="Compliance and regulatory requirements.")

# ---------------------------------------------------------------------------
# Design
# ---------------------------------------------------------------------------

class DesignSchema(BaseModel):
    """Variable set for the *Design Agent* template."""

    feature_spec: str = ""
    target_stack: str = Field("python", description="Primary language or runtime for the implementation.")
    performance_budget: str = ""
    security_requirements: str = ""
    observability_requirements: str = ""
    previous_outputs: str = ""
    design_patterns: List[str] = Field(default_factory=list,
        description="Recommended design patterns to apply.")
    component_structure: Dict[str, Any] = Field(default_factory=dict,
        description="Component breakdown and relationships.")
    data_flow: str = Field("", description="Description of data flow between components.")
    error_handling_strategy: str = Field("", description="Strategy for error handling and recovery.")
    scaling_considerations: str = Field("", description="Considerations for scaling the solution.")

# ---------------------------------------------------------------------------
# Code
# ---------------------------------------------------------------------------

class CodeSchema(BaseModel):
    """Variable set for the *Code Agent* template."""

    design_doc: str = ""
    language: str = Field("python", description="Target programming language.")
    framework: Optional[str] = None
    coding_guidelines: str = ""
    existing_code: str = ""
    previous_outputs: str = ""
    file_structure: Dict[str, str] = Field(default_factory=dict, 
        description="Map of file paths to brief descriptions.")
    dependencies: Dict[str, str] = Field(default_factory=dict,
        description="External dependencies and version constraints.")
    unit_test_requirements: str = Field("", description="Requirements for unit tests.")
    code_review_feedback: str = Field("", description="Feedback from previous code reviews.")
    version_control_strategy: str = Field("", 
        description="Git workflow instructions and commit message guidelines.")

# ---------------------------------------------------------------------------
# Review
# ---------------------------------------------------------------------------

class ReviewSchema(BaseModel):
    """Variable set for the *Review Agent* template."""

    code_diff: str = ""
    design_reference: str = ""
    specification_reference: str = ""
    review_focus: str = Field(
        "", description="Explicit reviewer attention areas (e.g., security, performance).")
    previous_outputs: str = ""
    static_analysis_results: str = Field("", 
        description="Results from static analysis tools.")
    code_complexity_metrics: Dict[str, Any] = Field(default_factory=dict,
        description="Code complexity and maintainability metrics.")
    previous_issues: List[Dict[str, str]] = Field(default_factory=list,
        description="Recurring issues found in previous reviews.")
    security_checklist: List[str] = Field(default_factory=list,
        description="Security considerations to verify.")
    best_practice_reference: str = Field("", description="Reference to coding best practices.")

# ---------------------------------------------------------------------------
# Test
# ---------------------------------------------------------------------------

class TestSchema(BaseModel):
    """Variable set for the *Test Agent* template."""

    code_under_test: str = ""
    acceptance_criteria: str = ""
    existing_tests: str = ""
    test_framework: str = Field("pytest", description="Default test runner.")
    performance_budget: str = ""
    previous_outputs: str = ""
    test_data_requirements: Dict[str, Any] = Field(default_factory=dict,
        description="Test data requirements and generation strategies.")
    mocking_strategy: str = Field("", description="Strategy for mocking dependencies.")
    test_coverage_targets: Dict[str, float] = Field(default_factory=dict,
        description="Target test coverage percentages by component.")
    edge_cases: List[str] = Field(default_factory=list, 
        description="List of identified edge cases to test.")
    regression_test_scope: str = Field("", description="Scope for regression testing.")

# ---------------------------------------------------------------------------
# MCP‑Git (server‑side tool schema for completeness)
# ---------------------------------------------------------------------------

class MCPGitSchema(BaseModel):
    """Schema for messages sent to the *MCP Git* tool service."""

    operation: str = Field(
        ..., description="One of: branch_create, commit, push, pull_request, merge.")
    repo_path: str = ""
    branch_name: str = ""
    commit_message: str = ""
    diff: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)
    author: str = Field("", description="Author of the commit.")
    reviewer: Optional[str] = Field(None, description="Requested reviewer for pull requests.")
    pr_title: Optional[str] = Field(None, description="Title for pull requests.")
    pr_description: Optional[str] = Field(None, description="Description for pull requests.")
    labels: List[str] = Field(default_factory=list, description="Labels for PRs or commits.")

# ---------------------------------------------------------------------------
# BeeAI Integration Schemas
# ---------------------------------------------------------------------------

class BeeAIMemorySchema(BaseModel):
    """Schema for BeeAI Framework memory management."""
    
    memory_key: str = Field(..., description="Unique identifier for this memory.")
    content_type: str = Field("text", description="Type of content in memory.")
    max_tokens: int = Field(2000, description="Maximum tokens to retain in memory.")
    priority: int = Field(1, description="Priority level for this memory (higher = more important).")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata.")
    timestamp: str = Field(datetime.now().isoformat(), description="Timestamp of memory creation/update.")

class BeeAIToolSchema(BaseModel):
    """Schema for BeeAI Framework tool definitions."""
    
    tool_name: str = Field(..., description="Name of the tool.")
    description: str = Field("", description="Description of what the tool does.")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Tool parameters and types.")
    required_params: List[str] = Field(default_factory=list, description="List of required parameters.")
    examples: List[Dict[str, Any]] = Field(default_factory=list, description="Example tool invocations.")
    tool_provider: str = Field("local", description="Provider of the tool (local, MCP, etc.)")

# ---------------------------------------------------------------------------
# Convenience export list
# ---------------------------------------------------------------------------

__all__ = [
    # Enums and Shared Types
    "PipelineStageStatus",
    "PriorityLevel",
    
    # Agent Schemas
    "PlannerSchema",
    "OrchestratorSchema",
    "PipelineAnalysisSchema",
    "SpecificationSchema",
    "DesignSchema",
    "CodeSchema",
    "ReviewSchema",
    "TestSchema",
    
    # Tool and Integration Schemas
    "MCPGitSchema",
    "BeeAIMemorySchema",
    "BeeAIToolSchema",
]
