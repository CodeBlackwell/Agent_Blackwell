"""
MVP Incremental Workflow with Test-Driven Development (TDD)
Enhanced version that writes tests before implementation for each feature
"""
import re
from typing import List, Dict, Optional
from pathlib import Path
from shared.data_models import CodingTeamInput, TeamMemberResult, TeamMember
from workflows.monitoring import WorkflowExecutionTracer
from workflows.mvp_incremental.retry_strategy import RetryStrategy, RetryConfig
from workflows.mvp_incremental.progress_monitor import ProgressMonitor, StepStatus
from workflows.mvp_incremental.review_integration import ReviewIntegration, ReviewPhase, ReviewRequest
from workflows.mvp_incremental.tdd_feature_implementer import TDDFeatureImplementer, create_tdd_implementer
from workflows.mvp_incremental.test_accumulator import TestAccumulator
from workflows.mvp_incremental.integration_verification import perform_integration_verification
from workflows.mvp_incremental.tdd_phase_tracker import TDDPhaseTracker
from workflows.logger import workflow_logger as logger


def parse_simple_features(design_output: str) -> List[Dict[str, str]]:
    """
    Simple feature parsing - just extract numbered items or bullet points.
    Returns list of feature dictionaries with title and description.
    """
    features = []
    
    # Look for numbered features (1. 2. etc) or bullet points
    pattern = r'(?:^|\n)\s*(?:\d+\.|-|\*|•)\s+([^\n]+(?:\n(?!\s*(?:\d+\.|-|\*|•))[^\n]+)*)'
    matches = re.findall(pattern, design_output, re.MULTILINE)
    
    if not matches:
        # Fallback: look for features in sections
        if "features" in design_output.lower() or "requirements" in design_output.lower():
            lines = design_output.split('\n')
            for line in lines:
                line = line.strip()
                if line and len(line) > 10 and len(line) < 200:
                    if any(keyword in line.lower() for keyword in ['add', 'create', 'implement', 'support', 'handle', 'method', 'function', 'class']):
                        features.append({
                            "id": f"feature_{len(features) + 1}",
                            "title": line[:100],
                            "description": line
                        })
        
        # If still no features, create one big feature
        if not features:
            features.append({
                "id": "feature_1",
                "title": "Complete Implementation",
                "description": design_output[:500] + "..."
            })
    else:
        for i, match in enumerate(matches, 1):
            title = match.strip().split('\n')[0][:100]
            features.append({
                "id": f"feature_{i}",
                "title": title,
                "description": match.strip()
            })
    
    return features


async def execute_mvp_incremental_tdd_workflow(
    input_data: CodingTeamInput,
    tracer: WorkflowExecutionTracer = None
) -> List[TeamMemberResult]:
    """
    Execute MVP incremental workflow with TDD approach.
    Planning → Design → For each feature: (Write Tests → Run Tests → Implement → Validate)
    """
    from orchestrator.orchestrator_agent import run_team_member_with_tracking
    from agents.feature_reviewer.feature_reviewer_agent import feature_reviewer_agent
    
    if not tracer:
        tracer = WorkflowExecutionTracer("mvp_incremental_tdd")
    
    # Initialize components
    progress_monitor = ProgressMonitor()
    review_integration = ReviewIntegration(feature_reviewer_agent)
    test_accumulator = TestAccumulator()
    phase_tracker = TDDPhaseTracker()  # Create phase tracker for RED-YELLOW-GREEN tracking
    
    results = []
    validator_session_id = None
    
    # Check if TDD mode is enabled through workflow config or metadata
    # Default to True for TDD workflow
    use_tdd = True
    if hasattr(input_data, 'metadata') and input_data.metadata:
        use_tdd = input_data.metadata.get('use_tdd', True)
    
    logger.info(f"Starting MVP Incremental Workflow with TDD: {use_tdd}")
    
    # Step 0: Expand vague requirements if needed
    from workflows.mvp_incremental.requirements_expander import RequirementsExpander
    
    expanded_requirements, was_expanded = RequirementsExpander.expand_requirements(input_data.requirements)
    
    if was_expanded:
        print("\n📝 Requirements expanded for clarity")
        print(f"Original: {input_data.requirements[:100]}...")
        print(f"Key areas identified: {', '.join(RequirementsExpander.extract_key_requirements(expanded_requirements))}")
    
    # Use expanded requirements for planning
    requirements_for_planning = expanded_requirements
    
    # Step 1: Planning
    progress_monitor.start_phase("Planning")
    progress_monitor.start_step("planning", "planning")
    
    planning_step_id = tracer.start_step("planning", "planner_agent", {
        "requirements": requirements_for_planning
    })
    
    planning_result = await run_team_member_with_tracking(
        "planner_agent",
        requirements_for_planning,
        "mvp_incremental_tdd_planning"
    )
    
    # Extract content from response
    if isinstance(planning_result, list) and len(planning_result) > 0:
        planning_output = planning_result[0].parts[0].content
    else:
        planning_output = str(planning_result)
    
    planner_result = TeamMemberResult(
        team_member=TeamMember.planner,
        output=planning_output,
        name="planner"
    )
    results.append(planner_result)
    
    tracer.complete_step(planning_step_id, {
        "output_length": len(planner_result.output),
        "status": "completed"
    })
    
    progress_monitor.complete_step("planning", success=True)
    
    # Review the plan
    planning_review = await review_integration.request_review(ReviewRequest(
        phase=ReviewPhase.PLANNING,
        content=planning_output,
        context={"requirements": input_data.requirements}
    ))
    
    if not planning_review.approved:
        print(f"\n🔍 Plan Review: NEEDS REVISION")
        print(f"   Feedback: {planning_review.feedback}")
    else:
        print(f"\n✅ Plan Review: APPROVED")
    
    # Step 2: Design
    progress_monitor.start_phase("Design")
    progress_monitor.start_step("design", "design")
    
    design_step_id = tracer.start_step("design", "designer_agent", {
        "plan": planner_result.output
    })
    
    design_result = await run_team_member_with_tracking(
        "designer_agent",
        f"Based on this plan, create a detailed technical design with clear features:\n\n{planner_result.output}",
        "mvp_incremental_tdd_design"
    )
    
    # Extract content from response
    if isinstance(design_result, list) and len(design_result) > 0:
        design_output = design_result[0].parts[0].content
    else:
        design_output = str(design_result)
    
    designer_result = TeamMemberResult(
        team_member=TeamMember.designer,
        output=design_output,
        name="designer"
    )
    results.append(designer_result)
    
    tracer.complete_step(design_step_id, {
        "output_length": len(designer_result.output),
        "status": "completed"
    })
    
    progress_monitor.complete_step("design", success=True)
    
    # Review the design
    design_review = await review_integration.request_review(ReviewRequest(
        phase=ReviewPhase.DESIGN,
        content=design_output,
        context={"requirements": input_data.requirements, "plan": planning_output}
    ))
    
    if not design_review.approved:
        print(f"\n🔍 Design Review: NEEDS REVISION")
        print(f"   Feedback: {design_review.feedback}")
    else:
        print(f"\n✅ Design Review: APPROVED")
    
    # Step 3: Parse features from design with testable criteria
    print("\n🔍 Parsing features with testable criteria...")
    from workflows.mvp_incremental.intelligent_feature_extractor import IntelligentFeatureExtractor
    
    # Use intelligent extraction for better feature parsing
    features = IntelligentFeatureExtractor.extract_features(
        plan=planning_output,
        design=design_output,
        requirements=input_data.requirements
    )
    print(f"Found {len(features)} features to implement with test criteria")
    
    # Order features by dependencies
    print("\n🔗 Analyzing feature dependencies...")
    from workflows.mvp_incremental.feature_dependency_parser import FeatureDependencyParser
    features = FeatureDependencyParser.order_features_smart(features, design_output)
    print("📊 Features ordered by dependencies")
    
    # Start the workflow with total feature count
    progress_monitor.start_workflow(total_features=len(features))
    
    # Step 4: Implement features using TDD
    progress_monitor.start_phase("TDD Implementation")
    accumulated_code = {}  # Track all code files created
    
    if use_tdd:
        # Create TDD implementer with phase tracker
        tdd_implementer = create_tdd_implementer(tracer, progress_monitor, review_integration, phase_tracker)
        
        # Implement each feature using TDD
        for i, feature in enumerate(features):
            print(f"\n{'='*60}")
            print(f"🎯 Feature {i+1}/{len(features)}: {feature['title']}")
            print(f"{'='*60}")
            
            # Get feature dependencies for test organization
            feature_dependencies = [f['id'] for f in features[:i]]
            
            # Implement feature using TDD
            tdd_result = await tdd_implementer.implement_feature_tdd(
                feature=feature,
                existing_code=accumulated_code,
                requirements=input_data.requirements,
                design_output=design_output,
                feature_index=i
            )
            
            # Add test code to accumulator
            test_files = test_accumulator.add_feature_tests(
                feature_id=feature['id'],
                test_code=tdd_result.test_code,
                feature_dependencies=feature_dependencies
            )
            
            # Update progress monitor with TDD metrics
            progress_monitor.update_tdd_progress(
                feature['id'],
                "tests_written",
                {
                    "test_files": len(test_files),
                    "test_functions": sum(len(tf.test_functions) for tf in test_files)
                }
            )
            
            if tdd_result.initial_test_result:
                progress_monitor.update_tdd_progress(
                    feature['id'],
                    "tests_initial_run",
                    {
                        "passed": tdd_result.initial_test_result.passed,
                        "failed": tdd_result.initial_test_result.failed
                    }
                )
            
            if tdd_result.success and tdd_result.final_test_result:
                progress_monitor.update_tdd_progress(
                    feature['id'],
                    "tests_passing",
                    {
                        "coverage": None  # Would be calculated by coverage tool
                    }
                )
            
            # Update accumulated code
            new_files = _parse_code_files(tdd_result.implementation_code)
            accumulated_code.update(new_files)
            
            # Create result for this feature
            feature_result = TeamMemberResult(
                team_member=TeamMember.coder,
                output=tdd_result.implementation_code,
                name=f"coder_feature_{i+1}",
                metadata={
                    "tdd": True,
                    "tests_written": True,
                    "tests_passing": tdd_result.success,
                    "retry_count": tdd_result.retry_count,
                    "test_files": len(test_files)
                }
            )
            results.append(feature_result)
            
            # Also add test writer result
            test_result = TeamMemberResult(
                team_member=TeamMember.test_writer,
                output=tdd_result.test_code,
                name=f"test_writer_feature_{i+1}",
                metadata={
                    "feature_id": feature['id'],
                    "test_count": sum(len(tf.test_functions) for tf in test_files)
                }
            )
            results.append(test_result)
            
    else:
        # Fall back to standard implementation if TDD is disabled
        print("\n⚠️  TDD disabled, using standard implementation approach")
        # Implementation code would go here (copy from original mvp_incremental.py)
    
    # Create final consolidated result
    print("\n📦 Consolidating final implementation...")
    
    # Generate test runner script
    test_runner_script = test_accumulator.generate_test_runner_script()
    accumulated_code['test_runner.py'] = test_runner_script
    
    # Generate test report
    test_report = test_accumulator.generate_test_report()
    accumulated_code['TEST_REPORT.md'] = test_report
    
    # Combine all test files
    combined_tests = test_accumulator.get_combined_test_suite("all")
    accumulated_code['tests/all_tests.py'] = combined_tests
    
    final_code = _consolidate_code(accumulated_code)
    
    # Count validation results
    tdd_features = [r for r in results if hasattr(r, 'metadata') and r.metadata and r.metadata.get('tdd', False)]
    passed_features = sum(1 for r in tdd_features if r.metadata.get('tests_passing', False))
    failed_features = len(tdd_features) - passed_features
    
    final_result = TeamMemberResult(
        team_member=TeamMember.coder,
        output=final_code,
        name="final_implementation",
        metadata={
            "tdd_enabled": use_tdd,
            "total_test_files": test_accumulator.test_suite.unit_tests.__len__() + 
                               test_accumulator.test_suite.integration_tests.__len__(),
            "test_command": test_accumulator.get_test_command()
        }
    )
    results.append(final_result)
    
    # End workflow and show summary
    progress_monitor.end_workflow()
    
    # Show TDD phase tracker summary
    print("\n" + "="*60)
    print(phase_tracker.get_summary_report())
    print("="*60)
    
    # Export metrics
    metrics = progress_monitor.export_metrics()
    
    # Final review
    final_review = await review_integration.request_review(ReviewRequest(
        phase=ReviewPhase.FINAL_IMPLEMENTATION,
        content=final_code,
        context={
            "requirements": input_data.requirements,
            "feature_summary": {
                "total": len(features),
                "successful": passed_features,
                "failed": failed_features
            },
            "tdd_metrics": metrics.get("tdd_metrics", {})
        }
    ))
    
    print(f"\n📋 Final Implementation Review:")
    print(f"   Status: {'APPROVED' if final_review.approved else 'NEEDS REVISION'}")
    print(f"   Feedback: {final_review.feedback[:200]}...")
    
    # Integration verification if enabled
    if hasattr(input_data, 'run_integration_verification') and input_data.run_integration_verification:
        print("\n🔍 Starting Integration Verification...")
        # Integration verification code would go here
    
    # Cleanup validator container if used
    if validator_session_id:
        print(f"\n🧹 Cleaning up validator session: {validator_session_id}")
        try:
            from agents.validator.container_manager import get_container_manager
            container_manager = get_container_manager()
            container_manager.cleanup_container(validator_session_id)
        except Exception as e:
            print(f"   ⚠️  Cleanup error: {e}")
    
    print("=" * 60)
    
    return results


def _parse_code_files(code_output: str) -> Dict[str, str]:
    """Extract files from coder output."""
    files = {}
    
    # Look for our standard format
    file_pattern = r'```(?:python|py|javascript|js)\s*\n#\s*filename:\s*(\S+)\n(.*?)```'
    matches = re.findall(file_pattern, code_output, re.DOTALL)
    
    if matches:
        for filename, content in matches:
            files[filename] = content.strip()
    
    return files


def _consolidate_code(code_dict: Dict[str, str]) -> str:
    """Consolidate all code files into final output."""
    if not code_dict:
        return "# No code generated"
    
    output_parts = ["# Final Implementation with TDD\n"]
    
    # Separate test files from implementation files
    test_files = {k: v for k, v in code_dict.items() if 'test' in k.lower()}
    impl_files = {k: v for k, v in code_dict.items() if 'test' not in k.lower()}
    
    # Implementation files first
    if impl_files:
        output_parts.append("\n## Implementation Files\n")
        for filename in sorted(impl_files.keys()):
            output_parts.append(f"\n### File: {filename}")
            output_parts.append("```python")
            output_parts.append(impl_files[filename])
            output_parts.append("```")
    
    # Then test files
    if test_files:
        output_parts.append("\n## Test Files\n")
        for filename in sorted(test_files.keys()):
            output_parts.append(f"\n### File: {filename}")
            output_parts.append("```python")
            output_parts.append(test_files[filename])
            output_parts.append("```")
    
    return "\n".join(output_parts)