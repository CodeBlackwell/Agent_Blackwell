"""
TDD Feature Implementer for MVP Incremental Workflow

This module implements Test-Driven Development (TDD) cycle for each feature:
1. Write tests first (RED phase - tests must fail)
2. Implement code to make tests pass (YELLOW phase - awaiting review)
3. Review and approve implementation (GREEN phase - complete)

Uses the RED-YELLOW-GREEN phase tracking system from Operation Red Yellow.
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

from shared.data_models import TeamMemberResult, TeamMember
from workflows.monitoring import WorkflowExecutionTracer
from workflows.mvp_incremental.retry_strategy import RetryStrategy, RetryConfig
from workflows.mvp_incremental.progress_monitor import ProgressMonitor, StepStatus
from workflows.mvp_incremental.review_integration import ReviewIntegration, ReviewPhase, ReviewRequest
from workflows.mvp_incremental.test_execution import TestExecutionConfig, TestResult, execute_and_fix_tests, TestExecutor
from workflows.mvp_incremental.validator import CodeValidator
from workflows.mvp_incremental.coverage_validator import TestCoverageValidator, validate_tdd_test_coverage
from workflows.mvp_incremental.tdd_phase_tracker import TDDPhase, TDDPhaseTracker
from workflows.mvp_incremental.red_phase import RedPhaseOrchestrator, RedPhaseError
from workflows.mvp_incremental.yellow_phase import YellowPhaseOrchestrator, YellowPhaseError
from workflows.mvp_incremental.green_phase import GreenPhaseOrchestrator, GreenPhaseMetrics, GreenPhaseError
from workflows.mvp_incremental.testable_feature_parser import TestableFeature
from workflows.logger import workflow_logger as logger


@dataclass
class TDDFeatureResult:
    """Result of TDD feature implementation"""
    feature_id: str
    feature_title: str
    test_code: str
    implementation_code: str
    initial_test_result: TestResult
    final_test_result: TestResult
    refactored: bool = False
    retry_count: int = 0
    success: bool = False
    final_phase: Optional[TDDPhase] = None
    green_phase_metrics: Optional[Dict[str, Any]] = None  # Metrics from GREEN phase completion


class TDDFeatureImplementer:
    """Manages TDD cycle for feature implementation with RED-YELLOW-GREEN tracking"""
    
    def __init__(self,
                 tracer: WorkflowExecutionTracer,
                 progress_monitor: ProgressMonitor,
                 review_integration: ReviewIntegration,
                 retry_strategy: RetryStrategy,
                 retry_config: RetryConfig,
                 phase_tracker: Optional[TDDPhaseTracker] = None):
        self.tracer = tracer
        self.progress_monitor = progress_monitor
        self.review_integration = review_integration
        self.retry_strategy = retry_strategy
        self.retry_config = retry_config
        self.validator = CodeValidator()
        self.phase_tracker = phase_tracker or TDDPhaseTracker()
        # Initialize test executor for RED phase orchestrator
        test_config = TestExecutionConfig(
            run_tests=True,
            fix_on_failure=False,
            test_timeout=30,
            expect_failure=True,
            cache_results=True,
            extract_coverage=False,
            verbose_output=True
        )
        self.test_executor = TestExecutor(self.validator, test_config)
        self.red_phase_orchestrator = RedPhaseOrchestrator(self.test_executor, self.phase_tracker)
        self.yellow_phase_orchestrator = YellowPhaseOrchestrator(self.phase_tracker)
        self.green_phase_orchestrator = GreenPhaseOrchestrator(self.phase_tracker)
        
    async def implement_feature_tdd(self,
                                  feature: Dict[str, str],
                                  existing_code: Dict[str, str],
                                  requirements: str,
                                  design_output: str,
                                  feature_index: int) -> TDDFeatureResult:
        """
        Implement a feature using TDD approach.
        
        Args:
            feature: Feature dictionary with id, title, description
            existing_code: Already implemented code files
            requirements: Original project requirements
            design_output: Design phase output
            feature_index: Index of this feature in the sequence
            
        Returns:
            TDDFeatureResult with test and implementation details
        """
        from orchestrator.orchestrator_agent import run_team_member_with_tracking
        
        feature_id = feature['id']
        feature_title = feature['title']
        
        logger.info(f"Starting TDD implementation for {feature_title}")
        self.progress_monitor.update_step(f"feature_{feature_id}", StepStatus.IN_PROGRESS)
        
        # Start tracking this feature in RED phase
        self.phase_tracker.start_feature(feature_id, {
            "title": feature_title,
            "index": feature_index
        })
        logger.info(f"{self.phase_tracker.get_visual_status(feature_id)}")
        
        # Phase 1: Write tests for the feature
        test_step_id = self.tracer.start_step(
            f"tdd_write_tests_{feature_id}",
            "test_writer_agent",
            {"feature": feature_title, "phase": "write_tests"}
        )
        
        test_writer_context = self._create_test_writer_context(
            feature, existing_code, requirements, design_output
        )
        
        test_result = await run_team_member_with_tracking(
            "test_writer_agent",
            test_writer_context,
            f"mvp_tdd_tests_{feature_index}"
        )
        
        # Extract test code
        test_code = self._extract_test_code(test_result)
        
        self.tracer.complete_step(test_step_id, {
            "tests_written": True,
            "test_files": self._count_test_files(test_code)
        })
        
        # Review the tests before proceeding
        test_review = await self._review_tests(test_code, feature)
        if not test_review.approved:
            logger.warning(f"Test review not approved for {feature_title}: {test_review.feedback}")
        
        # Phase 2: Run tests (expect failure) - Confirm RED phase using orchestrator
        logger.info(f"Validating RED phase for {feature_title} (expecting tests to fail)...")
        
        # Create TestableFeature for RED phase validation
        testable_feature = TestableFeature(
            id=feature_id,
            title=feature_title,
            description=feature['description'],
            test_criteria=[]  # Will be populated from test code
        )
        
        # Save test code to temporary location for execution
        import tempfile
        import os
        test_dir = tempfile.mkdtemp(prefix="tdd_tests_")
        test_file_path = os.path.join(test_dir, "test_feature.py")
        with open(test_file_path, 'w') as f:
            f.write(test_code)
        
        try:
            # Use RED phase orchestrator to validate and extract failure context
            red_phase_context = await self.red_phase_orchestrator.enforce_red_phase(
                testable_feature,
                test_file_path,
                os.getcwd()  # Use current working directory as project root
            )
            
            logger.info(f"✅ RED phase validated - {red_phase_context['failure_summary']['total_failures']} test failures detected")
            
            # Log failure types for visibility
            failure_types = red_phase_context['failure_summary'].get('failure_types', [])
            if failure_types:
                logger.info(f"   Failure types: {', '.join(failure_types)}")
            
            # Log missing components to guide implementation
            missing_components = red_phase_context.get('missing_components', [])
            if missing_components:
                logger.info(f"   Missing components: {', '.join(missing_components[:3])}")
            
            # Store RED phase context for use in implementation
            red_phase_info = red_phase_context
            
        except RedPhaseError as e:
            logger.error(f"RED phase validation failed: {e}")
            # Clean up temp directory
            import shutil
            shutil.rmtree(test_dir, ignore_errors=True)
            raise ValueError(f"Cannot proceed: {e}")
        finally:
            # Clean up temp directory
            import shutil
            shutil.rmtree(test_dir, ignore_errors=True)
        
        # Convert failure context to TestResult for backward compatibility
        initial_test_result = TestResult(
            success=False,  # Tests should fail in RED phase
            passed=0,
            failed=red_phase_context['failure_summary']['total_failures'],
            errors=[f['failure_message'] for f in red_phase_context['detailed_failures']],
            output="RED phase validated - tests failing as expected",
            test_files=self._extract_test_files(test_code),
            expected_failure=True
        )
        
        retry_count = 0
        implementation_successful = False
        implementation_code = ""
        final_test_result = initial_test_result
        
        while not implementation_successful and retry_count <= self.retry_config.max_retries:
            impl_step_id = self.tracer.start_step(
                f"tdd_implement_{feature_id}_attempt_{retry_count}",
                "coder_agent",
                {"feature": feature_title, "retry": retry_count}
            )
            
            # Create implementation context with RED phase info
            coder_context = self._create_coder_context_tdd(
                feature,
                test_code,
                initial_test_result if retry_count == 0 else final_test_result,
                existing_code,
                requirements,
                retry_count,
                red_phase_context=red_phase_info if retry_count == 0 else None
            )
            
            # Run coder agent
            coder_result = await run_team_member_with_tracking(
                "feature_coder_agent",
                coder_context,
                f"mvp_tdd_implement_{feature_index}_attempt_{retry_count}"
            )
            
            implementation_code = self._extract_implementation_code(coder_result)
            
            self.tracer.complete_step(impl_step_id, {
                "implementation_complete": True,
                "retry_count": retry_count
            })
            
            # Phase 4: Run tests again (expect success)
            logger.info(f"Running tests for {feature_title} (expecting success)...")
            updated_code = existing_code.copy()
            updated_code.update(self._parse_code_files(implementation_code))
            
            final_test_result = await self._run_tests(
                test_code,
                updated_code,
                feature_title,
                expect_failure=False
            )
            
            if final_test_result.success:
                # Tests are now passing - transition to YELLOW phase using orchestrator
                yellow_context = await self.yellow_phase_orchestrator.enter_yellow_phase(
                    feature=testable_feature,
                    test_results=final_test_result,
                    implementation_path=f"Feature {feature_id} implementation",
                    implementation_summary=f"Implemented {feature_title} based on test requirements"
                )
                logger.info(f"{self.phase_tracker.get_visual_status(feature_id)}")
                
                # Validate test coverage with enhanced metrics
                logger.info(f"Validating test coverage for {feature_title}...")
                coverage_success, coverage_msg, coverage_result = await validate_tdd_test_coverage(
                    test_code,
                    implementation_code,
                    minimum_coverage=80.0,
                    minimum_branch_coverage=70.0,
                    feature_id=feature_id
                )
                
                if coverage_success:
                    implementation_successful = True
                    logger.info(f"✅ Tests passing with sufficient coverage for {feature_title}")
                    for line in coverage_msg.split('\n'):
                        if line.strip():
                            logger.info(f"   {line.strip()}")
                    
                    # Log test quality score
                    if coverage_result and coverage_result.test_quality_score > 0:
                        logger.info(f"   📊 Test Quality Score: {coverage_result.test_quality_score:.1f}/100")
                    
                    # Check if coverage improved
                    if coverage_result and coverage_result.coverage_improved:
                        logger.info(f"   📈 Coverage improved from {coverage_result.previous_coverage:.1f}% to {coverage_result.coverage_report.coverage_percentage:.1f}%")
                else:
                    logger.warning(f"⚠️  Tests pass but coverage insufficient for {feature_title}")
                    for line in coverage_msg.split('\n'):
                        if line.strip():
                            logger.warning(f"   {line.strip()}")
                    
                    # Log suggestions
                    if coverage_result and coverage_result.suggestions:
                        logger.warning(f"   💡 Suggestions:")
                        for suggestion in coverage_result.suggestions[:3]:  # Show top 3
                            logger.warning(f"      - {suggestion}")
                    
                    # Continue anyway but log the issue
                    implementation_successful = True
            else:
                # Tests still failing, may need to retry
                if self.retry_strategy.should_retry(str(final_test_result.errors), retry_count, self.retry_config):
                    retry_count += 1
                    logger.info(f"🔄 Retrying implementation for {feature_title} (attempt {retry_count})")
                else:
                    logger.error(f"❌ Tests still failing for {feature_title} after {retry_count} attempts")
                    break
        
        # Phase 5: Review implementation if tests are passing (YELLOW → GREEN)
        if implementation_successful and self.phase_tracker.get_current_phase(feature_id) == TDDPhase.YELLOW:
            logger.info(f"Requesting implementation review for {feature_title}...")
            
            # Get review context from YELLOW phase orchestrator
            review_context = self.yellow_phase_orchestrator.prepare_review_context(feature_id)
            
            # Perform the review
            impl_review = await self._review_implementation(implementation_code, test_code, feature)
            
            # Handle review result through orchestrator
            next_phase = await self.yellow_phase_orchestrator.handle_review_result(
                feature_id=feature_id,
                approved=impl_review.approved,
                feedback=impl_review.feedback
            )
            
            if impl_review.approved:
                # Enter GREEN phase after approval
                metrics = GreenPhaseMetrics(
                    feature_id=feature_id,
                    feature_title=feature_title,
                    red_phase_start=self.phase_tracker.get_phase_history(feature_id)[0][1],  # First phase entry time
                    yellow_phase_start=yellow_context.time_entered_yellow,
                    green_phase_start=datetime.now(),
                    implementation_attempts=retry_count + 1,
                    review_attempts=yellow_context.review_attempts,
                    test_execution_count=retry_count + 2  # Initial RED + implementation attempts
                )
                
                try:
                    green_context = self.green_phase_orchestrator.enter_green_phase(
                        feature=testable_feature,
                        metrics=metrics,
                        review_approved=True,
                        review_feedback=impl_review.feedback
                    )
                    logger.info(f"{self.phase_tracker.get_visual_status(feature_id)}")
                    
                    # Complete the feature in GREEN phase
                    completion_notes = [
                        f"Tests written first and confirmed to fail",
                        f"Implementation completed in {retry_count + 1} attempt(s)",
                        f"All tests passing with implementation",
                        f"Code reviewed and approved"
                    ]
                    
                    completion_summary = self.green_phase_orchestrator.complete_feature(
                        green_context,
                        completion_notes=completion_notes
                    )
                    
                    # Log celebration message
                    logger.info(completion_summary["celebration_message"])
                    
                except GreenPhaseError as e:
                    logger.error(f"Failed to enter GREEN phase: {e}")
                    implementation_successful = False
            else:
                logger.warning(f"Implementation review rejected - back to RED phase")
                logger.warning(f"Feedback: {impl_review.feedback}")
                implementation_successful = False
        
        # Phase 6: Optional refactoring (only in GREEN phase)
        refactored = False
        if implementation_successful and self.phase_tracker.get_current_phase(feature_id) == TDDPhase.GREEN:
            if self._should_refactor(implementation_code, test_code):
                logger.info(f"Refactoring {feature_title}...")
                # In a full implementation, this would call a refactoring agent
                # For now, we'll skip actual refactoring
                refactored = False
        
        # Create result with GREEN phase metrics if available
        green_metrics = None
        if implementation_successful and self.phase_tracker.get_current_phase(feature_id) == TDDPhase.GREEN:
            # Get completion summary from GREEN phase orchestrator
            completion_report = self.green_phase_orchestrator.get_completion_report()
            # Find this feature's metrics
            for feature_data in completion_report.get("features", []):
                if feature_data["feature_id"] == feature_id:
                    green_metrics = feature_data
                    break
        
        result = TDDFeatureResult(
            feature_id=feature_id,
            feature_title=feature_title,
            test_code=test_code,
            implementation_code=implementation_code,
            initial_test_result=initial_test_result,
            final_test_result=final_test_result,
            refactored=refactored,
            retry_count=retry_count,
            success=implementation_successful,
            final_phase=self.phase_tracker.get_current_phase(feature_id),
            green_phase_metrics=green_metrics
        )
        
        # Update progress monitor
        if implementation_successful:
            self.progress_monitor.update_step(f"feature_{feature_id}", StepStatus.COMPLETED)
        else:
            self.progress_monitor.update_step(f"feature_{feature_id}", StepStatus.FAILED)
        
        return result
    
    def _create_test_writer_context(self,
                                  feature: Dict[str, str],
                                  existing_code: Dict[str, str],
                                  requirements: str,
                                  design_output: str) -> str:
        """Create context for test writer agent"""
        # Extract test criteria if available
        test_criteria = feature.get('test_criteria', {})
        criteria_section = ""
        
        if test_criteria:
            criteria_section = "\n\nTEST CRITERIA FROM DESIGN:"
            
            if test_criteria.get('input_examples'):
                criteria_section += "\nInput Examples:"
                for example in test_criteria['input_examples']:
                    criteria_section += f"\n  - {example}"
                    
            if test_criteria.get('expected_outputs'):
                criteria_section += "\nExpected Outputs:"
                for output in test_criteria['expected_outputs']:
                    criteria_section += f"\n  - {output}"
                    
            if test_criteria.get('edge_cases'):
                criteria_section += "\nEdge Cases to Test:"
                for edge in test_criteria['edge_cases']:
                    criteria_section += f"\n  - {edge}"
                    
            if test_criteria.get('error_conditions'):
                criteria_section += "\nError Conditions:"
                for error in test_criteria['error_conditions']:
                    criteria_section += f"\n  - {error}"
        
        context = f"""
You are implementing Test-Driven Development (TDD) for a specific feature.
Your task is to write tests BEFORE the implementation exists.

PROJECT REQUIREMENTS:
{requirements}

FEATURE TO TEST:
Title: {feature['title']}
Description: {feature['description']}
{criteria_section}

DESIGN CONTEXT:
{design_output[:1000]}...

EXISTING CODE:
{self._format_existing_code(existing_code)}

CRITICAL TDD INSTRUCTIONS:
1. Write tests that will FAIL because the feature is NOT implemented yet
2. Tests should define the expected behavior and interface
3. Include both positive and negative test cases
4. Tests should be specific to THIS feature only
5. Use appropriate testing framework (pytest for Python, jest for JS, etc.)
6. Tests should be executable, not just examples

REQUIRED OUTPUT FORMAT:
Generate ONLY executable test files in this format:

```python
# filename: tests/test_[feature_name].py
import pytest
from main import FeatureName  # This import will fail initially

def test_feature_behavior():
    # This test MUST fail initially
    result = FeatureName.do_something()
    assert result == expected_value

def test_edge_case():
    with pytest.raises(ValueError):
        FeatureName.invalid_input()
```

Write tests that clearly define what the feature should do.
"""
        return context
    
    def _create_coder_context_tdd(self,
                                feature: Dict[str, str],
                                test_code: str,
                                test_result: TestResult,
                                existing_code: Dict[str, str],
                                requirements: str,
                                retry_count: int,
                                red_phase_context: Optional[Dict[str, Any]] = None) -> str:
        """Create context for coder agent in TDD mode with RED phase guidance"""
        
        # Base context
        context = f"""
You are implementing code to make failing tests pass (TDD Green Phase).

FEATURE TO IMPLEMENT:
Title: {feature['title']}
Description: {feature['description']}

FAILING TESTS:
{test_code}

TEST RESULTS:
{self._format_test_results(test_result)}
"""

        # Add RED phase context if available
        if red_phase_context:
            context += f"""
RED PHASE ANALYSIS:
- Total failures: {red_phase_context['failure_summary']['total_failures']}
- Failure types: {', '.join(red_phase_context['failure_summary']['failure_types'])}
"""
            if red_phase_context.get('missing_components'):
                context += f"- Missing components: {', '.join(red_phase_context['missing_components'])}\n"
            
            if red_phase_context.get('implementation_hints'):
                context += "\nIMPLEMENTATION HINTS:\n"
                for hint in red_phase_context['implementation_hints']:
                    context += f"- {hint}\n"
            
            context += "\n"
        
        if retry_count > 0:
            context += f"""
RETRY ATTEMPT: {retry_count}
Previous implementation failed to make all tests pass.
Focus on the specific test failures above.
"""
        
        context += f"""
EXISTING CODE:
{self._format_existing_code(existing_code)}

TDD IMPLEMENTATION RULES:
1. Write ONLY the code needed to make the tests pass
2. Do NOT add features not covered by tests
3. Keep implementation simple - no premature optimization
4. Ensure all test assertions are satisfied
5. Maintain compatibility with existing code
6. Focus on making tests green

OUTPUT FORMAT:
```python
# filename: path/to/implementation.py
<implementation code>
```

Make the tests pass with minimal, clean code.
"""
        return context
    
    async def _run_tests(self,
                        test_code: str,
                        implementation_code: Dict[str, str],
                        feature_name: str,
                        expect_failure: bool) -> TestResult:
        """Run tests using enhanced test executor with RED phase support"""
        # Use enhanced test executor with expect_failure support
        test_config = TestExecutionConfig(
            run_tests=True,
            fix_on_failure=False,  # Don't auto-fix in TDD mode
            test_timeout=30,
            expect_failure=expect_failure,  # Pass RED phase expectation
            cache_results=True,  # Use caching for performance
            extract_coverage=not expect_failure,  # No coverage in RED phase
            verbose_output=True  # Get detailed failure info
        )
        
        try:
            from workflows.mvp_incremental.test_execution import TestExecutor, execute_and_fix_tests
            
            # Combine test code with implementation
            all_code = self._format_code_for_validator(implementation_code)
            if test_code:
                all_code += "\n\n# Test Code\n" + test_code
            
            # Extract test files from test_code for targeted execution
            test_files = self._extract_test_files(test_code)
            
            # Use the enhanced test executor
            if self.validator:
                executor = TestExecutor(self.validator, test_config)
                result = await executor.execute_tests(
                    all_code, 
                    feature_name,
                    test_files=test_files,
                    expect_failure=expect_failure
                )
                
                # Log detailed failure information if available
                if result.failure_details and len(result.failure_details) > 0:
                    logger.info(f"Test failure details for {feature_name}:")
                    for detail in result.failure_details[:3]:  # Show first 3
                        logger.info(f"  - {detail.test_name}: {detail.failure_type} - {detail.failure_message[:100]}")
                
                return result
            else:
                # Fallback if no validator available
                if expect_failure and not implementation_code:
                    return TestResult(
                        success=True,  # Success because we expect failure
                        passed=0,
                        failed=len(test_files),
                        errors=["No implementation - tests failing as expected"],
                        output="Tests failed (RED phase confirmed)",
                        test_files=test_files,
                        expected_failure=True
                    )
                else:
                    return TestResult(
                        success=False,
                        passed=0,
                        failed=0,
                        errors=["No validator available for test execution"],
                        output="",
                        test_files=test_files,
                        expected_failure=expect_failure
                    )
                
        except Exception as e:
            logger.error(f"Error running tests: {str(e)}")
            return TestResult(
                success=False,
                passed=0,
                failed=1,
                errors=[str(e)],
                output=f"Test execution error: {str(e)}",
                test_files=[],
                expected_failure=expect_failure
            )
    
    async def _review_tests(self, test_code: str, feature: Dict[str, str]) -> 'ReviewResult':
        """Review the written tests"""
        review_request = ReviewRequest(
            phase=ReviewPhase.TEST_SPECIFICATION,
            content=test_code,
            context={
                "feature": feature,
                "purpose": "TDD test review - ensure tests are comprehensive and will guide implementation"
            }
        )
        
        return await self.review_integration.request_review(review_request)
    
    async def _review_implementation(self, implementation_code: str, test_code: str, feature: Dict[str, str]) -> 'ReviewResult':
        """Review the implementation after tests pass"""
        review_request = ReviewRequest(
            phase=ReviewPhase.IMPLEMENTATION,
            content=implementation_code,
            context={
                "feature": feature,
                "test_code": test_code,
                "purpose": "TDD implementation review - verify code quality and test compliance"
            }
        )
        
        return await self.review_integration.request_review(review_request)
    
    def _should_refactor(self, implementation_code: str, test_code: str) -> bool:
        """Determine if refactoring is needed"""
        # Simple heuristics for refactoring need
        code_lines = implementation_code.count('\n')
        
        # Check for code smells
        if code_lines > 100:  # Long methods/classes
            return True
        if implementation_code.count('if') > 10:  # Complex conditionals
            return True
        if 'TODO' in implementation_code or 'FIXME' in implementation_code:
            return True
        if 'copy-paste' in implementation_code.lower():
            return True
            
        return False
    
    def _extract_test_code(self, test_result) -> str:
        """Extract test code from test writer result"""
        if isinstance(test_result, list) and len(test_result) > 0:
            return test_result[0].parts[0].content
        return str(test_result)
    
    def _extract_implementation_code(self, coder_result) -> str:
        """Extract implementation code from coder result"""
        if isinstance(coder_result, list) and len(coder_result) > 0:
            return coder_result[0].parts[0].content
        return str(coder_result)
    
    def _format_test_results(self, test_result: TestResult) -> str:
        """Format test results for display"""
        return f"""
Total Tests: {test_result.passed + test_result.failed}
Passed: {test_result.passed}
Failed: {test_result.failed}

Failures:
{chr(10).join(f"- {error}" for error in test_result.errors[:5])}

Output:
{test_result.output[:500]}
"""
    
    def _count_test_files(self, test_code: str) -> int:
        """Count number of test files in code"""
        return len(re.findall(r'# filename: test.*\.py', test_code))
    
    def _extract_test_files(self, test_code: str) -> List[str]:
        """Extract test file names from test code"""
        matches = re.findall(r'# filename: (test.*\.py)', test_code)
        return matches
    
    def _format_existing_code(self, code_dict: Dict[str, str]) -> str:
        """Format existing code for context"""
        if not code_dict:
            return "No existing code yet."
        
        formatted = []
        for filename, content in code_dict.items():
            # Show first 30 lines of each file
            lines = content.split('\n')[:30]
            preview = '\n'.join(lines)
            formatted.append(f"=== {filename} ===\n{preview}\n")
        
        return '\n'.join(formatted)
    
    def _format_code_for_validator(self, code_dict: Dict[str, str]) -> str:
        """Format code for validator"""
        if not code_dict:
            return ""
        
        formatted_parts = []
        for filename, content in code_dict.items():
            formatted_parts.append(f"""```python
# filename: {filename}
{content}
```""")
        
        return "\n\n".join(formatted_parts)
    
    def _parse_code_files(self, code_output: str) -> Dict[str, str]:
        """Parse code files from output"""
        files = {}
        
        # Look for our standard format
        file_pattern = r'```(?:python|py|javascript|js)\s*\n#\s*filename:\s*(\S+)\n(.*?)```'
        matches = re.findall(file_pattern, code_output, re.DOTALL)
        
        if matches:
            for filename, content in matches:
                files[filename] = content.strip()
        
        return files


def create_tdd_implementer(tracer: WorkflowExecutionTracer,
                          progress_monitor: ProgressMonitor,
                          review_integration: ReviewIntegration,
                          phase_tracker: Optional[TDDPhaseTracker] = None) -> TDDFeatureImplementer:
    """Factory function to create TDD implementer with default configuration"""
    retry_config = RetryConfig()
    retry_strategy = RetryStrategy()
    
    return TDDFeatureImplementer(
        tracer=tracer,
        progress_monitor=progress_monitor,
        review_integration=review_integration,
        retry_strategy=retry_strategy,
        retry_config=retry_config,
        phase_tracker=phase_tracker
    )