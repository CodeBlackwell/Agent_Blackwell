"""
MVP Incremental Workflow - TDD Only Mode
Mandatory Test-Driven Development with RED→YELLOW→GREEN phases for every feature.
No configuration options - TDD is the only way this workflow operates.
"""
import re
from typing import List, Dict, Optional
from pathlib import Path
from shared.data_models import CodingTeamInput, TeamMemberResult, TeamMember
from workflows.monitoring import WorkflowExecutionTracer
from workflows.mvp_incremental.retry_strategy import RetryStrategy, RetryConfig
from workflows.mvp_incremental.progress_monitor import ProgressMonitor, StepStatus
from workflows.mvp_incremental.review_integration import ReviewIntegration, ReviewPhase, ReviewRequest, ReviewResult
from workflows.mvp_incremental.test_execution import TestExecutionConfig, execute_and_fix_tests
from workflows.mvp_incremental.integration_verification import perform_integration_verification
from workflows.mvp_incremental.tdd_phase_tracker import TDDPhaseTracker, TDDPhase
from workflows.mvp_incremental.testable_feature_parser import TestableFeatureParser, TestableFeature
from workflows.mvp_incremental.tdd_feature_implementer import TDDFeatureImplementer, TDDFeatureResult




def parse_testable_features(design_output: str, requirements: str) -> List[TestableFeature]:
    """
    Parse design output into TestableFeature objects for TDD workflow.
    Each feature will go through mandatory RED→YELLOW→GREEN phases.
    """
    parser = TestableFeatureParser()
    
    # Parse features using the testable feature parser
    features = parser.parse_features_with_criteria(design_output)
    
    # If no features found, create a single feature for the entire implementation
    if not features:
        features = [TestableFeature(
            id="feature_1",
            title="Complete Implementation",
            description=design_output[:500] + "...",
            test_criteria={
                "description": "Implement all requirements",
                "input_examples": ["As per requirements"],
                "expected_outputs": ["Working implementation"],
                "edge_cases": ["Handle all edge cases"],
                "error_conditions": ["Proper error handling"]
            }
        )]
    
    return features


async def execute_mvp_incremental_workflow(
    input_data: CodingTeamInput,
    tracer: WorkflowExecutionTracer = None
) -> List[TeamMemberResult]:
    """
    Execute MVP incremental workflow with MANDATORY Test-Driven Development.
    Planning → Design → For each feature: RED→YELLOW→GREEN cycle
    
    This workflow enforces TDD - there is no option to disable it.
    Every feature MUST go through:
    1. RED phase: Write tests that fail
    2. YELLOW phase: Make tests pass, await review
    3. GREEN phase: Code approved and complete
    """
    from orchestrator.orchestrator_agent import run_team_member_with_tracking
    from agents.feature_reviewer.feature_reviewer_agent import feature_reviewer_agent
    
    if not tracer:
        tracer = WorkflowExecutionTracer("mvp_incremental_tdd")
    
    # Initialize TDD components
    progress_monitor = ProgressMonitor()
    review_integration = ReviewIntegration(feature_reviewer_agent)
    phase_tracker = TDDPhaseTracker()
    retry_strategy = RetryStrategy()
    retry_config = RetryConfig()
    
    # Create TDD feature implementer
    tdd_implementer = TDDFeatureImplementer(
        tracer=tracer,
        progress_monitor=progress_monitor,
        review_integration=review_integration,
        retry_strategy=retry_strategy,
        retry_config=retry_config,
        phase_tracker=phase_tracker
    )
    
    results = []
    validator_session_id = None  # Track validator session
    
    # Step 1: Planning
    progress_monitor.start_phase("Planning")
    progress_monitor.start_step("planning", "planning")
    
    planning_step_id = tracer.start_step("planning", "planner_agent", {
        "requirements": input_data.requirements
    })
    
    planning_result = await run_team_member_with_tracking(
        "planner_agent",
        input_data.requirements,
        "mvp_incremental_planning"
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
    
    # Phase 8: Review the plan
    planning_review_request = ReviewRequest(
        phase=ReviewPhase.PLANNING,
        content=planning_output,
        context={"requirements": input_data.requirements}
    )
    
    planning_review = await review_integration.request_review(planning_review_request)
    
    if not planning_review.approved:
        print(f"\n🔍 Plan Review: NEEDS REVISION")
        print(f"   Feedback: {planning_review.feedback}")
        # For now, we'll proceed anyway but log the review
        # In a full implementation, we might retry planning
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
        "mvp_incremental_design"
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
    
    # Phase 8: Review the design
    design_review_request = ReviewRequest(
        phase=ReviewPhase.DESIGN,
        content=design_output,
        context={"requirements": input_data.requirements, "plan": planning_output}
    )
    
    design_review = await review_integration.request_review(design_review_request)
    
    if not design_review.approved:
        print(f"\n🔍 Design Review: NEEDS REVISION")
        print(f"   Feedback: {design_review.feedback}")
        # For now, we'll proceed anyway but log the review
    else:
        print(f"\n✅ Design Review: APPROVED")
    
    # Step 3: Parse features for TDD implementation
    print("\n🔍 Parsing testable features from design...")
    features = parse_testable_features(design_output, input_data.requirements)
    print(f"Found {len(features)} features for TDD implementation")
    
    # Order features by dependencies
    print("\n🔗 Analyzing feature dependencies...")
    from workflows.mvp_incremental.feature_dependency_parser import FeatureDependencyParser
    # Convert to dict format for dependency parser, then back to TestableFeature
    feature_dicts = [{"id": f.id, "title": f.title, "description": f.description} for f in features]
    ordered_dicts = FeatureDependencyParser.order_features_smart(feature_dicts, design_output)
    
    # Map back to TestableFeature objects maintaining order
    feature_map = {f.id: f for f in features}
    features = [feature_map[d["id"]] for d in ordered_dicts]
    print("📊 Features ordered by dependencies")
    
    # Start the workflow with total feature count
    progress_monitor.start_workflow(total_features=len(features))
    
    # Step 4: Implement features using mandatory TDD cycle
    print("\n🚀 Starting TDD implementation cycle...")
    print("   Each feature will go through: RED → YELLOW → GREEN phases")
    progress_monitor.start_phase("TDD Implementation")
    
    accumulated_code = {}  # Track all code files created
    accumulated_test_code = {}  # Track all test files created
    tdd_results = []  # Track TDD results for each feature
    
    for i, feature in enumerate(features):
        # Display TDD phase tracker status
        print(f"\n{'='*60}")
        print(f"Feature {i+1}/{len(features)}: {feature.title}")
        print(f"{'='*60}")
        
        # Start tracking feature progress
        progress_monitor.start_feature(feature.id, feature.title, i+1)
        
        # Execute TDD cycle for this feature
        try:
            # Run the complete TDD cycle (RED→YELLOW→GREEN)
            tdd_result = await tdd_implementer.implement_feature_tdd(
                feature={
                    "id": feature.id,
                    "title": feature.title,
                    "description": feature.description
                },
                existing_code=accumulated_code,
                requirements=input_data.requirements,
                design_output=design_output,
                feature_index=i
            )
            
            # Store TDD result
            tdd_results.append(tdd_result)
            
            # Update accumulated code with implementation
            if tdd_result.implementation_code:
                code_files = _parse_code_files(tdd_result.implementation_code)
                accumulated_code.update(code_files)
            
            # Update accumulated test code
            if tdd_result.test_code:
                test_files = _parse_code_files(tdd_result.test_code)
                accumulated_test_code.update(test_files)
            
            # Update progress based on final phase
            if tdd_result.final_phase == TDDPhase.GREEN:
                progress_monitor.complete_feature(feature.id, success=True)
                print(f"\n✅ Feature completed in GREEN phase!")
                if tdd_result.green_phase_metrics:
                    metrics = tdd_result.green_phase_metrics
                    print(f"   Total cycle time: {metrics.get('metrics', {}).get('cycle_time_seconds', 0):.1f}s")
                    print(f"   Implementation attempts: {metrics.get('metrics', {}).get('implementation_attempts', 1)}")
            else:
                progress_monitor.complete_feature(feature.id, success=False)
                print(f"\n⚠️  Feature stuck in {tdd_result.final_phase.value if tdd_result.final_phase else 'UNKNOWN'} phase")
            
            # Create TeamMemberResult for compatibility
            feature_result = TeamMemberResult(
                team_member=TeamMember.coder,
                output=f"# Test Code:\n{tdd_result.test_code}\n\n# Implementation Code:\n{tdd_result.implementation_code}",
                name=f"tdd_feature_{i+1}",
                metadata={
                    "tdd_phase": tdd_result.final_phase.value if tdd_result.final_phase else None,
                    "success": tdd_result.success,
                    "retry_count": tdd_result.retry_count,
                    "test_results": {
                        "initial": {
                            "failed": tdd_result.initial_test_result.failed,
                            "expected_failure": tdd_result.initial_test_result.expected_failure
                        },
                        "final": {
                            "passed": tdd_result.final_test_result.passed,
                            "failed": tdd_result.final_test_result.failed,
                            "success": tdd_result.final_test_result.success
                        }
                    }
                }
            )
            results.append(feature_result)
            
        except Exception as e:
            print(f"\n❌ TDD cycle failed for feature: {str(e)}")
            progress_monitor.complete_feature(feature.id, success=False)
            
            # Create error result
            error_result = TeamMemberResult(
                team_member=TeamMember.coder,
                output=f"TDD cycle failed: {str(e)}",
                name=f"tdd_feature_{i+1}_error",
                metadata={"error": str(e), "success": False}
            )
            results.append(error_result)
        
        # Show progress bar with TDD phase information
        if (i + 1) % 2 == 0 or i == len(features) - 1:  # Every 2 features or at the end
            progress_monitor.print_progress_bar()
            # Show current phase distribution
            phase_dist = phase_tracker.get_phase_distribution()
            if phase_dist:
                print(f"   Phase Distribution: 🔴 RED: {phase_dist.get(TDDPhase.RED, 0)} | 🟡 YELLOW: {phase_dist.get(TDDPhase.YELLOW, 0)} | 🟢 GREEN: {phase_dist.get(TDDPhase.GREEN, 0)}")
    
    # Create final consolidated result with TDD summary
    print("\n📦 Consolidating final TDD implementation...")
    final_code = _consolidate_code(accumulated_code)
    
    # Show TDD summary
    print("\n📊 TDD Workflow Summary:")
    print(f"   Total features: {len(features)}")
    print(f"   Features in GREEN phase: {sum(1 for r in tdd_results if r.final_phase == TDDPhase.GREEN)}")
    print(f"   Features in YELLOW phase: {sum(1 for r in tdd_results if r.final_phase == TDDPhase.YELLOW)}")
    print(f"   Features in RED phase: {sum(1 for r in tdd_results if r.final_phase == TDDPhase.RED)}")
    print(f"   Features with retries: {sum(1 for r in tdd_results if r.retry_count > 0)}")
    
    # Get phase tracker summary
    phase_summary = phase_tracker.get_summary()
    print(f"\n🔄 TDD Phase Transitions: {phase_summary['total_transitions']}")
    
    # Count TDD results
    tdd_success_count = sum(1 for r in tdd_results if r.success and r.final_phase == TDDPhase.GREEN)
    tdd_partial_count = sum(1 for r in tdd_results if r.final_phase == TDDPhase.YELLOW)
    tdd_failed_count = sum(1 for r in tdd_results if r.final_phase == TDDPhase.RED or not r.success)
    
    final_result = TeamMemberResult(
        team_member=TeamMember.coder,
        output=final_code,
        name="final_implementation"
    )
    results.append(final_result)
    
    # Phase 6: End workflow and show summary (moved up to export metrics first)
    progress_monitor.end_workflow()
    
    # Export metrics for potential further analysis
    metrics = progress_monitor.export_metrics()
    
    # Final review of complete TDD implementation
    final_review_request = ReviewRequest(
        phase=ReviewPhase.FINAL_IMPLEMENTATION,
        content=final_code,
        context={
            "requirements": input_data.requirements,
            "tdd_summary": {
                "total_features": len(features),
                "green_phase": tdd_success_count,
                "yellow_phase": tdd_partial_count,
                "red_phase": tdd_failed_count,
                "total_transitions": phase_summary['total_transitions']
            },
            "feature_phases": {f.feature_id: f.final_phase.value for f in tdd_results if f.final_phase}
        }
    )
    
    final_review = await review_integration.request_review(final_review_request)
    
    print(f"\n📋 Final Implementation Review:")
    print(f"   Status: {'APPROVED' if final_review.approved else 'NEEDS REVISION'}")
    print(f"   Feedback: {final_review.feedback[:200]}...")
    
    # Generate comprehensive TDD review summary document
    print("\n📝 Generating TDD workflow summary document...")
    review_summary = await _generate_tdd_review_summary(
        input_data.requirements,
        review_integration,
        tdd_results,
        final_review,
        metrics,
        phase_tracker
    )
    
    # Add review summary to accumulated code as README.md
    accumulated_code['README.md'] = review_summary
    
    # Update final code with the review summary
    final_code = _consolidate_code(accumulated_code)
    
    # Update the final result with the new code including review summary
    final_result.output = final_code
    
    # Add review summary to metrics
    metrics['review_summary'] = review_integration.get_approval_summary()
    
    # Add metrics to the final result
    final_result.metadata = metrics
    
    # Save the accumulated code to disk
    from workflows.mvp_incremental.code_saver import CodeSaver
    from datetime import datetime
    from pathlib import Path
    
    print("\n💾 Saving generated code to disk...")
    # Use custom output path if provided, otherwise use default
    if hasattr(input_data, 'output_path') and input_data.output_path:
        code_saver = CodeSaver(base_path=Path(input_data.output_path))
    else:
        code_saver = CodeSaver()
    
    # Create a session directory with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_name = f"app_generated_{timestamp}"
    session_path = code_saver.create_session_directory(session_name)
    
    # Save all accumulated code files
    if accumulated_code:
        saved_files = code_saver.save_code_files(accumulated_code)
        print(f"   ✅ Saved {len(saved_files)} files to {session_path}")
        
    # Save test files with deduplication
    if accumulated_test_code:
        # Deduplicate test files, preferring those in tests/ directory
        deduplicated_test_files = _deduplicate_test_files(accumulated_test_code)
        
        # Log deduplication if any occurred
        if len(deduplicated_test_files) < len(accumulated_test_code):
            print(f"   📋 Deduplicated {len(accumulated_test_code)} test files to {len(deduplicated_test_files)}")
        
        test_saved_files = code_saver.save_code_files(deduplicated_test_files)
        print(f"   ✅ Saved {len(test_saved_files)} test files to {session_path}")
        
        # Extract dependencies and create requirements.txt if needed
        from workflows.mvp_incremental.code_saver import extract_dependencies_from_code
        dependencies = extract_dependencies_from_code(accumulated_code)
        if dependencies:
            code_saver.create_requirements_file(dependencies)
            print(f"   ✅ Created requirements.txt with {len(dependencies)} dependencies")
            
        # Save metadata about the workflow
        metadata = {
            "workflow_type": "mvp_incremental_tdd",
            "requirements": input_data.requirements[:500] + "..." if len(input_data.requirements) > 500 else input_data.requirements,
            "features_implemented": len(features),
            "tdd_summary": {
                "green_features": sum(1 for r in tdd_results if r.final_phase == TDDPhase.GREEN),
                "yellow_features": sum(1 for r in tdd_results if r.final_phase == TDDPhase.YELLOW),
                "red_features": sum(1 for r in tdd_results if r.final_phase == TDDPhase.RED)
            },
            "metrics": metrics
        }
        code_saver.save_metadata(metadata)
        print(f"   ✅ Saved session metadata")
    else:
        print("   ⚠️  No code files to save")
    
    # Create a symlink to latest for easy access
    latest_link = code_saver.base_path / "app_generated_latest"
    if latest_link.exists() and latest_link.is_symlink():
        latest_link.unlink()
    if accumulated_code or accumulated_test_code:  # Create symlink if we saved any code
        latest_link.symlink_to(session_path.name)
        print(f"   ✅ Created symlink: app_generated_latest -> {session_path.name}")
    
    # Phase 10: Integration Verification
    if hasattr(input_data, 'run_integration_verification') and input_data.run_integration_verification:
        print("\n🔍 Starting Integration Verification...")
        progress_monitor.start_phase("Integration Verification")
        
        # Use the session path we just created
        generated_path = session_path
        
        # Create feature summary for integration verification from TDD results
        feature_summary = []
        for i, feature in enumerate(features):
            tdd_result = tdd_results[i] if i < len(tdd_results) else None
            feature_data = {
                "name": feature.title,
                "id": feature.id,
                "status": "completed" if (tdd_result and tdd_result.final_phase == TDDPhase.GREEN) else "failed",
                "tdd_phase": tdd_result.final_phase.value if tdd_result and tdd_result.final_phase else "UNKNOWN",
                "retries": tdd_result.retry_count if tdd_result else 0,
                "test_driven": True  # All features are test-driven in this workflow
            }
            feature_summary.append(feature_data)
        
        # Create a simplified workflow report for integration verification
        class SimpleWorkflowReport:
            def __init__(self, output_path, total_duration):
                self.output_path = output_path
                self.total_duration = total_duration
        
        workflow_report = SimpleWorkflowReport(
            output_path=str(generated_path),
            total_duration=metrics.get('total_duration', 'unknown')
        )
        
        # Run integration verification
        integration_result, completion_report = await perform_integration_verification(
            generated_path,
            feature_summary,
            workflow_report,
            project_name=input_data.requirements.split('\n')[0][:50]  # First line as project name
        )
        
        print("\n📋 Integration Verification Results:")
        print(f"   All tests pass: {integration_result.all_tests_pass}")
        print(f"   Build successful: {integration_result.build_successful}")
        print(f"   Smoke test: {'PASSED' if integration_result.smoke_test_passed else 'FAILED'}")
        if integration_result.issues_found:
            print(f"   Issues found: {len(integration_result.issues_found)}")
            for issue in integration_result.issues_found[:3]:  # Show first 3 issues
                print(f"      - {issue}")
        
        print(f"\n📄 Completion report saved to: {generated_path}/COMPLETION_REPORT.md")
        
        # Add integration results to metrics
        metrics['integration_verification'] = {
            'tests_passed': integration_result.all_tests_pass,
            'build_successful': integration_result.build_successful,
            'issues_count': len(integration_result.issues_found)
        }
        
        progress_monitor.complete_step("integration_verification", success=integration_result.all_tests_pass)
    
    # Cleanup validator container
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


def _format_code_for_validator(code_dict: Dict[str, str]) -> str:
    """Format code for validator agent with proper file markers."""
    if not code_dict:
        return "No code to validate yet."
    
    formatted_parts = []
    for filename, content in code_dict.items():
        formatted_parts.append(f"""```python
# filename: {filename}
{content}
```""")
    
    return "\n\n".join(formatted_parts)


def _format_existing_code(code_dict: Dict[str, str]) -> str:
    """Format existing code for context."""
    if not code_dict:
        return "No existing code yet. This is the first feature."
    
    formatted = "The following files have been created so far:\n"
    for filename in sorted(code_dict.keys()):
        formatted += f"\n--- {filename} ---\n"
        # Show first 20 lines or 500 chars, whichever is shorter
        content = code_dict[filename]
        lines = content.split('\n')[:20]
        preview = '\n'.join(lines)
        if len(preview) > 500:
            preview = preview[:500] + "\n... (truncated)"
        formatted += preview + "\n"
    
    return formatted


def _parse_code_files(code_output: str) -> Dict[str, str]:
    """Extract files from coder output."""
    files = {}
    
    # First, check if this is the coder agent's structured output format
    if "--- IMPLEMENTATION DETAILS ---" in code_output:
        # Parse the structured format
        # Look for FILENAME: followed by code blocks
        file_pattern = r'FILENAME:\s*(\S+)\s*\n```(?:\w+)?\n(.*?)```'
        matches = re.findall(file_pattern, code_output, re.DOTALL)
        
        if matches:
            for filename, content in matches:
                files[filename] = content.strip()
            return files
    
    # Check for our new format: ```python\n# filename: path/to/file.py
    file_pattern = r'```(?:python|py|javascript|js)\s*\n#\s*filename:\s*(\S+)\n(.*?)```'
    matches = re.findall(file_pattern, code_output, re.DOTALL)
    
    if matches:
        for filename, content in matches:
            files[filename] = content.strip()
        return files
    
    # Fallback to original parsing for other formats
    # Look for file markers like ```python filename.py or just ```python
    file_pattern = r'```(?:python|py|javascript|js)\s*(?:# )?(\S+\.(?:py|js))?\n(.*?)```'
    matches = re.findall(file_pattern, code_output, re.DOTALL)
    
    if matches:
        for i, (filename, content) in enumerate(matches):
            if not filename:
                # Default filename if not specified
                filename = f"main.py" if i == 0 else f"module_{i}.py"
            files[filename] = content.strip()
    else:
        # Last fallback: treat entire output as main.py
        # But skip if it contains obvious non-code content
        if not any(marker in code_output for marker in ["✅ PROJECT CREATED", "📁 Location", "📄 Files created"]):
            files["main.py"] = code_output.strip()
    
    return files


async def _generate_tdd_review_summary(
    requirements: str,
    review_integration: ReviewIntegration,
    tdd_results: List[TDDFeatureResult],
    final_review: 'ReviewResult',
    metrics: Dict,
    phase_tracker: TDDPhaseTracker
) -> str:
    """Generate a comprehensive review summary document using an LLM."""
    from orchestrator.orchestrator_agent import run_team_member_with_tracking
    
    # Gather all review data
    approval_summary = review_integration.get_approval_summary()
    all_must_fix = review_integration.get_must_fix_items()
    
    # Get phase summary
    phase_summary = phase_tracker.get_summary()
    
    # Build prompt for TDD summary generation
    summary_prompt = f"""Generate a comprehensive review summary document in Markdown format for this Test-Driven Development (TDD) workflow project.

## Original Requirements
{requirements}

## TDD Workflow Summary
This project was implemented using MANDATORY Test-Driven Development with RED→YELLOW→GREEN phases.

### Phase Distribution
- Features in GREEN (completed): {sum(1 for r in tdd_results if r.final_phase == TDDPhase.GREEN)}
- Features in YELLOW (tests pass, awaiting review): {sum(1 for r in tdd_results if r.final_phase == TDDPhase.YELLOW)}
- Features in RED (tests written/failing): {sum(1 for r in tdd_results if r.final_phase == TDDPhase.RED)}

### TDD Metrics
- Total phase transitions: {phase_summary['total_transitions']}
- Features with test-first approach: 100% (mandatory)
- Average retry count: {sum(r.retry_count for r in tdd_results) / len(tdd_results) if tdd_results else 0:.1f}

## Review Summary by Phase
{_format_approval_summary(approval_summary)}

## Workflow Duration
- Total time: {metrics.get('workflow_duration', 0):.1f}s
- Phase breakdown: {metrics.get('phase_times', {})}

## Final Review Assessment
Status: {final_review.approved}
Feedback: {final_review.feedback}

## Feature-by-Feature TDD Results
{_format_tdd_feature_results(tdd_results)}

## All Must-Fix Items Identified
{chr(10).join(f'- {item}' for item in all_must_fix) if all_must_fix else 'None'}

Please create a professional README.md that includes:
1. Project Overview - summarize what was built
2. Implementation Status - which features succeeded/failed
3. Code Quality Assessment - based on all reviews
4. Key Recommendations - most important improvements needed
5. Technical Debt - issues to address in future iterations
6. Success Metrics - what went well
7. Lessons Learned - insights from the review process

Make it comprehensive but concise, focusing on actionable insights."""

    # Use the reviewer agent to generate the summary
    summary_result = await run_team_member_with_tracking(
        "feature_reviewer_agent",
        summary_prompt,
        "review_summary_generation"
    )
    
    # Extract content
    if isinstance(summary_result, list) and len(summary_result) > 0:
        summary_content = summary_result[0].parts[0].content
    else:
        summary_content = str(summary_result)
    
    # Ensure it's properly formatted as markdown
    if not summary_content.startswith("# "):
        summary_content = f"# Code Review Summary\n\n{summary_content}"
    
    return summary_content


def _format_approval_summary(approval_summary: Dict) -> str:
    """Format the approval summary for display."""
    lines = []
    for phase, data in approval_summary.items():
        lines.append(f"- **{phase.title()}**: {data['approved']} approved, {data['rejected']} rejected")
        if 'features' in data and data['features']:
            for feature_id, approved in data['features'].items():
                status = "✅" if approved else "❌"
                lines.append(f"  - {feature_id}: {status}")
    return '\n'.join(lines)


def _format_tdd_feature_results(tdd_results: List[TDDFeatureResult]) -> str:
    """Format TDD feature results for summary."""
    if not tdd_results:
        return "No features implemented"
    
    lines = []
    for result in tdd_results:
        phase_emoji = {
            TDDPhase.GREEN: "🟢",
            TDDPhase.YELLOW: "🟡", 
            TDDPhase.RED: "🔴"
        }.get(result.final_phase, "⚫")
        
        lines.append(f"### {result.feature_title}")
        lines.append(f"- Final Phase: {phase_emoji} {result.final_phase.value if result.final_phase else 'UNKNOWN'}")
        lines.append(f"- Tests Written: {result.initial_test_result.failed} tests (initially failing)")
        lines.append(f"- Final Test Status: {result.final_test_result.passed} passed, {result.final_test_result.failed} failed")
        lines.append(f"- Implementation Attempts: {result.retry_count + 1}")
        if result.green_phase_metrics:
            cycle_time = result.green_phase_metrics.get('metrics', {}).get('cycle_time_seconds', 0)
            lines.append(f"- Total Cycle Time: {cycle_time:.1f}s")
        lines.append("")
    
    return '\n'.join(lines)


def _consolidate_code(code_dict: Dict[str, str]) -> str:
    """Consolidate all code files into final output."""
    if not code_dict:
        return "# No code generated"
    
    output_parts = ["# Final Implementation\n"]
    
    for filename in sorted(code_dict.keys()):
        output_parts.append(f"\n## File: {filename}")
        output_parts.append("```python")
        output_parts.append(code_dict[filename])
        output_parts.append("```")
    
    return "\n".join(output_parts)


def _deduplicate_test_files(test_files: Dict[str, str]) -> Dict[str, str]:
    """
    Deduplicate test files, preferring those in tests/ directory.
    Consolidates tests for the same module into a single file.
    """
    from collections import defaultdict
    
    # Group files by their base name (without directory)
    file_groups = defaultdict(list)
    
    for filepath, content in test_files.items():
        # Extract base name (e.g., test_main.py from tests/test_main.py or test_main.py)
        basename = filepath.split('/')[-1]
        file_groups[basename].append((filepath, content))
    
    # For each group, prefer the one in tests/ directory
    deduplicated = {}
    
    for basename, file_list in file_groups.items():
        if len(file_list) == 1:
            # No duplicates
            deduplicated[file_list[0][0]] = file_list[0][1]
        else:
            # Multiple files with same base name
            # Prefer the one in tests/ directory
            tests_dir_file = None
            root_file = None
            
            for filepath, content in file_list:
                if filepath.startswith('tests/'):
                    tests_dir_file = (filepath, content)
                else:
                    root_file = (filepath, content)
            
            if tests_dir_file:
                deduplicated[tests_dir_file[0]] = tests_dir_file[1]
            elif root_file:
                # If no tests/ version, use root but move to tests/
                new_path = f"tests/{root_file[0]}"
                deduplicated[new_path] = root_file[1]
    
    # Ensure all test files are in tests/ directory
    final_files = {}
    for filepath, content in deduplicated.items():
        if not filepath.startswith('tests/'):
            filepath = f"tests/{filepath}"
        final_files[filepath] = content
    
    return final_files


