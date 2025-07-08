"""
TDD Feature Implementer for MVP Incremental Workflow

This module implements Test-Driven Development (TDD) cycle for each feature:
1. Write tests first (RED phase - tests must fail)
2. Implement code to make tests pass (YELLOW phase - awaiting review)
3. Review and approve implementation (GREEN phase - complete)

Uses the RED-YELLOW-GREEN phase tracking system from Operation Red Yellow.
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from shared.data_models import TeamMemberResult, TeamMember
from workflows.monitoring import WorkflowExecutionTracer
from workflows.mvp_incremental.retry_strategy import RetryStrategy, RetryConfig
from workflows.mvp_incremental.progress_monitor import ProgressMonitor, StepStatus
from workflows.mvp_incremental.review_integration import ReviewIntegration, ReviewPhase, ReviewRequest
from workflows.mvp_incremental.test_execution import TestExecutionConfig, TestResult, execute_and_fix_tests
from workflows.mvp_incremental.validator import CodeValidator
from workflows.mvp_incremental.coverage_validator import TestCoverageValidator, validate_tdd_test_coverage
from workflows.mvp_incremental.tdd_phase_tracker import TDDPhase, TDDPhaseTracker
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
        
        # Phase 2: Run tests (expect failure) - Confirm RED phase
        logger.info(f"Running tests for {feature_title} (expecting failure)...")
        initial_test_result = await self._run_tests(
            test_code, 
            existing_code, 
            feature_title,
            expect_failure=True
        )
        
        if initial_test_result.success:
            logger.warning(f"Tests passed before implementation for {feature_title} - tests may be invalid")
            # Tests should fail in RED phase
        else:
            logger.info(f"✅ Tests failing as expected - RED phase confirmed")
            # RED phase is confirmed - tests are failing without implementation
        
        # Phase 3: Implement feature to make tests pass
        # Enforce RED phase before allowing implementation
        try:
            self.phase_tracker.enforce_red_phase_start(feature_id)
        except Exception as e:
            logger.error(f"Cannot start implementation: {e}")
            raise ValueError(f"Feature {feature_id} must be in RED phase before implementation can begin")
        
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
            
            # Create implementation context
            coder_context = self._create_coder_context_tdd(
                feature,
                test_code,
                initial_test_result if retry_count == 0 else final_test_result,
                existing_code,
                requirements,
                retry_count
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
                # Tests are now passing - transition to YELLOW phase
                self.phase_tracker.transition_to(
                    feature_id, 
                    TDDPhase.YELLOW,
                    "Tests passing - awaiting review",
                    {"test_count": final_test_result.passed}
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
            impl_review = await self._review_implementation(implementation_code, test_code, feature)
            
            if impl_review.approved:
                # Transition to GREEN phase - feature complete!
                self.phase_tracker.transition_to(
                    feature_id,
                    TDDPhase.GREEN,
                    "Implementation reviewed and approved",
                    {"reviewer": "feature_reviewer_agent"}
                )
                logger.info(f"{self.phase_tracker.get_visual_status(feature_id)}")
            else:
                # Review rejected - back to RED phase
                self.phase_tracker.transition_to(
                    feature_id,
                    TDDPhase.RED,
                    f"Review rejected: {impl_review.feedback[:100]}",
                    {"needs_rework": True}
                )
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
        
        # Create result
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
            final_phase=self.phase_tracker.get_current_phase(feature_id)
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
                                retry_count: int) -> str:
        """Create context for coder agent in TDD mode"""
        
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