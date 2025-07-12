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
from workflows.incremental.error_analyzer import ErrorAnalyzer, ErrorContext
from workflows.incremental.validation_system import GranularValidator
from agents.executor.validation_debugger import ValidationDebugger


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
        self.error_analyzer = ErrorAnalyzer()
        self.granular_validator = GranularValidator()
        # Enable debugging for validation decisions
        self.validation_debugger = ValidationDebugger(session_id, debug_enabled=True)
    
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
        from orchestrator.orchestrator_agent import run_team_member
        
        # Update codebase state
        self.codebase_state.update(new_files)
        
        # Prepare executor input following ACP message format
        executor_input = self._prepare_executor_input(
            feature, 
            new_files, 
            existing_tests
        )
        
        # Record validation attempt if tracer is available
        validation_id = None
        if self.tracer:
            validation_id = self.tracer.start_step(
                step_name=f"validate_{feature.id}",
                agent_name="executor_agent",
                input_data={"feature": feature.id, "complexity": feature.complexity.value}
            )
        
        try:
            # Log validation attempt
            self.validation_debugger.log_validation_attempt(
                feature.id, 
                {"files": list(new_files.keys()), "validation_criteria": feature.validation_criteria}
            )
            
            # Run executor agent following ACP patterns
            result = await run_team_member("executor_agent", executor_input)
            execution_output = str(result)
            
            # Log executor output
            self.validation_debugger.log_executor_output(feature.id, execution_output)
            
            # Extract proof of execution details
            from agents.executor.proof_reader import extract_proof_from_executor_output
            proof_details = extract_proof_from_executor_output(execution_output, self.session_id)
            
            # Append proof details to execution output if found
            if proof_details and "No proof of execution found" not in proof_details:
                execution_output += f"\n\n{proof_details}"
            
            # Parse results
            validation_result = self._parse_validation_output(
                execution_output,
                feature,
                new_files
            )
            
            # Log final result
            self.validation_debugger.log_final_result(
                feature.id,
                validation_result.success,
                validation_result.feedback
            )
            
            # Update tracer
            if self.tracer and validation_id:
                self.tracer.complete_step(
                    step_id=validation_id,
                    output_data={
                        "success": validation_result.success,
                        "details": validation_result.execution_details
                    }
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
            
            if self.tracer and validation_id:
                self.tracer.complete_step(
                    step_id=validation_id,
                    output_data={
                        "success": False,
                        "details": error_result.execution_details
                    },
                    error=str(e)
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
        exit_code = None
        
        # First, check for explicit Docker execution markers
        if "✅ DOCKER EXECUTION RESULT" in output:
            # This is a successful Docker execution - check exit codes
            exit_code_match = re.search(r'Exit Code:\s*(\d+)', output)
            if exit_code_match:
                exit_code = int(exit_code_match.group(1))
                success = (exit_code == 0)
        elif "❌ DOCKER EXECUTION ERROR" in output:
            # This is a failed Docker execution
            success = False
            # Extract the specific error message
            error_match = re.search(r'Error:\s*(.+?)(?:\n|$)', output)
            if error_match:
                feedback_lines.append(error_match.group(1))
        else:
            # Fallback to general pattern matching
            # Check for explicit failure markers first
            explicit_failures = ["❌", "validation failed", "tests failed", "execution failed"]
            explicit_successes = ["✅", "validation passed", "all tests passed", "successfully validated"]
            
            output_lower = output.lower()
            
            # Check explicit markers
            has_explicit_failure = any(marker in output_lower for marker in explicit_failures)
            has_explicit_success = any(marker in output_lower for marker in explicit_successes)
            
            if has_explicit_failure:
                success = False
            elif has_explicit_success:
                success = True
            else:
                # No explicit markers - look for other indicators
                # Only treat as error if it's clearly an execution error
                if "traceback" in output_lower or "syntaxerror" in output_lower:
                    success = False
                elif "error" in output_lower:
                    # Check if error is in an actual error context
                    error_lines = [line for line in output.split('\n') 
                                 if 'error' in line.lower() and 
                                 any(ctx in line.lower() for ctx in ['failed', 'exception', 'traceback'])]
                    if error_lines:
                        success = False
                        feedback_lines.extend(error_lines[:3])
                else:
                    # Default to success if no clear failure indicators
                    success = True
        
        # Extract test results if present
        test_match = re.search(r'(\d+)\s+passed.*?(\d+)\s+failed', output, re.IGNORECASE)
        if test_match:
            test_results["passed"] = int(test_match.group(1))
            test_results["failed"] = int(test_match.group(2))
            # Test results override other success indicators
            success = test_results["failed"] == 0
        
        # Extract specific error details for feedback
        if not success and not feedback_lines:
            # Look for specific error patterns
            if "docker" in output.lower() and "timeout" in output.lower():
                feedback_lines.append("Docker connection timeout")
            elif "import" in output.lower() and "error" in output.lower():
                import_error = re.search(r'(ImportError|ModuleNotFoundError):\s*(.+)', output)
                if import_error:
                    feedback_lines.append(f"Import error: {import_error.group(2)}")
            elif "syntax" in output.lower() and "error" in output.lower():
                syntax_error = re.search(r'SyntaxError:\s*(.+)', output)
                if syntax_error:
                    feedback_lines.append(f"Syntax error: {syntax_error.group(1)}")
        
        # Build feedback message
        if success:
            feedback = f"✅ {feature.title} validated successfully"
            if test_results["passed"] > 0:
                feedback += f" ({test_results['passed']} tests passed)"
            if exit_code is not None:
                feedback += f" [Exit code: {exit_code}]"
        else:
            feedback = f"❌ {feature.title} validation failed"
            if feedback_lines:
                feedback += ": " + "; ".join(feedback_lines)
            elif test_results["failed"] > 0:
                feedback += f" ({test_results['failed']} tests failed)"
            if exit_code is not None and exit_code != 0:
                feedback += f" [Exit code: {exit_code}]"
        
        # Log parsing decision
        parsing_details = {
            "success_determined_by": "docker_marker" if "DOCKER EXECUTION" in output else "pattern_matching",
            "exit_code": exit_code,
            "test_results": test_results,
            "explicit_markers_found": {
                "success": "✅" in output,
                "failure": "❌" in output,
                "docker_success": "✅ DOCKER EXECUTION RESULT" in output,
                "docker_error": "❌ DOCKER EXECUTION ERROR" in output
            },
            "final_decision": success,
            "feedback_lines": feedback_lines
        }
        
        # Log to validation debugger
        if hasattr(self, 'validation_debugger'):
            self.validation_debugger.log_parsing_decision(feature.id, parsing_details)
        
        # Add debug logging to tracer
        if hasattr(self, 'tracer') and self.tracer:
            self.tracer.add_metadata(f"validation_parse_{feature.id}", parsing_details)
        
        return ValidationResult(
            success=success,
            feedback=feedback,
            execution_details={
                "feature_id": feature.id,
                "files_created": list(new_files.keys()),
                "validation_criteria": feature.validation_criteria,
                "output_preview": output[:500],
                "exit_code": exit_code
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
        # Save validation debug log
        if hasattr(self, 'validation_debugger'):
            self.validation_debugger.save_debug_log()
            self.validation_debugger.print_summary()
        
        return {
            "validated_features": len(self.validated_features),
            "total_files": len(self.codebase_state),
            "feature_ids": self.validated_features,
            "session_id": self.session_id,
            "validation_debug_report": self.validation_debugger.get_validation_report() if hasattr(self, 'validation_debugger') else None
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
