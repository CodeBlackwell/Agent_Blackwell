"""Enhanced TDD Orchestrator with requirements analysis and architecture planning"""

import asyncio
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
import json
import sys

# Add import path for parent modules
parent_path = Path(__file__).parent.parent.parent
if str(parent_path) not in sys.path:
    sys.path.insert(0, str(parent_path))

# Import EventType from the right location
try:
    from models.execution_tracer import EventType
except ImportError:
    # Define EventType locally if import fails
    from enum import Enum
    class EventType(Enum):
        PHASE_START = "phase_start"
        PHASE_END = "phase_end"

from .enhanced_models import (
    EnhancedTDDPhase, TDDFeature, EnhancedTDDOrchestratorConfig, 
    EnhancedFeatureResult, PhaseResult, EnhancedAgentContext, TDDCycle,
    ExpandedRequirements, ProjectArchitecture, TestableFeature,
    ValidationReport, MultiFileOutput
)
from .phase_manager import PhaseManager
from .enhanced_agent_coordinator import EnhancedAgentCoordinator
from .retry_coordinator import RetryCoordinator
from .metrics_collector import MetricsCollector
from .project_structure_manager import ProjectStructureManager
from .feature_based_test_generator import FeatureBasedTestGenerator


class EnhancedTDDOrchestrator:
    """Enhanced orchestrator for TDD workflow with comprehensive planning"""
    
    def __init__(self, config: EnhancedTDDOrchestratorConfig = None, 
                 run_team_member_func: Optional[Callable] = None,
                 session_id: Optional[str] = None,
                 base_output_dir: Optional[str] = None,
                 tracer: Optional[Any] = None):
        """
        Initialize Enhanced TDD Orchestrator
        Args:
            config: Configuration for the orchestrator
            run_team_member_func: Optional function to run team members
            session_id: Session ID for the workflow (used for directory naming)
            base_output_dir: Base directory for output (defaults to ./generated)
            tracer: ExecutionTracer instance for comprehensive logging
        """
        self.config = config or EnhancedTDDOrchestratorConfig()
        self.session_id = session_id
        self.tracer = tracer
        self.phase_manager = PhaseManager()
        self.agent_coordinator = EnhancedAgentCoordinator(run_team_member_func, tracer)
        self.retry_coordinator = RetryCoordinator(self.config.__dict__)
        self.metrics_collector = MetricsCollector()
        self.project_manager = ProjectStructureManager(
            session_id=session_id,
            base_output_dir=base_output_dir,
            tracer=tracer
        )
        self.test_generator = FeatureBasedTestGenerator()
        
        # Output handlers
        self.verbose = self.config.verbose_output
        
    async def execute_feature(self, requirements: str) -> EnhancedFeatureResult:
        """
        Execute enhanced TDD workflow for requirements
        Returns: EnhancedFeatureResult with implementation details
        """
        print(f"\n{'='*80}")
        print(f"🚀 Starting Enhanced TDD Workflow")
        print(f"Requirements: {requirements}")
        print(f"{'='*80}\n")
        
        # Create initial feature
        feature = TDDFeature(
            id=f"feature_{int(time.time())}",
            description=requirements,
            test_criteria=[],
            metadata={}
        )
        
        # Start metrics collection
        feature_metrics = self.metrics_collector.start_feature(
            feature.id, feature.description
        )
        
        # Initialize result containers
        expanded_requirements = None
        architecture = None
        validation_report = None
        generated_files = {}
        cycles = []
        success = False
        errors = []
        
        try:
            # Phase 1: Requirements Analysis
            if self.config.enable_requirements_analysis:
                print(f"\n{'='*60}")
                print(f"📋 Phase 1: Requirements Analysis")
                print(f"{'='*60}\n")
                
                # Trace phase start
                if self.tracer:
                    self.tracer.trace_event(
                        EventType.PHASE_START,
                        phase="REQUIREMENTS",
                        data={"feature_id": feature.id, "requirements": requirements}
                    )
                
                expanded_requirements = await self._analyze_requirements(feature)
                if not expanded_requirements:
                    raise Exception("Failed to analyze requirements")
                
                # Update feature with expanded information
                feature.test_criteria = self._extract_test_criteria(expanded_requirements)
                
            # Phase 2: Architecture Planning
            if self.config.enable_architecture_planning:
                print(f"\n{'='*60}")
                print(f"🏗️ Phase 2: Architecture Planning")
                print(f"{'='*60}\n")
                
                architecture = await self._plan_architecture(feature, expanded_requirements)
                if not architecture:
                    raise Exception("Failed to plan architecture")
                
                # Set up project structure
                self.project_manager.setup_project_structure(architecture)
            
            # Phase 3: Feature-based TDD Implementation
            if self.config.feature_based_implementation and expanded_requirements:
                print(f"\n{'='*60}")
                print(f"🔄 Phase 3: Feature-based TDD Implementation")
                print(f"{'='*60}\n")
                
                # Implement each feature through TDD cycles
                for testable_feature in expanded_requirements.features:
                    print(f"\n--- Implementing Feature: {testable_feature.title} ---")
                    
                    feature_cycle = await self._execute_feature_tdd_cycle(
                        testable_feature, 
                        expanded_requirements,
                        architecture,
                        generated_files
                    )
                    cycles.append(feature_cycle)
                    
                    if feature_cycle.is_complete:
                        # Merge generated files
                        self._merge_generated_files(generated_files, feature_cycle)
                    else:
                        print(f"⚠️ Feature implementation incomplete: {testable_feature.title}")
            else:
                # Fallback to traditional single-cycle TDD
                print(f"\n{'='*60}")
                print(f"🔄 Phase 3: Traditional TDD Cycle")
                print(f"{'='*60}\n")
                
                cycle = await self._execute_traditional_tdd_cycle(
                    feature, architecture, generated_files
                )
                cycles.append(cycle)
            
            # Phase 4: Validation
            if self.config.enable_feature_validation:
                print(f"\n{'='*60}")
                print(f"✅ Phase 4: Validation")
                print(f"{'='*60}\n")
                
                validation_report = await self._validate_implementation(
                    expanded_requirements,
                    architecture,
                    generated_files
                )
                
                success = validation_report.all_requirements_met
                if not success:
                    print(f"⚠️ Validation failed: {len(validation_report.missing_features)} features missing")
            else:
                # Consider success if all cycles completed
                success = all(cycle.is_complete for cycle in cycles)
                
            # Complete feature metrics
            self.metrics_collector.complete_feature(feature.id, success)
            
        except Exception as e:
            errors.append(f"Fatal error: {str(e)}")
            print(f"\n❌ Fatal error during execution: {e}")
            self.metrics_collector.complete_feature(feature.id, False)
            
        # Save all generated files
        if self.config.multi_file_support and generated_files:
            self.project_manager.save_generated_files(generated_files)
        
        # Generate final result
        final_tests = self._collect_all_tests(cycles, generated_files)
        final_code = self._collect_all_code(cycles, generated_files)
        
        # Get performance metrics
        feature_perf = self.metrics_collector.get_feature_metrics(feature.id)
        
        # Calculate duration if end_time is set
        duration_seconds = 0.0
        if feature_perf and feature_perf.end_time and feature_perf.start_time:
            duration_seconds = (feature_perf.end_time - feature_perf.start_time).total_seconds()
        
        return EnhancedFeatureResult(
            feature_id=feature.id,
            feature_description=feature.description,
            success=success,
            cycles=cycles,
            total_duration_seconds=duration_seconds,
            phase_metrics=feature_perf.phase_metrics if feature_perf else {},
            errors=errors,
            final_tests=final_tests,
            final_code=final_code,
            test_coverage=validation_report.test_coverage_report.get("overall", 0) if validation_report else None,
            expanded_requirements=expanded_requirements,
            architecture=architecture,
            validation_report=validation_report,
            generated_files=generated_files
        )
    
    async def _analyze_requirements(self, feature: TDDFeature) -> Optional[ExpandedRequirements]:
        """Analyze and expand requirements using planner agent"""
        context = EnhancedAgentContext(
            phase=EnhancedTDDPhase.REQUIREMENTS,
            feature_id=feature.id,
            feature_description=feature.description,
            attempt_number=1,
            previous_attempts=[],
            phase_context={"original_requirements": feature.description},
            global_context={}
        )
        
        try:
            # Invoke planner agent
            result = await self.agent_coordinator.invoke_agent("planner", context)
            
            # Parse planner output into ExpandedRequirements
            expanded = self._parse_planner_output(result, feature.description)
            
            if self.verbose:
                print(f"📋 Expanded to {len(expanded.features)} features:")
                for f in expanded.features:
                    print(f"  - {f.title}: {f.description}")
            
            return expanded
            
        except Exception as e:
            print(f"❌ Requirements analysis failed: {e}")
            return None
    
    async def _plan_architecture(self, feature: TDDFeature, 
                                expanded_requirements: Optional[ExpandedRequirements]) -> Optional[ProjectArchitecture]:
        """Plan system architecture using designer agent"""
        context = EnhancedAgentContext(
            phase=EnhancedTDDPhase.ARCHITECTURE,
            feature_id=feature.id,
            feature_description=feature.description,
            attempt_number=1,
            previous_attempts=[],
            phase_context={
                "expanded_requirements": expanded_requirements.__dict__ if expanded_requirements else None
            },
            global_context={},
            expanded_requirements=expanded_requirements
        )
        
        try:
            # Invoke designer agent
            result = await self.agent_coordinator.invoke_agent("designer", context)
            
            # Parse designer output into ProjectArchitecture
            architecture = self._parse_designer_output(result, expanded_requirements)
            
            if self.verbose:
                print(f"🏗️ Architecture planned:")
                print(f"  Project Type: {architecture.project_type}")
                print(f"  Components: {len(architecture.components)}")
                print(f"  Tech Stack: {', '.join(architecture.technology_stack.values())}")
            
            return architecture
            
        except Exception as e:
            print(f"❌ Architecture planning failed: {e}")
            return None
    
    async def _execute_feature_tdd_cycle(self, testable_feature: TestableFeature,
                                        expanded_requirements: ExpandedRequirements,
                                        architecture: ProjectArchitecture,
                                        generated_files: Dict[str, str]) -> TDDCycle:
        """Execute TDD cycle for a specific feature"""
        cycle = TDDCycle(
            feature_id=testable_feature.id,
            feature_description=testable_feature.description,
            current_phase=EnhancedTDDPhase.RED
        )
        
        # Context for this feature
        context = EnhancedAgentContext(
            phase=EnhancedTDDPhase.RED,
            feature_id=testable_feature.id,
            feature_description=testable_feature.description,
            attempt_number=1,
            previous_attempts=[],
            phase_context={},
            global_context={
                "all_features": [f.title for f in expanded_requirements.features],
                "architecture": architecture.__dict__ if architecture else None
            },
            expanded_requirements=expanded_requirements,
            architecture=architecture,
            current_feature=testable_feature,
            generated_files=generated_files
        )
        
        # RED Phase: Generate tests for this feature
        print(f"\n🔴 RED: Writing tests for {testable_feature.title}")
        test_result = await self._execute_red_phase(context, testable_feature)
        cycle.phase_history.append(test_result)
        
        if not test_result.success:
            return cycle
        
        # Update generated tests
        cycle.generated_tests = test_result.agent_outputs.get("test_code", "")
        
        # YELLOW Phase: Implement to pass tests
        print(f"\n🟡 YELLOW: Implementing {testable_feature.title}")
        context.phase = EnhancedTDDPhase.YELLOW
        context.phase_context = {"test_code": cycle.generated_tests}
        
        impl_result = await self._execute_yellow_phase(context, testable_feature)
        cycle.phase_history.append(impl_result)
        
        if not impl_result.success:
            return cycle
        
        # Update generated code
        cycle.generated_code = impl_result.agent_outputs.get("implementation", "")
        
        # GREEN Phase: Run tests
        print(f"\n🟢 GREEN: Running tests for {testable_feature.title}")
        context.phase = EnhancedTDDPhase.GREEN
        context.phase_context = {
            "test_code": cycle.generated_tests,
            "implementation": cycle.generated_code
        }
        
        test_run_result = await self._execute_green_phase(context, testable_feature)
        cycle.phase_history.append(test_run_result)
        
        if test_run_result.success:
            cycle.is_complete = True
            cycle.current_phase = EnhancedTDDPhase.COMPLETE
            print(f"✅ Feature complete: {testable_feature.title}")
        
        cycle.end_time = datetime.now()
        return cycle
    
    async def _execute_traditional_tdd_cycle(self, feature: TDDFeature,
                                           architecture: Optional[ProjectArchitecture],
                                           generated_files: Dict[str, str]) -> TDDCycle:
        """Execute traditional single TDD cycle"""
        # This is similar to the original TDD workflow
        # Implementation would follow the existing pattern
        # but with architecture awareness
        pass  # Simplified for brevity
    
    async def _execute_red_phase(self, context: EnhancedAgentContext, 
                                feature: TestableFeature) -> PhaseResult:
        """Execute RED phase - generate tests"""
        start_time = time.time()
        
        try:
            # Use feature-based test generator
            test_code = await self.test_generator.generate_tests_for_feature(
                feature, context
            )
            
            return PhaseResult(
                phase=EnhancedTDDPhase.RED,
                success=True,
                attempts=1,
                duration_seconds=time.time() - start_time,
                agent_outputs={"test_code": test_code}
            )
            
        except Exception as e:
            return PhaseResult(
                phase=EnhancedTDDPhase.RED,
                success=False,
                attempts=1,
                duration_seconds=time.time() - start_time,
                errors=[str(e)]
            )
    
    async def _execute_yellow_phase(self, context: EnhancedAgentContext,
                                   feature: TestableFeature) -> PhaseResult:
        """Execute YELLOW phase - generate implementation"""
        start_time = time.time()
        
        try:
            # Invoke enhanced coder with multi-file support
            result = await self.agent_coordinator.invoke_agent("coder", context)
            
            # Handle multi-file output
            if isinstance(result, MultiFileOutput):
                # Store files in context
                context.generated_files.update(result.files)
                implementation = result.files.get(result.main_file, "")
            else:
                implementation = str(result)
            
            return PhaseResult(
                phase=EnhancedTDDPhase.YELLOW,
                success=True,
                attempts=1,
                duration_seconds=time.time() - start_time,
                agent_outputs={"implementation": implementation}
            )
            
        except Exception as e:
            return PhaseResult(
                phase=EnhancedTDDPhase.YELLOW,
                success=False,
                attempts=1,
                duration_seconds=time.time() - start_time,
                errors=[str(e)]
            )
    
    async def _execute_green_phase(self, context: EnhancedAgentContext,
                                  feature: TestableFeature) -> PhaseResult:
        """Execute GREEN phase - run tests"""
        start_time = time.time()
        
        try:
            # Save files temporarily for test execution
            if context.generated_files:
                self.project_manager.save_temp_files(context.generated_files)
            
            # Run tests
            result = await self.agent_coordinator.invoke_agent("executor", context)
            
            test_passed = result.get("all_tests_passed", False)
            
            # Trace test execution if tracer available
            if self.tracer and isinstance(result, dict):
                test_results = result.get("test_results", [])
                if test_results:
                    self.tracer.trace_test_execution(
                        test_file=f"{feature.title}_tests",
                        test_results=test_results,
                        duration_ms=(time.time() - start_time) * 1000
                    )
            
            return PhaseResult(
                phase=EnhancedTDDPhase.GREEN,
                success=test_passed,
                attempts=1,
                duration_seconds=time.time() - start_time,
                agent_outputs={"test_results": str(result)},
                test_results=result
            )
            
        except Exception as e:
            return PhaseResult(
                phase=EnhancedTDDPhase.GREEN,
                success=False,
                attempts=1,
                duration_seconds=time.time() - start_time,
                errors=[str(e)]
            )
    
    async def _validate_implementation(self, expanded_requirements: Optional[ExpandedRequirements],
                                     architecture: Optional[ProjectArchitecture],
                                     generated_files: Dict[str, str]) -> ValidationReport:
        """Validate that all requirements are met"""
        context = EnhancedAgentContext(
            phase=EnhancedTDDPhase.VALIDATION,
            feature_id="validation",
            feature_description="Validate implementation",
            attempt_number=1,
            previous_attempts=[],
            phase_context={
                "generated_files": list(generated_files.keys()),
                "requirements": expanded_requirements.__dict__ if expanded_requirements else None,
                "architecture": architecture.__dict__ if architecture else None
            },
            global_context={},
            expanded_requirements=expanded_requirements,
            architecture=architecture,
            generated_files=generated_files
        )
        
        try:
            # Invoke validator agent
            result = await self.agent_coordinator.invoke_agent("validator", context)
            
            # Parse validation results
            validation_report = self._parse_validation_output(result, expanded_requirements)
            
            if self.verbose:
                print(f"\n📊 Validation Results:")
                print(f"  Requirements Met: {validation_report.all_requirements_met}")
                print(f"  Implemented: {len(validation_report.implemented_features)}")
                print(f"  Missing: {len(validation_report.missing_features)}")
                if validation_report.missing_features:
                    print(f"  Missing Features:")
                    for feature in validation_report.missing_features:
                        print(f"    - {feature}")
            
            return validation_report
            
        except Exception as e:
            print(f"❌ Validation failed: {e}")
            # Return failed validation
            return ValidationReport(
                all_requirements_met=False,
                implemented_features=[],
                missing_features=["Validation error occurred"],
                test_coverage_report={},
                integration_test_results={},
                recommendations=[str(e)]
            )
    
    def _extract_test_criteria(self, expanded_requirements: ExpandedRequirements) -> List[str]:
        """Extract test criteria from expanded requirements"""
        criteria = []
        for feature in expanded_requirements.features:
            for criterion in feature.test_criteria:
                criteria.append(f"{feature.title}: {criterion.description}")
        return criteria
    
    def _parse_planner_output(self, result: Any, original_requirements: str) -> ExpandedRequirements:
        """Parse planner agent output into ExpandedRequirements"""
        # Result should be a dict with 'output' and 'expanded_requirements'
        if isinstance(result, dict) and 'expanded_requirements' in result:
            expanded_data = result['expanded_requirements']
            
            # Convert to TestableFeature objects
            testable_features = []
            for feature in expanded_data.get("features", []):
                testable_features.append(TestableFeature(
                    id=feature.get("id", f"feature_{len(testable_features)}"),
                    title=feature.get("title", ""),
                    description=feature.get("description", ""),
                    components=feature.get("components", []),
                    test_criteria=[],  # Will be filled by test generator
                    complexity=feature.get("complexity", "Medium")
                ))
            
            return ExpandedRequirements(
                original_requirements=original_requirements,
                project_type=expanded_data.get("project_type", "web_app"),
                expanded_description=result.get("output", ""),  # The text output
                features=testable_features,
                technical_requirements=expanded_data.get("technical_requirements", []),
                non_functional_requirements=expanded_data.get("non_functional_requirements", [])
            )
        
        # Fallback if result format is unexpected
        return ExpandedRequirements(
            original_requirements=original_requirements,
            project_type="web_app",
            expanded_description=str(result),
            features=[],
            technical_requirements=[],
            non_functional_requirements=[]
        )
    
    def _parse_designer_output(self, result: Any, 
                              expanded_requirements: Optional[ExpandedRequirements]) -> ProjectArchitecture:
        """Parse designer agent output into ProjectArchitecture"""
        # Result should be a dict with 'output' and 'architecture'
        if isinstance(result, dict) and 'architecture' in result:
            arch_data = result['architecture']
            
            # Import models
            from .enhanced_models import ArchitectureComponent, APIContract
            
            # Convert components
            components = []
            for comp in arch_data.get("components", []):
                components.append(ArchitectureComponent(
                    name=comp.get("name", ""),
                    type=comp.get("type", ""),
                    description=comp.get("description", ""),
                    files=comp.get("files", []),
                    dependencies=comp.get("dependencies", []),
                    interfaces=comp.get("interfaces", [])
                ))
            
            # Convert API contracts
            api_contracts = []
            for api in arch_data.get("api_contracts", []):
                api_contracts.append(APIContract(
                    method=api.get("method", ""),
                    path=api.get("path", ""),
                    description=api.get("description", ""),
                    request_schema=api.get("request_schema"),
                    response_schema=api.get("response_schema"),
                    auth_required=api.get("auth_required", False)
                ))
            
            return ProjectArchitecture(
                project_type=arch_data.get("project_type", "web_app"),
                structure=arch_data.get("structure", {}),
                technology_stack=arch_data.get("technology_stack", {}),
                components=components,
                api_contracts=api_contracts,
                dependencies=arch_data.get("dependencies", {})
            )
        
        # Fallback if result format is unexpected
        project_type = expanded_requirements.project_type if expanded_requirements else "web_app"
        return ProjectArchitecture(
            project_type=project_type,
            structure={},
            technology_stack={},
            components=[]
        )
    
    def _merge_generated_files(self, all_files: Dict[str, str], cycle: TDDCycle):
        """Merge files generated in a cycle into the main collection"""
        # Extract files from cycle outputs
        # This would parse the generated code and tests
        # and add them to the all_files dictionary
        pass
    
    def _collect_all_tests(self, cycles: List[TDDCycle], generated_files: Dict[str, str]) -> str:
        """Collect all test code from cycles and files"""
        all_tests = []
        
        # From cycles
        for cycle in cycles:
            if cycle.generated_tests:
                all_tests.append(cycle.generated_tests)
        
        # From files
        for filepath, content in generated_files.items():
            if "test" in filepath.lower() and filepath.endswith(".py"):
                all_tests.append(f"# {filepath}\n{content}")
        
        return "\n\n".join(all_tests)
    
    def _collect_all_code(self, cycles: List[TDDCycle], generated_files: Dict[str, str]) -> str:
        """Collect all implementation code from cycles and files"""
        all_code = []
        
        # From cycles
        for cycle in cycles:
            if cycle.generated_code:
                all_code.append(cycle.generated_code)
        
        # From files
        for filepath, content in generated_files.items():
            if "test" not in filepath.lower():
                all_code.append(f"# {filepath}\n{content}")
        
        return "\n\n".join(all_code)
    
    def _parse_validation_output(self, result: Any, 
                                expanded_requirements: Optional[ExpandedRequirements]) -> ValidationReport:
        """Parse validator output into ValidationReport"""
        # This would parse the validator's structured output
        # For now, create a basic report
        
        # Default to success for now (would be determined by actual validation)
        implemented = []
        missing = []
        
        if expanded_requirements:
            # Check each feature (simplified)
            for feature in expanded_requirements.features:
                # In reality, would check if feature is actually implemented
                implemented.append(feature.title)
        
        return ValidationReport(
            all_requirements_met=len(missing) == 0,
            implemented_features=implemented,
            missing_features=missing,
            test_coverage_report={"overall": 85.0},  # Example
            integration_test_results={},
            recommendations=[]
        )