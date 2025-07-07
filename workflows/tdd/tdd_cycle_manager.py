"""
TDD Cycle Manager
Implements proper Test-Driven Development cycle with red-green-refactor phases
"""
import asyncio
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from workflows.logger import workflow_logger as logger
from workflows.tdd.file_manager import TDDFileManager


class TDDPhase(Enum):
    """TDD cycle phases"""
    RED = "red"  # Write failing tests
    GREEN = "green"  # Make tests pass
    REFACTOR = "refactor"  # Improve code quality


@dataclass
class TestExecutionResult:
    """Result from running tests"""
    phase: TDDPhase
    success: bool
    total_tests: int
    passed_tests: int
    failed_tests: int
    error_messages: List[str]
    output: str
    coverage_percent: Optional[float] = None
    
    @property
    def all_passing(self) -> bool:
        """Check if all tests are passing"""
        return self.failed_tests == 0 and self.total_tests > 0


@dataclass
class TDDCycleResult:
    """Result of complete TDD cycle"""
    test_code: str
    implementation_code: str
    initial_test_result: TestExecutionResult  # Red phase
    final_test_result: TestExecutionResult   # Green phase
    refactored: bool = False
    iterations: int = 0
    success: bool = False


class TDDCycleManager:
    """Manages the TDD red-green-refactor cycle"""
    
    def __init__(self, max_iterations: int = 5, require_test_failure: bool = True):
        self.max_iterations = max_iterations
        self.require_test_failure = require_test_failure
        self.file_manager = TDDFileManager()
        
    async def execute_tdd_cycle(
        self,
        requirements: str,
        test_code: str,
        existing_code: Dict[str, str] = None
    ) -> TDDCycleResult:
        """
        Execute complete TDD cycle for given requirements and tests
        
        Args:
            requirements: Feature requirements
            test_code: Test code written by test_writer_agent
            existing_code: Any existing code files
            
        Returns:
            TDDCycleResult with all cycle information
        """
        existing_code = existing_code or {}
        
        # Parse test files using file manager
        test_files = self.file_manager.parse_files(test_code, extract_location=False)
        logger.info(f"Parsed {len(test_files)} test files")
        
        # Phase 1: RED - Run tests, expect failure
        logger.info("🔴 TDD RED Phase: Running tests (expecting failure)...")
        initial_result = await self._execute_tests(
            test_code, 
            existing_code,
            phase=TDDPhase.RED
        )
        
        # Validate that tests actually fail
        if initial_result.all_passing and self.require_test_failure:
            logger.warning("⚠️  Tests are passing without implementation! Tests may be invalid.")
            # Add a synthetic failure to ensure we go through the cycle
            initial_result.error_messages.append(
                "Tests passed without implementation - possible test issue"
            )
        
        # Phase 2: GREEN - Implement code to make tests pass
        logger.info("🟢 TDD GREEN Phase: Implementing code to pass tests...")
        implementation_code = ""
        final_result = initial_result
        iterations = 0
        
        while not final_result.all_passing and iterations < self.max_iterations:
            iterations += 1
            logger.info(f"  Iteration {iterations}/{self.max_iterations}")
            
            # Generate implementation based on test failures
            implementation_code = await self._implement_for_tests(
                requirements,
                test_code,
                initial_result if iterations == 1 else final_result,
                existing_code,
                implementation_code,
                iteration=iterations
            )
            
            # Parse implementation files and extract project location
            impl_files = self.file_manager.parse_files(implementation_code, extract_location=True)
            
            # Merge implementation with existing code
            updated_code = existing_code.copy()
            updated_code.update(impl_files)
            
            # Update files in project if we have a location
            if self.file_manager.current_project:
                self.file_manager.update_files_in_project(impl_files)
            
            # Run tests again
            final_result = await self._execute_tests(
                test_code,
                updated_code,
                phase=TDDPhase.GREEN
            )
            
            if final_result.all_passing:
                logger.info(f"✅ All tests passing after {iterations} iteration(s)!")
                break
        
        # Phase 3: REFACTOR (optional)
        refactored = False
        if final_result.all_passing and self._should_refactor(implementation_code):
            logger.info("🔄 TDD REFACTOR Phase: Improving code quality...")
            # In a full implementation, this would call a refactoring agent
            # For now, we'll skip actual refactoring
            refactored = False
        
        # Create result
        return TDDCycleResult(
            test_code=test_code,
            implementation_code=implementation_code,
            initial_test_result=initial_result,
            final_test_result=final_result,
            refactored=refactored,
            iterations=iterations,
            success=final_result.all_passing
        )
    
    async def _execute_tests(
        self,
        test_code: str,
        implementation_code: Dict[str, str],
        phase: TDDPhase
    ) -> TestExecutionResult:
        """Execute tests and return results"""
        from workflows.tdd.test_executor import TestExecutor
        
        # Detect language from test code or implementation
        language = self._detect_language(test_code, implementation_code)
        
        # Use real test executor
        test_executor = TestExecutor(use_docker=False, timeout=30)
        
        # Get project directory from file manager based on config
        from workflows.tdd.tdd_config import TEST_CONFIG
        use_project = TEST_CONFIG.get("use_generated_directory", True) and TEST_CONFIG.get("test_isolation_mode", "project") == "project"
        project_dir = self.file_manager.get_test_directory(use_project_dir=use_project)
        
        try:
            # Execute actual tests
            result = await test_executor.execute_tests(
                test_code=test_code,
                implementation_code=implementation_code,
                phase=phase,
                language=language,
                project_directory=project_dir
            )
            
            # Log the results
            logger.info(f"Test execution results: {result.passed_tests}/{result.total_tests} passed")
            if result.error_messages:
                logger.info(f"Test failures: {result.error_messages[:3]}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing tests: {str(e)}")
            
            # Fallback to simulation if real execution fails
            test_count = self._count_tests(test_code)
            
            if phase == TDDPhase.RED and not implementation_code:
                # Tests should fail in RED phase without implementation
                return TestExecutionResult(
                    phase=phase,
                    success=False,
                    total_tests=test_count,
                    passed_tests=0,
                    failed_tests=test_count,
                    error_messages=[
                        f"Test execution error: {str(e)}",
                        "Tests failed as expected - no implementation found"
                    ],
                    output=f"Test execution failed: {str(e)}"
                )
            else:
                # Return error result
                return TestExecutionResult(
                    phase=phase,
                    success=False,
                    total_tests=test_count,
                    passed_tests=0,
                    failed_tests=test_count,
                    error_messages=[f"Test execution error: {str(e)}"],
                    output=f"Test execution failed: {str(e)}"
                )
    
    async def _implement_for_tests(
        self,
        requirements: str,
        test_code: str,
        test_result: TestExecutionResult,
        existing_code: Dict[str, str],
        previous_implementation: str,
        iteration: int
    ) -> str:
        """Generate implementation to make failing tests pass"""
        # Import here to avoid circular dependency
        from orchestrator.orchestrator_agent import run_team_member_with_tracking
        
        context = self._create_implementation_context(
            requirements,
            test_code,
            test_result,
            existing_code,
            previous_implementation,
            iteration
        )
        
        # Call coder agent with TDD-specific context
        logger.info(f"Calling coder agent for TDD iteration {iteration}")
        
        try:
            result = await run_team_member_with_tracking(
                "coder_agent", 
                context, 
                f"tdd_green_{iteration}"
            )
            
            implementation = str(result)
            logger.info(f"Received implementation from coder agent")
            
            return implementation
            
        except Exception as e:
            logger.error(f"Error calling coder agent: {str(e)}")
            # Return a minimal implementation attempt based on test failures
            return self._generate_minimal_implementation(test_code, test_result)
    
    def _create_implementation_context(
        self,
        requirements: str,
        test_code: str,
        test_result: TestExecutionResult,
        existing_code: Dict[str, str],
        previous_implementation: str,
        iteration: int
    ) -> str:
        """Create context for coder agent focused on making tests pass"""
        
        # Determine language for syntax hints
        language = self._detect_language(test_code, existing_code)
        
        context = f"""
You are implementing code using Test-Driven Development (TDD).
Your ONLY goal is to make the failing tests pass with minimal code.

PROGRAMMING LANGUAGE: {language}

REQUIREMENTS:
{requirements}

FAILING TESTS:
{test_code}

TEST EXECUTION RESULTS:
- Total tests: {test_result.total_tests}
- Passed: {test_result.passed_tests}
- Failed: {test_result.failed_tests}

SPECIFIC TEST FAILURES:
{self._format_test_failures(test_result)}

TEST OUTPUT:
{test_result.output[-1000:] if test_result.output else "No output available"}
"""
        
        if iteration > 1 and previous_implementation:
            context += f"""

PREVIOUS IMPLEMENTATION (Iteration {iteration-1}):
This code still has {test_result.failed_tests} failing tests. Fix the specific issues identified above.
{previous_implementation}
"""
        
        if existing_code:
            context += f"""

EXISTING CODE FILES:
{self._format_existing_code(existing_code)}
"""
        
        # Add project directory context to prevent new directory creation
        if self.file_manager.current_project:
            context += f"""

CRITICAL PROJECT INFORMATION:
📁 EXISTING PROJECT LOCATION: {self.file_manager.current_project.project_path}
📝 PROJECT NAME: {self.file_manager.current_project.project_name}

EXISTING PROJECT FILES:
{', '.join(self.file_manager.list_project_files())}

IMPORTANT INSTRUCTIONS:
1. DO NOT create a new project directory
2. DO NOT use timestamps in filenames or project names
3. UPDATE the existing files in the project location above
4. When generating code, use the SAME filenames as before
5. This is iteration {iteration} of the TDD cycle - continue working in the same project

Location: {self.file_manager.current_project.project_path}
"""
        
        context += f"""

TDD IMPLEMENTATION RULES:
1. Write ONLY the code needed to make the failing tests pass
2. Do NOT add features not required by the tests
3. Focus on the SPECIFIC test failures listed above
4. Keep implementation simple and direct
5. All test assertions must be satisfied
6. Use proper {language} syntax and conventions
7. Include proper error handling for edge cases shown in tests

IMPORTANT: Your implementation must make ALL {test_result.failed_tests} failing tests pass.
Generate the minimal implementation needed to achieve this.
"""
        return context
    
    def _format_test_failures(self, result: TestExecutionResult) -> str:
        """Format test failure information"""
        if not result.error_messages:
            return "No specific failure information available"
        
        formatted = []
        for i, error in enumerate(result.error_messages[:5], 1):
            formatted.append(f"{i}. {error}")
        
        if len(result.error_messages) > 5:
            formatted.append(f"... and {len(result.error_messages) - 5} more failures")
        
        return "\n".join(formatted)
    
    def _format_existing_code(self, code_dict: Dict[str, str]) -> str:
        """Format existing code for context"""
        if not code_dict:
            return "No existing code"
        
        formatted = []
        for filename, content in list(code_dict.items())[:3]:
            lines = content.split('\n')[:20]
            formatted.append(f"=== {filename} ===\n" + "\n".join(lines))
        
        return "\n\n".join(formatted)
    
    def _count_tests(self, test_code: str) -> int:
        """Count number of test functions in code"""
        # Simple heuristic: count test_ functions
        import re
        test_pattern = r'def test_\w+\s*\('
        matches = re.findall(test_pattern, test_code)
        return len(matches) if matches else 1
    
    
    def _should_refactor(self, code: str) -> bool:
        """Determine if refactoring is warranted"""
        # Simple heuristics
        lines = code.split('\n')
        
        # Check for code smells
        if len(lines) > 200:  # Large file
            return True
        if code.count('if') > 15:  # Complex conditionals
            return True
        if 'TODO' in code or 'FIXME' in code:
            return True
        
        return False
    
    def _detect_language(self, test_code: str, implementation_code: Dict[str, str]) -> str:
        """Detect programming language from code"""
        # Check file extensions in implementation
        for filename in implementation_code.keys():
            if filename.endswith('.py'):
                return 'python'
            elif filename.endswith(('.js', '.jsx')):
                return 'javascript'
            elif filename.endswith(('.ts', '.tsx')):
                return 'typescript'
            elif filename.endswith('.java'):
                return 'java'
            elif filename.endswith('.rb'):
                return 'ruby'
            elif filename.endswith('.go'):
                return 'go'
        
        # Check test code patterns
        if 'import pytest' in test_code or 'def test_' in test_code:
            return 'python'
        elif 'describe(' in test_code or 'it(' in test_code or 'test(' in test_code:
            return 'javascript'
        elif '@Test' in test_code or 'import org.junit' in test_code:
            return 'java'
        elif 'require "rspec"' in test_code or 'RSpec.describe' in test_code:
            return 'ruby'
        elif 'func Test' in test_code:
            return 'go'
        
        # Default to python
        return 'python'
    
    def _generate_minimal_implementation(self, test_code: str, test_result: TestExecutionResult) -> str:
        """Generate minimal implementation based on test failures"""
        # This is a fallback when coder agent fails
        # It creates a basic structure based on test patterns
        
        language = self._detect_language(test_code, {})
        
        if language == 'python':
            # Look for class and method names in test code
            import re
            
            # Find tested class names
            class_matches = re.findall(r'(\w+)\(', test_code)
            # Find tested methods
            method_matches = re.findall(r'\.(\w+)\(', test_code)
            
            if class_matches:
                class_name = class_matches[0]
                return f"""
# filename: {class_name.lower()}.py
class {class_name}:
    def __init__(self):
        pass
    
{chr(10).join(f'    def {method}(self, *args, **kwargs):{chr(10)}        raise NotImplementedError("Method {method} not implemented")' for method in set(method_matches) if method not in ['assertEqual', 'assertTrue', 'assertFalse', 'assertRaises'])}
"""
        
        # Default minimal implementation
        return """
# filename: implementation.py
# Minimal implementation - please implement based on test requirements
def main():
    raise NotImplementedError("Implementation needed based on test failures")
"""


# Integration helper
async def run_tdd_cycle(
    requirements: str,
    test_code: str,
    existing_code: Dict[str, str] = None,
    max_iterations: int = 5
) -> TDDCycleResult:
    """Helper function to run TDD cycle"""
    manager = TDDCycleManager(max_iterations=max_iterations)
    return await manager.execute_tdd_cycle(requirements, test_code, existing_code)