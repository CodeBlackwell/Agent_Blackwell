"""Test Writer Agent for RED phase - Writes failing tests based on requirements"""

import asyncio
from typing import AsyncGenerator, Dict, Any
import json

from models.flagship_models import (
    AgentType, TDDPhase, AgentMessage, PhaseResult, TestStatus, TestResult
)


class TestWriterFlagship:
    """Agent responsible for writing failing tests in the RED phase"""
    
    def __init__(self, file_manager=None):
        self.agent_type = AgentType.TEST_WRITER
        self.phase = TDDPhase.RED
        self.file_manager = file_manager
    
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
        
        # Check for existing tests if file manager is available
        if self.file_manager:
            file_context = self.file_manager.get_file_context("test_writer")
            existing_tests = file_context.get("existing_tests", [])
            if existing_tests:
                yield f"📁 Found {len(existing_tests)} existing test file(s)\n"
                # Read and analyze existing tests
                for test_file in existing_tests[:3]:  # Limit to first 3 files
                    content = self.file_manager.read_file(test_file)
                    if content:
                        yield f"  - {test_file}: {len(content.splitlines())} lines\n"
        
        # Analyze requirements
        test_plan = self._analyze_requirements(requirements)
        yield f"\nTest Plan:\n{self._format_test_plan(test_plan)}\n"
        
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
        
        # Save test code to file manager if available
        if self.file_manager:
            self.file_manager.write_file("test_generated.py", test_code)
            yield "\n✅ Test code saved to session directory"
    
    def _analyze_requirements(self, requirements: str) -> Dict[str, Any]:
        """Analyze requirements to determine what tests to write"""
        import re
        
        test_plan = {
            "test_categories": [],
            "test_count": 0,
            "edge_cases": [],
            "classes": [],
            "methods": [],
            "properties": [],
            "validations": []
        }
        
        requirements_lower = requirements.lower()
        
        # Extract class names
        class_pattern = r'\b(?:class|create\s+a|create\s+an?)\s+(\w+)'
        class_matches = re.findall(class_pattern, requirements, re.IGNORECASE)
        # Filter out common words that aren't class names
        exclude_words = {'with', 'and', 'or', 'the', 'a', 'an', 'to', 'for', 'of', 'in', 'on', 'at'}
        test_plan["classes"] = [match.capitalize() for match in class_matches if match.lower() not in exclude_words]
        
        # Extract properties/attributes
        prop_patterns = [
            r'with\s+([\w\s,]+?)\s+(?:property|properties|attribute|attributes)',
            r'(\w+)\s+(?:property|properties|attribute|attributes)',
            r'(?:property|properties|attribute|attributes):\s*([\w\s,]+)'
        ]
        for pattern in prop_patterns:
            matches = re.findall(pattern, requirements, re.IGNORECASE)
            for match in matches:
                if isinstance(match, str):
                    # Handle "name and age" pattern
                    props = re.split(r'\s+and\s+|\s*,\s*', match)
                    props = [p.strip() for p in props if p.strip() and p.strip() not in exclude_words]
                    test_plan["properties"].extend(props)
        
        # Extract methods
        method_patterns = [
            r'(?:method|methods|function|functions)\s+(?:for|to|that)?\s*(\w+)',
            r'(\w+)\s+method',
            r'include\s+(\w+)\s+method'
        ]
        for pattern in method_patterns:
            matches = re.findall(pattern, requirements, re.IGNORECASE)
            test_plan["methods"].extend(matches)
        
        # Extract validation rules
        if "must be" in requirements_lower or "should be" in requirements_lower:
            validation_pattern = r'(\w+)\s+(?:must|should)\s+be\s+([^.]+)'
            validations = re.findall(validation_pattern, requirements, re.IGNORECASE)
            test_plan["validations"] = validations
        
        # Determine test categories based on requirements
        if test_plan["classes"]:
            test_plan["test_categories"].append("class_instantiation")
        if test_plan["properties"]:
            test_plan["test_categories"].append("property_access")
        if test_plan["methods"]:
            test_plan["test_categories"].append("method_functionality")
        if test_plan["validations"]:
            test_plan["test_categories"].append("validation")
            test_plan["edge_cases"].append("invalid inputs")
        
        # Add common edge cases
        if "age" in requirements_lower:
            test_plan["edge_cases"].extend(["negative age", "age over limit"])
        if "name" in requirements_lower:
            test_plan["edge_cases"].extend(["empty name", "name with special characters"])
        
        # Calculate test count
        test_plan["test_count"] = len(test_plan["test_categories"]) * 2 + len(test_plan["edge_cases"])
        
        return test_plan
    
    def _format_test_plan(self, test_plan: Dict[str, Any]) -> str:
        """Format the test plan for display"""
        lines = []
        if test_plan.get('classes'):
            lines.append(f"- Classes: {', '.join(test_plan['classes'])}")
        if test_plan.get('properties'):
            lines.append(f"- Properties: {', '.join(test_plan['properties'])}")
        if test_plan.get('methods'):
            lines.append(f"- Methods: {', '.join(test_plan['methods'])}")
        lines.append(f"- Test Categories: {', '.join(test_plan['test_categories'])}")
        lines.append(f"- Number of Tests: {test_plan['test_count']}")
        lines.append(f"- Edge Cases: {', '.join(test_plan['edge_cases'])}")
        return '\n'.join(lines)
    
    def _generate_test_code(self, requirements: str, test_plan: Dict[str, Any]) -> str:
        """Generate actual test code based on requirements"""
        # Check for specific known patterns first
        if "calculator" in requirements.lower() and not test_plan.get('classes'):
            return self._generate_calculator_tests()
        elif "greet" in requirements.lower() and not test_plan.get('classes'):
            return self._generate_greet_tests()
        elif test_plan.get('classes') or test_plan.get('methods') or test_plan.get('properties'):
            # Use the analyzed test plan to generate appropriate tests
            return self._generate_tests_from_plan(requirements, test_plan)
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
    
    def _generate_tests_from_plan(self, requirements: str, test_plan: Dict[str, Any]) -> str:
        """Generate tests based on the analyzed test plan"""
        imports = ["import pytest"]
        
        # Determine what to import
        if test_plan['classes']:
            class_name = test_plan['classes'][0]
            # Create a module name from class name (Person -> person)
            module_name = class_name.lower()
            imports.append(f"from {module_name} import {class_name}")
        else:
            imports.append("from main import *")
        
        test_code = '\n'.join(imports) + '\n\n\n'
        
        # Generate test class for each main class
        for class_name in test_plan['classes']:
            test_code += f'class Test{class_name}:\n'
            test_code += f'    """Test suite for {class_name} class"""\n\n'
            
            # Removed setup_method generation as it was creating instances without required arguments
            # Each test method creates its own instances with proper parameters
            
            # Test instantiation
            test_code += '    def test_instantiation(self):\n'
            test_code += f'        """Test {class_name} instantiation"""\n'
            
            # Generate constructor based on properties
            if 'name' in test_plan['properties'] and 'age' in test_plan['properties']:
                test_code += f'        person = {class_name}("John Doe", 30)\n'
                test_code += '        assert person is not None\n'
                test_code += '        assert isinstance(person, ' + class_name + ')\n\n'
            else:
                test_code += f'        obj = {class_name}()\n'
                test_code += '        assert obj is not None\n\n'
            
            # Test properties with getters
            for prop in test_plan['properties']:
                if prop and prop.lower() not in ['and', 'or', '']:  # Filter out parsing artifacts
                    test_code += f'    def test_{prop.lower()}_property(self):\n'
                    test_code += f'        """Test {prop} property and getter"""\n'
                    
                    if prop.lower() == 'name':
                        test_code += f'        person = {class_name}("Alice Smith", 25)\n'
                        test_code += '        assert person.get_name() == "Alice Smith"\n'
                        test_code += '        assert person.name == "Alice Smith"\n\n'
                    elif prop.lower() == 'age':
                        test_code += f'        person = {class_name}("Bob Jones", 45)\n'
                        test_code += '        assert person.get_age() == 45\n'
                        test_code += '        assert person.age == 45\n\n'
                    else:
                        test_code += f'        # Test for {prop} property\n'
                        test_code += f'        obj = {class_name}()\n'
                        test_code += f'        assert hasattr(obj, "{prop}")\n\n'
            
            # Test validations
            if test_plan['validations']:
                test_code += '    def test_validations(self):\n'
                test_code += '        """Test input validations"""\n'
                
                for field, rule in test_plan['validations']:
                    if 'name' in field.lower() and 'empty' in rule:
                        test_code += '        # Name must not be empty\n'
                        test_code += '        with pytest.raises(ValueError, match="Name cannot be empty"):\n'
                        test_code += f'            {class_name}("", 30)\n'
                    if 'age' in field.lower() and 'positive' in rule:
                        test_code += '        # Age must be positive\n'
                        test_code += '        with pytest.raises(ValueError, match="Age must be positive"):\n'
                        test_code += f'            {class_name}("John", -5)\n'
                
                test_code += '\n'
            
            # Edge cases
            if 'age' in [p.lower() for p in test_plan['properties']]:
                test_code += '    def test_age_boundaries(self):\n'
                test_code += '        """Test age boundary conditions"""\n'
                test_code += '        # Test minimum age\n'
                test_code += f'        person = {class_name}("Young", 0)\n'
                test_code += '        assert person.get_age() == 0\n'
                test_code += '        \n'
                test_code += '        # Test maximum age\n'
                test_code += f'        person = {class_name}("Old", 150)\n'
                test_code += '        assert person.get_age() == 150\n'
                test_code += '        \n'
                test_code += '        # Test over limit\n'
                test_code += '        with pytest.raises(ValueError, match="Age must be between 0 and 150"):\n'
                test_code += f'            {class_name}("TooOld", 151)\n\n'
            
            if 'name' in [p.lower() for p in test_plan['properties']]:
                test_code += '    def test_name_edge_cases(self):\n'
                test_code += '        """Test name edge cases"""\n'
                test_code += '        # Test with special characters\n'
                test_code += f'        person = {class_name}("José García-López", 30)\n'
                test_code += '        assert person.get_name() == "José García-López"\n'
                test_code += '        \n'
                test_code += '        # Test with unicode\n'
                test_code += f'        person = {class_name}("李明", 25)\n'
                test_code += '        assert person.get_name() == "李明"\n'
        
        return test_code.rstrip()
    
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