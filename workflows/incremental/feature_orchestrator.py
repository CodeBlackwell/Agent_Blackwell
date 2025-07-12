"""
Feature orchestrator for managing incremental feature-based development.
Follows ACP workflow patterns.
"""
from typing import List, Dict, Any, Optional, Tuple, Union
import asyncio
import re
from dataclasses import dataclass
from datetime import datetime

from shared.utils.feature_parser import Feature, FeatureParser, ComplexityLevel
# No direct imports from incremental_executor to avoid circular imports
from workflows.monitoring import WorkflowExecutionTracer
from shared.data_models import TeamMemberResult, TeamMember
from .stagnation_detector import StagnationDetector
from .retry_strategies import RetryOrchestrator, RetryContext, RetryStrategy
from .progress_monitor import ProgressMonitor


def extract_content_from_message(message_result: Union[List, str, Dict, Any]) -> str:
    """Safely extract content from various message formats."""
    if isinstance(message_result, str):
        return message_result
    
    # Handle dictionary format (e.g., {'content': '...', 'messages': [], 'success': True})
    if isinstance(message_result, dict):
        if 'content' in message_result:
            return message_result['content']
        elif 'output' in message_result:
            return message_result['output']
        elif 'text' in message_result:
            return message_result['text']
        # If no known fields, convert to string
        return str(message_result)
    
    if isinstance(message_result, list) and len(message_result) > 0:
        first_item = message_result[0]
        # Handle Message object with parts
        if hasattr(first_item, 'parts') and len(first_item.parts) > 0:
            if hasattr(first_item.parts[0], 'content'):
                return first_item.parts[0].content
            return str(first_item.parts[0])
        # Handle Message object with direct content
        elif hasattr(first_item, 'content'):
            return first_item.content
        # Handle other message formats
        elif hasattr(first_item, 'text'):
            return first_item.text
        else:
            return str(first_item)
    
    # Fallback to string conversion
    return str(message_result)


@dataclass
class FeatureImplementationResult:
    """Result of feature implementation following ACP result patterns"""
    feature: Feature
    code_output: str
    files_created: Dict[str, str]
    validation_passed: bool
    validation_feedback: str
    retry_count: int
    execution_time: float


class FeatureOrchestrator:
    """
    Orchestrates feature-based incremental development.
    Follows ACP workflow orchestration patterns.
    """
    
    def __init__(self, tracer: WorkflowExecutionTracer):
        self.tracer = tracer
        self.parser = FeatureParser()
        self.results: List[FeatureImplementationResult] = []
    
    async def execute_incremental_development(
        self,
        designer_output: str,
        requirements: str,
        tests: Optional[str] = None,
        max_retries: int = 3
    ) -> Tuple[List[TeamMemberResult], Dict[str, str], Dict[str, Any]]:
        """
        Execute incremental feature-based development.
        
        Args:
            designer_output: Output from designer including implementation plan
            requirements: Original project requirements
            tests: Test code (for TDD workflow)
            max_retries: Maximum retries per feature
            
        Returns:
            Tuple of (team_results, final_codebase, execution_summary)
        """
        # Parse features from designer output
        features = self.parser.parse(designer_output)
        
        if not features:
            raise ValueError("No features found in designer output")
        
        # Log feature plan
        self.tracer.add_metadata("feature_count", len(features))
        self.tracer.add_metadata("feature_plan", [
            {
                "id": f.id,
                "title": f.title,
                "short_name": f.short_name,
                "complexity": f.complexity.value,
                "dependencies": f.dependencies
            }
            for f in features
        ])
        
        print(f"\n📋 Executing {len(features)} features incrementally...")
        
        # Execute features
        completed_features, final_codebase = await execute_features_incrementally(
            features=features,
            requirements=requirements,
            design=designer_output,
            tests=tests,
            tracer=self.tracer,
            max_retries=max_retries
        )
        
        # Generate execution summary
        execution_summary = self._generate_execution_summary(
            features,
            completed_features,
            final_codebase
        )
        
        # Convert to TeamMemberResult format
        team_results = self._convert_to_team_results(completed_features)
        
        return team_results, final_codebase, execution_summary
    
    def _generate_execution_summary(
        self,
        all_features: List[Feature],
        completed_features: List[Dict[str, Any]],
        final_codebase: Dict[str, str]
    ) -> Dict[str, Any]:
        """Generate summary of incremental execution"""
        
        # Calculate statistics
        total_features = len(all_features)
        completed_count = len(completed_features)
        success_rate = (completed_count / total_features * 100) if total_features > 0 else 0
        
        # Group by complexity
        complexity_stats = {
            "low": {"total": 0, "completed": 0},
            "medium": {"total": 0, "completed": 0},
            "high": {"total": 0, "completed": 0}
        }
        
        for feature in all_features:
            complexity_stats[feature.complexity.value]["total"] += 1
        
        for completed in completed_features:
            feature = completed["feature"]
            complexity_stats[feature.complexity.value]["completed"] += 1
        
        # File statistics
        total_files = len(final_codebase)
        total_lines = sum(len(content.split('\n')) for content in final_codebase.values())
        
        # Failed features
        completed_ids = {c["feature"].id for c in completed_features}
        failed_features = [f for f in all_features if f.id not in completed_ids]
        
        # Check if workflow was cancelled
        workflow_cancelled = self.tracer.report.metadata.get("workflow_cancelled", False)
        cancellation_reason = self.tracer.report.metadata.get("cancellation_reason", "")
        
        return {
            "total_features": total_features,
            "completed_features": completed_count,
            "failed_features": len(failed_features),
            "success_rate": success_rate,
            "workflow_cancelled": workflow_cancelled,
            "cancellation_reason": cancellation_reason,
            "complexity_breakdown": complexity_stats,
            "files_created": total_files,
            "total_lines": total_lines,
            "failed_feature_details": [
                {
                    "id": f.id,
                    "title": f.title,
                    "complexity": f.complexity.value,
                    "reason": "Not attempted" if f.dependencies and any(
                        dep not in completed_ids for dep in f.dependencies
                    ) else "Validation failed"
                }
                for f in failed_features
            ],
            "codebase_structure": self._generate_file_tree(final_codebase)
        }
    
    def _convert_to_team_results(
        self, 
        completed_features: List[Dict[str, Any]]
    ) -> List[TeamMemberResult]:
        """Convert feature results to TeamMemberResult format"""
        if not completed_features:
            return []
        
        # Aggregate all code outputs
        all_code_outputs = []
        all_files = {}
        
        for completed in completed_features:
            feature = completed["feature"]
            code = completed["code"]
            files = completed["files"]
            
            all_code_outputs.append(f"# {feature.title}\n{code}")
            all_files.update(files)
        
        # Create a single comprehensive result
        combined_output = "\n\n".join(all_code_outputs)
        
        # Add file listing
        file_listing = "\n\nFILES CREATED:\n"
        for filename in sorted(all_files.keys()):
            file_listing += f"  - {filename}\n"
        
        combined_output += file_listing
        
        return [TeamMemberResult(
            team_member=TeamMember.coder,
            output=combined_output,
            name="coder"
        )]
    
    def _generate_file_tree(self, codebase: Dict[str, str]) -> str:
        """Generate a tree view of the codebase structure"""
        # Sort files by path
        sorted_files = sorted(codebase.keys())
        
        tree_lines = ["Project Structure:"]
        
        # Build tree (simplified version)
        for filepath in sorted_files:
            parts = filepath.split('/')
            indent = "  " * (len(parts) - 1)
            filename = parts[-1]
            tree_lines.append(f"{indent}├── {filename}")
        
        return "\n".join(tree_lines)


# Integration helper for workflows
# Helper functions moved from incremental_executor.py to avoid circular imports

def prepare_feature_context(
    feature: Feature,
    requirements: str,
    design: str,
    existing_code: Dict[str, str],
    tests: Optional[str],
    retry_attempt: int = 0
) -> str:
    """Prepare context for coder agent following ACP message format"""
    context_parts = [
        "You are implementing a specific feature as part of a larger project.",
        "",
        "PROJECT REQUIREMENTS:",
        requirements,
        "",
        f"FEATURE TO IMPLEMENT: {feature.title}",
        f"Description: {feature.description}",
        f"Files to create/modify: {', '.join(feature.files)}",
        f"Success criteria: {feature.validation_criteria}",
        "",
        "IMPORTANT: If this feature requires any Python packages (like Flask, requests, etc.), you MUST also create a requirements.txt file listing all dependencies.",
        ""
    ]
    
    # Add existing code context
    if existing_code:
        context_parts.extend([
            "EXISTING CODEBASE:",
            "The following files already exist and have been validated:"
        ])
        
        for filename in sorted(existing_code.keys()):
            context_parts.append(f"  - {filename}")
        
        # Include relevant existing code based on dependencies
        if feature.dependencies:
            context_parts.extend(["", "Relevant existing code:"])
            for dep_feature_id in feature.dependencies:
                # Include interface/signatures from dependent features
                # This is simplified - real implementation would be smarter
                for filename, content in existing_code.items():
                    if any(dep_file in filename for dep_file in ['__init__.py', 'base.py']):
                        context_parts.extend([
                            "",
                            f"--- {filename} ---",
                            content[:500] + "..." if len(content) > 500 else content
                        ])
    
    # Add retry context if applicable
    if retry_attempt > 0:
        context_parts.extend([
            "",
            f"RETRY ATTEMPT {retry_attempt}:",
            "The previous attempt failed validation. Focus on fixing the specific issues.",
            "Previous error: [error details would be passed here]"
        ])
    
    # Add instructions
    context_parts.extend([
        "",
        "IMPORTANT INSTRUCTIONS:",
        "1. Implement ONLY this specific feature",
        "2. Create/modify ONLY the files listed above",
        "3. Ensure the validation criteria will pass",
        "4. Build upon the existing codebase",
        "5. Follow the design patterns established in existing code",
        ""
    ])
    
    # Add relevant tests for TDD
    if tests and feature.files:
        relevant_tests = extract_relevant_tests_for_feature(tests, feature)
        if relevant_tests:
            context_parts.extend([
                "TESTS TO PASS:",
                relevant_tests,
                ""
            ])
    
    return "\n".join(context_parts)


def parse_code_files(code_output: str) -> Dict[str, str]:
    """Extract individual files from coder output"""
    files = {}
    
    # Pattern: FILENAME: path/to/file.py followed by code block
    file_pattern = r'FILENAME:\s*([^\n]+)\n```(?:\w+)?\n(.*?)```'
    
    matches = re.finditer(file_pattern, code_output, re.DOTALL)
    
    for match in matches:
        filename = match.group(1).strip()
        content = match.group(2).strip()
        files[filename] = content
    
    # Fallback: look for standard file markers if FILENAME not used
    if not files:
        # Try to parse markdown code blocks with file comments
        alt_pattern = r'#\s*([^\n]+\.py)\n```python\n(.*?)```'
        matches = re.finditer(alt_pattern, code_output, re.DOTALL)
        
        for match in matches:
            filename = match.group(1).strip()
            content = match.group(2).strip()
            files[filename] = content
    
    return files


def extract_relevant_tests_for_feature(all_tests: str, feature: Feature) -> Optional[str]:
    """Extract tests specifically relevant to a feature"""
    # This is a simplified implementation
    # Real version would use AST parsing for accuracy
    
    relevant_sections = []
    
    for file in feature.files:
        # Create test patterns from file names
        base_name = file.split('/')[-1].replace('.py', '')
        test_patterns = [
            f"test_{base_name}",
            f"Test{base_name.title()}",
            f"test.*{base_name}"
        ]
        
        for pattern in test_patterns:
            regex = re.compile(pattern, re.IGNORECASE)
            if regex.search(all_tests):
                # Extract the test section
                # This is simplified - would need proper parsing
                relevant_sections.append(f"# Tests for {file}")
    
    return "\n".join(relevant_sections) if relevant_sections else None
async def execute_features_incrementally(
    features: List[Feature],
    requirements: str,
    design: str,
    tests: Optional[str],
    tracer: WorkflowExecutionTracer,
    max_retries: int = 3,
    stagnation_threshold: float = 0.7
) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
    """
    Execute features incrementally with retry logic and stagnation detection.
    Follows ACP patterns for orchestrated execution.
    """
    try:
        from orchestrator.orchestrator_agent import run_team_member_with_tracking
    except ImportError as e:
        # Fallback for testing or alternate configurations
        raise ImportError(f"Failed to import run_team_member_with_tracking: {e}")
    
    # Dynamic import to avoid circular dependency
    try:
        from orchestrator.utils.incremental_executor import IncrementalExecutor
    except ImportError as e:
        raise ImportError(f"Failed to import IncrementalExecutor: {e}")
    
    executor = IncrementalExecutor(
        session_id=f"inc_{tracer.execution_id}",
        tracer=tracer
    )
    
    # Initialize stagnation detector
    stagnation_detector = StagnationDetector(
        stagnation_threshold=stagnation_threshold,
        min_attempts_before_detection=3
    )
    
    # Initialize retry orchestrator
    retry_orchestrator = RetryOrchestrator()
    
    # Initialize progress monitor
    progress_monitor = ProgressMonitor(
        workflow_id=tracer.execution_id,
        total_features=len(features)
    )
    
    completed_features = []
    skipped_features = []
    
    # Print initial progress visualization
    print(progress_monitor.visualize_progress())
    
    for idx, feature in enumerate(features):
        print(f"\n🔨 Implementing {feature.id}: {feature.short_name}")
        
        # Start progress tracking for this feature
        progress_monitor.start_feature(feature.id, feature.short_name)
        
        # Start feature step
        step_id = tracer.start_step(
            f"feature_{feature.id}",
            "coder",
            {
                "feature_id": feature.id,
                "feature_name": feature.short_name,
                "feature_title": feature.title,
                "files": feature.files,
                "complexity": feature.complexity.value
            }
        )
        
        success = False
        retry_count = 0
        
        # Check if we should skip this feature due to previous stagnation
        if stagnation_detector.should_skip_feature(feature.id):
            print(f"⏭️  Skipping {feature.id} due to previous stagnation")
            skipped_features.append(feature)
            progress_monitor.skip_feature(feature.id, "Previous stagnation detected")
            tracer.complete_step(step_id, {
                "status": "skipped",
                "reason": "stagnation_detected"
            })
            continue
        
        while not success and retry_count < max_retries:
            attempt_start_time = datetime.now()
            
            # Check for stagnation before retry
            if retry_count > 0:
                stagnation_info = stagnation_detector.detect_stagnation(feature.id)
                if stagnation_info and 'recommendation' in stagnation_info:
                    print(f"\n⚠️  Stagnation detected: {stagnation_info['recommendation']}")
                    
                    # Get alternative approach suggestion
                    alternative = stagnation_detector.suggest_alternative_approach(feature.id)
                    if alternative:
                        print(f"💡 Suggestion: {alternative}")
            
            # Prepare context for coder with stagnation awareness
            coder_input = prepare_feature_context(
                feature,
                requirements,
                design,
                executor.codebase_state,
                tests,
                retry_count
            )
            
            # Add stagnation context if available
            if retry_count > 0:
                summary = stagnation_detector.get_feature_summary(feature.id)
                if summary and summary['most_recent_errors']:
                    coder_input += "\n\nPREVIOUS ERRORS TO AVOID:\n"
                    for error in summary['most_recent_errors']:
                        coder_input += f"- {error['type']}: {error['message']}\n"
                
                # Apply retry strategy modifications if available
                if 'retry_decision' in locals() and retry_decision.modifications:
                    coder_input = retry_decision.get_modified_context(coder_input)
            
            # Get code from coder agent
            code_result = await run_team_member_with_tracking("coder_agent", coder_input, "incremental_coding")
            
            # Extract content using helper function
            code_output = extract_content_from_message(code_result)
            
            # Parse files from output
            new_files = parse_code_files(code_output)
            
            # Calculate code change size for stagnation detection
            code_diff_size = sum(len(content.split('\n')) for content in new_files.values())
            
            # Validate with executor
            validation_result = await executor.validate_feature(
                feature,
                new_files,
                tests
            )
            
            # Record attempt for stagnation detection
            attempt_duration = (datetime.now() - attempt_start_time).total_seconds()
            test_results = None
            if validation_result.tests_passed is not None or validation_result.tests_failed is not None:
                test_results = (
                    validation_result.tests_passed or 0,
                    validation_result.tests_failed or 0
                )
            
            stagnation_detector.record_attempt(
                feature_id=feature.id,
                success=validation_result.success,
                error_message=validation_result.feedback if not validation_result.success else None,
                files_changed=list(new_files.keys()),
                code_diff_size=code_diff_size,
                test_results=test_results,
                duration=attempt_duration
            )
            
            if validation_result.success:
                success = True
                completed_features.append({
                    "feature": feature,
                    "code": code_output,
                    "files": new_files,
                    "validation": validation_result
                })
                
                # Update progress monitor
                progress_monitor.complete_feature(
                    feature.id,
                    success=True,
                    files_created=list(new_files.keys()),
                    lines_of_code=code_diff_size
                )
                
                # Complete step
                tracer.complete_step(step_id, {
                    "status": "success",
                    "files_created": list(new_files.keys()),
                    "validation_passed": True
                })
                
                # Show progress visualization
                print(f"✅ {feature.id} complete")
                print(progress_monitor.visualize_progress())
                
            else:
                retry_count += 1
                if retry_count < max_retries:
                    # Create retry context for decision
                    # Get error history from stagnation detector
                    error_history = []
                    if hasattr(stagnation_detector, 'feature_metrics') and feature.id in stagnation_detector.feature_metrics:
                        metrics = stagnation_detector.feature_metrics[feature.id]
                        if hasattr(metrics, 'failed_validations') and metrics.failed_validations:
                            error_history = [v.get('error', 'Unknown error') for v in metrics.failed_validations if isinstance(v, dict)]
                    error_categories = []
                    for err in error_history:
                        if "syntax" in err.lower():
                            error_categories.append("syntax_error")
                        elif "import" in err.lower():
                            error_categories.append("import_error")
                        elif "test" in err.lower():
                            error_categories.append("test_failure")
                        else:
                            error_categories.append("unknown")
                    
                    retry_context = RetryContext(
                        feature_id=feature.id,
                        attempt_number=retry_count,
                        total_attempts=max_retries,
                        error_history=error_history[-5:],  # Last 5 errors
                        error_categories=error_categories[-5:],
                        time_spent=attempt_duration,
                        code_changes_size=[code_diff_size],
                        test_progress=[test_results] if test_results else [],
                        complexity_level=feature.complexity.value,
                        dependencies=feature.dependencies
                    )
                    
                    # Get retry decision
                    retry_decision = retry_orchestrator.decide_retry(retry_context)
                    
                    if retry_decision.should_retry:
                        print(f"❌ Validation failed, retrying ({retry_count}/{max_retries})")
                        print(f"   Strategy: {retry_decision.strategy.value} - {retry_decision.reason}")
                        
                        # Update progress monitor with retry
                        progress_monitor.record_retry(
                            feature.id,
                            retry_decision.strategy.value,
                            validation_result.feedback
                        )
                        
                        # Apply delay if needed
                        if retry_decision.delay_seconds > 0:
                            import asyncio
                            print(f"   Waiting {retry_decision.delay_seconds:.1f}s before retry...")
                            await asyncio.sleep(retry_decision.delay_seconds)
                        
                        tracer.record_retry(
                            attempt_number=retry_count,
                            reason=validation_result.feedback,
                            metadata={"strategy": retry_decision.strategy.value}
                        )
                    else:
                        # Decision is not to retry
                        break
        
        if not success:
            # Check if we should skip based on stagnation
            if stagnation_detector.should_skip_feature(feature.id):
                print(f"⚠️  {feature.id} is stagnating after {retry_count} attempts - skipping")
                skipped_features.append(feature)
                progress_monitor.mark_stagnant(feature.id)
                progress_monitor.skip_feature(feature.id, "Stagnation after retries")
                tracer.complete_step(step_id, {
                    "status": "skipped",
                    "reason": "stagnation_after_retries",
                    "attempts": retry_count
                })
            else:
                # Feature failed after all retries
                progress_monitor.complete_feature(
                    feature.id,
                    success=False,
                    files_created=[],
                    lines_of_code=0
                )
                tracer.complete_step(step_id, {
                    "status": "failed",
                    "error": validation_result.feedback,
                    "attempts": retry_count
                })
                
                print(f"⚠️  {feature.id} failed after {retry_count} attempts")
                
                # Cancel workflow if Project Foundation fails
                if feature.id == "FEATURE[1]" or feature.title.lower() == "project foundation":
                    print("\n" + "="*60)
                    print("❌ WORKFLOW CANCELLED: Project Foundation validation failed")
                    print("="*60)
                    print("The Project Foundation is critical for all subsequent features.")
                    print("Please fix the foundation issues before continuing.")
                    print("\nCommon issues:")
                    print("- Missing or incorrect requirements.txt")
                    print("- Application not starting properly")
                    print("- Import errors or syntax errors in main files")
                    print("- Configuration issues")
                    
                    # Add cancellation metadata
                    tracer.add_metadata("workflow_cancelled", True)
                    tracer.add_metadata("cancellation_reason", "Project Foundation validation failed")
                    tracer.add_metadata("failed_feature", {
                        "id": feature.id,
                        "title": feature.title,
                        "validation_feedback": validation_result.feedback
                    })
                    
                    # Mark all remaining features as skipped
                    for remaining_feature in features[idx+1:]:
                        progress_monitor.skip_feature(
                            remaining_feature.id, 
                            "Workflow cancelled due to foundation failure"
                        )
                    
                    break
                
                # Decide whether to continue based on complexity
                if hasattr(feature, 'complexity') and feature.complexity == ComplexityLevel.HIGH:
                    print("❌ Stopping due to high-complexity feature failure")
                    break
    
    # Add summary of skipped features
    if skipped_features:
        print(f"\n📊 Skipped {len(skipped_features)} features due to stagnation")
        for feature in skipped_features:
            summary = stagnation_detector.get_feature_summary(feature.id)
            if summary:
                print(f"  - {feature.id}: {summary['total_attempts']} attempts, "
                      f"stagnation score: {summary['stagnation_score']:.2f}")
    
    # Print final progress visualization
    print("\n" + "="*60)
    print("FINAL PROGRESS REPORT")
    print(progress_monitor.visualize_progress())
    
    # Export progress data to tracer metadata
    tracer.add_metadata("progress_report", progress_monitor.get_progress_summary())
    tracer.add_metadata("retry_strategies", retry_orchestrator.get_strategy_report())
    
    return completed_features, executor.codebase_state


async def run_incremental_coding_phase(
    designer_output: str,
    requirements: str,
    tests: Optional[str],
    tracer: WorkflowExecutionTracer,
    max_retries: int = 3
) -> Tuple[str, Dict[str, Any]]:
    """
    Helper function for workflow integration.
    
    Returns:
        Tuple of (aggregated_code_output, execution_metrics)
    """
    orchestrator = FeatureOrchestrator(tracer)
    
    team_results, final_codebase, execution_summary = await orchestrator.execute_incremental_development(
        designer_output=designer_output,
        requirements=requirements,
        tests=tests,
        max_retries=max_retries
    )
    
    # Return aggregated output and metrics
    if team_results:
        return team_results[0].output, execution_summary
    else:
        return "", execution_summary
