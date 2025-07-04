"""
Incremental executor utilities for managing progressive code validation.
Follows ACP orchestrator patterns for session and state management.
"""
import asyncio
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import re

from shared.utils.feature_parser import Feature, ComplexityLevel
from workflows.monitoring import WorkflowExecutionTracer
from shared.data_models import TeamMemberResult, ExecutionResult
from workflows.workflow_config import EXECUTION_CONFIG


@dataclass
class ValidationResult(ExecutionResult):
    """Result of feature validation following ACP execution result patterns"""
    success: bool
    feedback: str
    execution_details: Dict[str, Any]
    files_validated: List[str]
    tests_passed: Optional[int] = None
    tests_failed: Optional[int] = None


class IncrementalExecutor:
    """
    Manages incremental code execution and validation.
    Follows ACP orchestrator patterns for session management.
    """
    
    def __init__(self, session_id: str, tracer: Optional[WorkflowExecutionTracer] = None):
        self.session_id = session_id
        self.tracer = tracer
        self.codebase_state: Dict[str, str] = {}
        self.validated_features: List[str] = []
    
    async def validate_feature(
        self,
        feature: Feature,
        new_files: Dict[str, str],
        existing_tests: Optional[str] = None
    ) -> ValidationResult:
        """
        Validate a single feature implementation.
        Follows ACP pattern for agent invocation.
        """
        from orchestrator.orchestrator_agent import run_agent
        
        # Update codebase state
        self.codebase_state.update(new_files)
        
        # Prepare executor input following ACP message format
        executor_input = self._prepare_executor_input(
            feature, 
            new_files, 
            existing_tests
        )
        
        # Record validation attempt if tracer is available
        if self.tracer:
            validation_id = self.tracer.record_execution(
                execution_name=f"validate_{feature.id}",
                execution_type="feature_validation"
            )
        
        try:
            # Run executor agent following ACP patterns
            result = await run_agent("executor", executor_input, session_id=self.session_id)
            execution_output = str(result)
            
            # Parse results
            validation_result = self._parse_validation_output(
                execution_output,
                feature,
                new_files
            )
            
            # Update tracer
            if self.tracer:
                self.tracer.record_result(
                    execution_id=validation_id,
                    success=validation_result.success,
                    details=validation_result.execution_details
                )
            
            # Track successful features
            if validation_result.success:
                self.validated_features.append(feature.id)
            
            return validation_result
            
        except Exception as e:
            error_result = ValidationResult(
                success=False,
                feedback=f"Execution error: {str(e)}",
                execution_details={"error": str(e)},
                files_validated=list(new_files.keys())
            )
            
            if self.tracer:
                self.tracer.record_result(
                    execution_id=validation_id,
                    success=False,
                    details=error_result.execution_details
                )
            
            return error_result
    
    def _prepare_executor_input(
        self, 
        feature: Feature,
        new_files: Dict[str, str],
        tests: Optional[str]
    ) -> str:
        """Prepare input for executor agent following ACP message format"""
        input_lines = [
            f"SESSION_ID: {self.session_id}",
            "OPERATION: incremental_validation",
            f"FEATURE: {feature.title}",
            "",
            "Add these files to the existing codebase:"
        ]
        
        # Add new files
        for filename, content in new_files.items():
            input_lines.extend([
                "",
                f"FILENAME: {filename}",
                "```python",
                content,
                "```"
            ])
        
        # Add validation criteria
        input_lines.extend([
            "",
            "VALIDATION CRITERIA:",
            feature.validation_criteria,
            "",
            "Verify that the above criteria is met."
        ])
        
        # Add tests if provided (TDD workflow)
        if tests and self._extract_relevant_tests(tests, feature):
            input_lines.extend([
                "",
                "Run these relevant tests:",
                self._extract_relevant_tests(tests, feature)
            ])
        
        # Add focus instruction
        input_lines.extend([
            "",
            "IMPORTANT: Focus validation and feedback on the NEW functionality only.",
            "The existing codebase has already been validated."
        ])
        
        return "\n".join(input_lines)
    
    def _parse_validation_output(
        self,
        output: str,
        feature: Feature,
        new_files: Dict[str, str]
    ) -> ValidationResult:
        """Parse executor output into ValidationResult"""
        success = False
        feedback_lines = []
        test_results = {"passed": 0, "failed": 0}
        
        # Check for success indicators
        success_indicators = ["✅", "passed", "success", "validated"]
        failure_indicators = ["❌", "failed", "error", "failure"]
        
        output_lower = output.lower()
        
        # Determine success
        if any(indicator in output_lower for indicator in success_indicators):
            if not any(indicator in output_lower for indicator in failure_indicators):
                success = True
        
        # Extract test results if present
        test_match = re.search(r'(\d+)\s+passed.*?(\d+)\s+failed', output, re.IGNORECASE)
        if test_match:
            test_results["passed"] = int(test_match.group(1))
            test_results["failed"] = int(test_match.group(2))
            success = test_results["failed"] == 0
        
        # Extract specific feedback
        if "error" in output_lower:
            # Find error details
            error_lines = [line for line in output.split('\n') if 'error' in line.lower()]
            feedback_lines.extend(error_lines[:3])  # First 3 error lines
        
        # Build feedback
        if success:
            feedback = f"✅ {feature.title} validated successfully"
            if test_results["passed"] > 0:
                feedback += f" ({test_results['passed']} tests passed)"
        else:
            feedback = f"❌ {feature.title} validation failed"
            if feedback_lines:
                feedback += ": " + "; ".join(feedback_lines)
            elif test_results["failed"] > 0:
                feedback += f" ({test_results['failed']} tests failed)"
        
        return ValidationResult(
            success=success,
            feedback=feedback,
            execution_details={
                "feature_id": feature.id,
                "files_created": list(new_files.keys()),
                "validation_criteria": feature.validation_criteria,
                "output_preview": output[:500]
            },
            files_validated=list(new_files.keys()),
            tests_passed=test_results["passed"] if test_results["passed"] > 0 else None,
            tests_failed=test_results["failed"] if test_results["failed"] > 0 else None
        )
    
    def _extract_relevant_tests(self, all_tests: str, feature: Feature) -> Optional[str]:
        """Extract tests relevant to the current feature"""
        # Simple heuristic: look for test files/classes that match feature files
        relevant_tests = []
        
        for file in feature.files:
            # Convert file to test pattern (e.g., user.py -> test_user)
            base_name = file.replace('.py', '').replace('/', '_')
            test_patterns = [
                f"test_{base_name}",
                f"Test{base_name.title()}",
                f"{base_name}_test"
            ]
            
            for pattern in test_patterns:
                if pattern in all_tests:
                    # Extract the test class or function
                    # This is simplified - real implementation would be more robust
                    start_idx = all_tests.find(pattern)
                    end_idx = all_tests.find("\nclass", start_idx + 1)
                    if end_idx == -1:
                        end_idx = all_tests.find("\ndef", start_idx + 1)
                    if end_idx == -1:
                        end_idx = len(all_tests)
                    
                    relevant_tests.append(all_tests[start_idx:end_idx])
        
        return "\n".join(relevant_tests) if relevant_tests else None
    
    def get_progress_summary(self) -> Dict[str, Any]:
        """Get current progress summary"""
        return {
            "validated_features": len(self.validated_features),
            "total_files": len(self.codebase_state),
            "feature_ids": self.validated_features,
            "session_id": self.session_id
        }


# Helper functions for workflow integration
# execute_features_incrementally moved to feature_orchestrator.py to avoid circular imports


# prepare_feature_context moved to feature_orchestrator.py to avoid circular imports


# parse_code_files moved to feature_orchestrator.py to avoid circular imports


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
