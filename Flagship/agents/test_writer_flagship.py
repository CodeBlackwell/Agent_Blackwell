"""Test Writer Agent for RED phase - Writes failing tests based on requirements"""

import asyncio
from typing import AsyncGenerator, Dict, Any
import json

from models.flagship_models import (
    AgentType, TDDPhase, AgentMessage, PhaseResult, TestStatus, TestResult
)


class TestWriterFlagship:
    """Agent responsible for writing failing tests in the RED phase"""
    
    def __init__(self):
        self.agent_type = AgentType.TEST_WRITER
        self.phase = TDDPhase.RED
    
    async def write_tests(self, requirements: str, context: Dict[str, Any] = None) -> AsyncGenerator[str, None]:
        """
        Write failing tests based on requirements
        
        Args:
            requirements: The requirements to write tests for
            context: Additional context (previous iterations, etc.)
            
        Yields:
            Test code chunks as they're generated
        """
        yield f"🔴 RED Phase: Writing failing tests for requirements...\n"
        yield f"Requirements: {requirements}\n\n"
        
        # Analyze requirements
        test_plan = self._analyze_requirements(requirements)
        yield f"Test Plan:\n{self._format_test_plan(test_plan)}\n"
        
        # Generate test code
        test_code = self._generate_test_code(requirements, test_plan)
        
        # Yield test code in chunks for streaming
        yield "Generated Test Code:\n"
        yield "```python\n"
        for line in test_code.split('\n'):
            yield line + '\n'
            await asyncio.sleep(0.01)  # Small delay for streaming effect
        yield "```\n"
        
        # Store the test code in the result
        self._test_code = test_code
    
    def _analyze_requirements(self, requirements: str) -> Dict[str, Any]:
        """Analyze requirements to determine what tests to write"""
        # Simple analysis for the MVP
        # In a real system, this would use NLP or more sophisticated parsing
        
        test_plan = {
            "test_categories": [],
            "test_count": 0,
            "edge_cases": []
        }
        
        # Basic heuristics
        requirements_lower = requirements.lower()
        
        if "calculator" in requirements_lower:
            test_plan["test_categories"] = ["basic_operations", "edge_cases", "error_handling"]
            test_plan["test_count"] = 8
            test_plan["edge_cases"] = ["division by zero", "invalid input types"]
        elif "api" in requirements_lower:
            test_plan["test_categories"] = ["endpoints", "validation", "error_responses"]
            test_plan["test_count"] = 10
            test_plan["edge_cases"] = ["missing parameters", "invalid data"]
        else:
            # Generic test plan
            test_plan["test_categories"] = ["basic_functionality", "edge_cases"]
            test_plan["test_count"] = 5
            test_plan["edge_cases"] = ["null inputs", "boundary conditions"]
        
        return test_plan
    
    def _format_test_plan(self, test_plan: Dict[str, Any]) -> str:
        """Format the test plan for display"""
        lines = []
        lines.append(f"- Test Categories: {', '.join(test_plan['test_categories'])}")
        lines.append(f"- Number of Tests: {test_plan['test_count']}")
        lines.append(f"- Edge Cases: {', '.join(test_plan['edge_cases'])}")
        return '\n'.join(lines)
    
    def _generate_test_code(self, requirements: str, test_plan: Dict[str, Any]) -> str:
        """Generate actual test code based on requirements"""
        # For the MVP, we'll generate calculator tests as the default example
        if "calculator" in requirements.lower():
            return self._generate_calculator_tests()
        elif "greet" in requirements.lower():
            return self._generate_greet_tests()
        else:
            return self._generate_generic_tests(requirements)
    
    def _generate_calculator_tests(self) -> str:
        """Generate failing tests for a calculator"""
        return '''import pytest
from calculator import Calculator


class TestCalculator:
    """Test suite for Calculator class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.calc = Calculator()
    
    def test_addition(self):
        """Test addition operation"""
        assert self.calc.add(2, 3) == 5
        assert self.calc.add(-1, 1) == 0
        assert self.calc.add(0, 0) == 0
    
    def test_subtraction(self):
        """Test subtraction operation"""
        assert self.calc.subtract(5, 3) == 2
        assert self.calc.subtract(0, 5) == -5
        assert self.calc.subtract(-3, -3) == 0
    
    def test_multiplication(self):
        """Test multiplication operation"""
        assert self.calc.multiply(3, 4) == 12
        assert self.calc.multiply(-2, 3) == -6
        assert self.calc.multiply(0, 100) == 0
    
    def test_division(self):
        """Test division operation"""
        assert self.calc.divide(10, 2) == 5
        assert self.calc.divide(7, 2) == 3.5
        assert self.calc.divide(-10, 2) == -5
    
    def test_division_by_zero(self):
        """Test division by zero raises exception"""
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            self.calc.divide(10, 0)
    
    def test_invalid_input_types(self):
        """Test that invalid input types raise TypeError"""
        with pytest.raises(TypeError):
            self.calc.add("2", 3)
        
        with pytest.raises(TypeError):
            self.calc.multiply(2, [3])
    
    def test_large_numbers(self):
        """Test operations with large numbers"""
        large_num = 10**10
        assert self.calc.add(large_num, large_num) == 2 * large_num
        assert self.calc.multiply(large_num, 0) == 0
    
    def test_float_precision(self):
        """Test floating point operations"""
        result = self.calc.add(0.1, 0.2)
        assert abs(result - 0.3) < 1e-10  # Account for floating point precision'''
    
    def _generate_greet_tests(self) -> str:
        """Generate failing tests for greet function"""
        return '''import pytest
from greet import greet


class TestGreet:
    """Test suite for greet function"""
    
    def test_basic_greeting(self):
        """Test basic greeting functionality"""
        assert greet("Alice") == "Hello, Alice!"
        assert greet("Bob") == "Hello, Bob!"
    
    def test_greeting_with_spaces(self):
        """Test greeting with names containing spaces"""
        assert greet("Mary Jane") == "Hello, Mary Jane!"
    
    def test_empty_name(self):
        """Test greeting with empty string"""
        assert greet("") == "Hello, !"
    
    def test_special_characters(self):
        """Test greeting with special characters"""
        assert greet("José") == "Hello, José!"
        assert greet("李明") == "Hello, 李明!"
    
    def test_long_name(self):
        """Test greeting with very long name"""
        long_name = "A" * 100
        assert greet(long_name) == f"Hello, {long_name}!"'''
    
    def _generate_generic_tests(self, requirements: str) -> str:
        """Generate generic failing tests based on requirements"""
        # Extract a simple function name from requirements
        func_name = "process" if "process" in requirements.lower() else "execute"
        
        return f'''import pytest
from main import {func_name}


class Test{func_name.capitalize()}:
    """Test suite for {func_name} function"""
    
    def test_basic_functionality(self):
        """Test basic {func_name} functionality"""
        result = {func_name}("test input")
        assert result is not None
        assert isinstance(result, str)
    
    def test_empty_input(self):
        """Test {func_name} with empty input"""
        result = {func_name}("")
        assert result == "empty"
    
    def test_none_input(self):
        """Test {func_name} with None input"""
        with pytest.raises(ValueError, match="Input cannot be None"):
            {func_name}(None)
    
    def test_special_characters(self):
        """Test {func_name} with special characters"""
        result = {func_name}("!@#$%")
        assert result == "special"
    
    def test_performance(self):
        """Test {func_name} performance with large input"""
        large_input = "x" * 10000
        result = {func_name}(large_input)
        assert len(result) < len(large_input)  # Should process/compress somehow'''
    
    def get_test_code(self) -> str:
        """Get the generated test code"""
        return getattr(self, '_test_code', '')
    
    def create_phase_result(self, success: bool = True, error: str = None) -> PhaseResult:
        """Create a PhaseResult for this agent's execution"""
        # Create test results showing all tests as "NOT_RUN" in RED phase
        test_code = self.get_test_code()
        test_results = []
        
        # Parse test names from the code (simple approach)
        for line in test_code.split('\n'):
            if line.strip().startswith('def test_'):
                test_name = line.strip().split('(')[0].replace('def ', '')
                test_results.append(TestResult(
                    test_name=test_name,
                    status=TestStatus.NOT_RUN,
                    error_message="Test not yet executed (RED phase)"
                ))
        
        return PhaseResult(
            phase=self.phase,
            success=success,
            agent=self.agent_type,
            output=test_code,
            test_results=test_results,
            error=error,
            metadata={
                "test_count": len(test_results),
                "test_framework": "pytest"
            }
        )