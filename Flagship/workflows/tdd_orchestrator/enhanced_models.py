"""Enhanced TDD models with requirements analysis and architecture planning phases"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum, auto
from typing import Dict, List, Optional, Any

# Import the original models to extend
from .models import (
    TDDFeature, PhaseResult, TDDCycle, FeatureResult, 
    AgentContext, RetryDecision, MetricsSnapshot
)


class EnhancedTDDPhase(Enum):
    """Enhanced TDD workflow phases with planning stages"""
    REQUIREMENTS = "REQUIREMENTS"  # Analyze and expand requirements
    ARCHITECTURE = "ARCHITECTURE"  # Plan system architecture
    RED = "RED"                    # Write failing tests
    YELLOW = "YELLOW"              # Write minimal code to pass
    GREEN = "GREEN"                # All tests passing
    VALIDATION = "VALIDATION"      # Validate all requirements met
    COMPLETE = "COMPLETE"          # Feature complete


@dataclass
class ProjectArchitecture:
    """Represents the planned architecture for the project"""
    project_type: str  # e.g., "web_app", "rest_api", "cli_tool"
    structure: Dict[str, List[str]]  # Directory structure
    technology_stack: Dict[str, str]  # Frontend, backend, database, etc.
    components: List['ArchitectureComponent']
    api_contracts: Optional[List['APIContract']] = None
    dependencies: Dict[str, List[str]] = field(default_factory=dict)


@dataclass
class ArchitectureComponent:
    """A component in the system architecture"""
    name: str
    type: str  # frontend, backend, shared, database
    description: str
    files: List[str]
    dependencies: List[str] = field(default_factory=list)
    interfaces: List[str] = field(default_factory=list)


@dataclass
class APIContract:
    """API endpoint contract"""
    method: str
    path: str
    description: str
    request_schema: Optional[Dict[str, Any]] = None
    response_schema: Optional[Dict[str, Any]] = None
    auth_required: bool = False


@dataclass
class TestableFeature:
    """Feature broken down into testable components"""
    id: str
    title: str
    description: str
    components: List[str]
    test_criteria: List['TestCriteria']
    complexity: str  # Low, Medium, High
    dependencies: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "components": self.components,
            "test_criteria": [tc.to_dict() if hasattr(tc, 'to_dict') else asdict(tc) for tc in self.test_criteria],
            "complexity": self.complexity,
            "dependencies": self.dependencies
        }


@dataclass
class TestCriteria:
    """Specific test criteria for a feature component"""
    component: str
    test_type: str  # unit, integration, e2e
    description: str
    expected_behavior: str


@dataclass
class ExpandedRequirements:
    """Requirements expanded from vague input"""
    original_requirements: str
    project_type: str
    expanded_description: str
    features: List[TestableFeature]
    technical_requirements: List[str]
    non_functional_requirements: List[str]
    constraints: List[str] = field(default_factory=list)


@dataclass
class EnhancedTDDOrchestratorConfig:
    """Enhanced configuration for TDD Orchestrator"""
    # Original config options
    max_phase_retries: int = 3
    max_total_retries: int = 10
    timeout_seconds: int = 300
    require_review_approval: bool = True
    verbose_output: bool = True
    auto_fix_syntax_errors: bool = True
    test_framework: str = "pytest"
    
    # New config options
    enable_requirements_analysis: bool = True
    enable_architecture_planning: bool = True
    enable_feature_validation: bool = True
    multi_file_support: bool = True
    feature_based_implementation: bool = True
    parallel_feature_implementation: bool = False
    
    # Phase-specific timeouts (extended)
    phase_timeouts: Dict[str, int] = field(default_factory=lambda: {
        "REQUIREMENTS": 60,
        "ARCHITECTURE": 90,
        "RED": 60,
        "YELLOW": 120,
        "GREEN": 30,
        "VALIDATION": 60
    })
    
    # Retry strategies (extended)
    retry_strategies: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        "syntax_error": {"max_attempts": 2, "delay_seconds": 1},
        "test_failure": {"max_attempts": 3, "delay_seconds": 2},
        "import_error": {"max_attempts": 2, "delay_seconds": 1},
        "validation_failure": {"max_attempts": 2, "delay_seconds": 3}
    })


@dataclass
class EnhancedFeatureResult(FeatureResult):
    """Extended feature result with planning artifacts"""
    expanded_requirements: Optional[ExpandedRequirements] = None
    architecture: Optional[ProjectArchitecture] = None
    validation_report: Optional['ValidationReport'] = None
    generated_files: Dict[str, str] = field(default_factory=dict)  # filepath -> content


@dataclass
class ValidationReport:
    """Report from validation phase"""
    all_requirements_met: bool
    implemented_features: List[str]
    missing_features: List[str]
    test_coverage_report: Dict[str, float]  # component -> coverage
    integration_test_results: Dict[str, bool]  # test -> pass/fail
    recommendations: List[str] = field(default_factory=list)


@dataclass
class MultiFileOutput:
    """Container for multi-file generation output"""
    files: Dict[str, str]  # filepath -> content
    main_file: str  # Entry point file
    file_types: Dict[str, str]  # filepath -> type (frontend, backend, config, etc.)
    dependencies: Dict[str, List[str]]  # Language -> dependencies


@dataclass
class EnhancedAgentContext(AgentContext):
    """Extended context with planning artifacts"""
    expanded_requirements: Optional[ExpandedRequirements] = None
    architecture: Optional[ProjectArchitecture] = None
    current_feature: Optional[TestableFeature] = None
    generated_files: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for agent input"""
        base_dict = super().to_dict()
        base_dict.update({
            "expanded_requirements": self.expanded_requirements.__dict__ if self.expanded_requirements else None,
            "architecture": self._architecture_to_dict() if self.architecture else None,
            "current_feature": self.current_feature.__dict__ if self.current_feature else None,
            "generated_files": self.generated_files
        })
        return base_dict
    
    def _architecture_to_dict(self) -> Dict[str, Any]:
        """Convert architecture to dictionary"""
        if not self.architecture:
            return None
        return {
            "project_type": self.architecture.project_type,
            "structure": self.architecture.structure,
            "technology_stack": self.architecture.technology_stack,
            "components": [comp.__dict__ for comp in self.architecture.components],
            "api_contracts": [contract.__dict__ for contract in self.architecture.api_contracts] if self.architecture.api_contracts else None,
            "dependencies": self.architecture.dependencies
        }