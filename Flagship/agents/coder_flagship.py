"""Coder Agent for YELLOW phase - Writes minimal code to pass tests"""

import asyncio
import re
from typing import AsyncGenerator, Dict, Any, List, Tuple

from models.flagship_models import (
    AgentType, TDDPhase, AgentMessage, PhaseResult, TestResult
)


class CoderFlagship:
    """Agent responsible for writing minimal code to pass tests in the YELLOW phase"""
    
    def __init__(self, file_manager=None):
        self.agent_type = AgentType.CODER
        self.phase = TDDPhase.YELLOW
        self.file_manager = file_manager
    
    async def write_code(self, test_code: str, test_results: List[TestResult], 
                        context: Dict[str, Any] = None) -> AsyncGenerator[str, None]:
        """
        Write minimal code to make failing tests pass
        
        Args:
            test_code: The test code to make pass
            test_results: Results from running the tests
            context: Additional context (previous iterations, etc.)
            
        Yields:
            Implementation code chunks as they're generated
        """
        yield f"🟡 YELLOW Phase: Writing minimal code to pass tests...\n"
        
        # Check for existing implementation if file manager is available
        if self.file_manager:
            file_context = self.file_manager.get_file_context("coder")
            test_files = file_context.get("test_files", [])
            impl_files = file_context.get("implementation_files", [])
            
            if test_files:
                yield f"📁 Found {len(test_files)} test file(s)\n"
                # Read test file if not provided
                if not test_code and test_files:
                    test_code = self.file_manager.read_file(test_files[0]) or test_code
                    
            if impl_files:
                yield f"📁 Found {len(impl_files)} existing implementation file(s)\n"
                # Read and analyze existing implementations
                for impl_file in impl_files[:2]:  # Limit to first 2 files
                    content = self.file_manager.read_file(impl_file)
                    if content:
                        yield f"  - {impl_file}: {len(content.splitlines())} lines\n"
                        # Could analyze existing code here to build upon it
        
        # Analyze failing tests
        failing_tests = [t for t in test_results if t.status.name in ['FAILED', 'ERROR']]
        yield f"\nFound {len(failing_tests)} failing tests to fix\n\n"
        
        # Extract requirements from test code
        requirements = self._extract_requirements_from_tests(test_code)
        yield f"Extracted Requirements:\n{self._format_requirements(requirements)}\n"
        
        # Generate implementation code
        implementation_code = self._generate_implementation(test_code, failing_tests, requirements)
        
        # Yield implementation code in chunks
        yield "Generated Implementation:\n"
        yield "```python\n"
        for line in implementation_code.split('\n'):
            yield line + '\n'
            await asyncio.sleep(0.01)  # Small delay for streaming effect
        yield "```\n"
        
        # Store the implementation code
        self._implementation_code = implementation_code
        
        # Save implementation code to file manager if available
        if self.file_manager:
            self.file_manager.write_file("implementation_generated.py", implementation_code)
            yield "\n✅ Implementation code saved to session directory"
    
    def _extract_requirements_from_tests(self, test_code: str) -> Dict[str, Any]:
        """Extract implementation requirements from test code"""
        requirements = {
            "imports": set(),
            "classes": set(),
            "methods": [],
            "error_handling": []
        }
        
        # Parse imports
        import_pattern = r'from\s+(\w+)\s+import\s+(\w+)'
        for match in re.finditer(import_pattern, test_code):
            module, item = match.groups()
            if module not in ['pytest', 'unittest']:  # Skip test framework imports
                requirements["imports"].add((module, item))
                requirements["classes"].add(item)
        
        # Parse test methods to understand required functionality
        method_pattern = r'def\s+test_(\w+).*?(?=def\s+test_|\Z)'
        for match in re.finditer(method_pattern, test_code, re.DOTALL):
            test_name = match.group(1)
            test_body = match.group(0)
            
            # Extract method calls
            call_pattern = r'self\.\w+\.(\w+)\('
            for method_match in re.finditer(call_pattern, test_body):
                method_name = method_match.group(1)
                if method_name not in requirements["methods"]:
                    requirements["methods"].append({
                        "name": method_name,
                        "test": test_name,
                        "body": test_body
                    })
            
            # Check for exception handling
            if 'pytest.raises' in test_body or 'assertRaises' in test_body:
                exception_pattern = r'raises\((\w+)'
                for exc_match in re.finditer(exception_pattern, test_body):
                    requirements["error_handling"].append({
                        "exception": exc_match.group(1),
                        "test": test_name
                    })
        
        return requirements
    
    def _format_requirements(self, requirements: Dict[str, Any]) -> str:
        """Format requirements for display"""
        lines = []
        
        if requirements["classes"]:
            lines.append(f"- Classes: {', '.join(requirements['classes'])}")
        
        if requirements["methods"]:
            method_names = [m["name"] for m in requirements["methods"]]
            lines.append(f"- Methods: {', '.join(method_names)}")
        
        if requirements["error_handling"]:
            exceptions = [e["exception"] for e in requirements["error_handling"]]
            lines.append(f"- Exceptions: {', '.join(set(exceptions))}")
        
        return '\n'.join(lines)
    
    def _generate_implementation(self, test_code: str, failing_tests: List[TestResult], 
                               requirements: Dict[str, Any]) -> str:
        """Generate minimal implementation to pass tests"""
        # Check if it's calculator tests
        if "Calculator" in str(requirements["classes"]):
            return self._generate_calculator_implementation()
        # Check for specific function patterns in test code
        elif "greet" in test_code.lower():
            return self._generate_greet_implementation(test_code)
        else:
            return self._generate_generic_implementation(requirements)
    
    def _generate_greet_implementation(self, test_code: str) -> str:
        """Generate minimal greet function implementation"""
        return '''def greet(name):
    """Greet a person by name"""
    return f"Hello, {name}!"'''
    
    def _generate_calculator_implementation(self) -> str:
        """Generate minimal calculator implementation"""
        return '''class Calculator:
    """A simple calculator class with basic operations"""
    
    def add(self, a, b):
        """Add two numbers"""
        self._validate_numbers(a, b)
        return a + b
    
    def subtract(self, a, b):
        """Subtract b from a"""
        self._validate_numbers(a, b)
        return a - b
    
    def multiply(self, a, b):
        """Multiply two numbers"""
        self._validate_numbers(a, b)
        return a * b
    
    def divide(self, a, b):
        """Divide a by b"""
        self._validate_numbers(a, b)
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b
    
    def _validate_numbers(self, a, b):
        """Validate that inputs are numbers"""
        if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
            raise TypeError("Both arguments must be numbers")'''
    
    def _generate_generic_implementation(self, requirements: Dict[str, Any]) -> str:
        """Generate generic implementation based on requirements"""
        # Get the main function/class name
        if requirements["classes"]:
            class_name = list(requirements["classes"])[0]
        else:
            class_name = None
        
        # Get method names
        methods = requirements["methods"]
        
        if methods and methods[0]["name"]:
            func_name = methods[0]["name"]
        else:
            func_name = "process"
        
        # Generate a simple implementation
        code_lines = []
        
        if class_name:
            # Class-based implementation
            code_lines.append(f'class {class_name}:')
            code_lines.append(f'    """Implementation of {class_name}"""')
            code_lines.append('')
            
            for method in methods:
                method_name = method["name"]
                code_lines.append(f'    def {method_name}(self, *args, **kwargs):')
                code_lines.append(f'        """Implementation of {method_name}"""')
                
                # Add basic implementation based on test analysis
                if "None" in method["body"]:
                    code_lines.append('        if args and args[0] is None:')
                    code_lines.append('            raise ValueError("Input cannot be None")')
                
                code_lines.append('        # Minimal implementation')
                code_lines.append('        if not args or args[0] == "":')
                code_lines.append('            return "empty"')
                code_lines.append('        elif any(c in "!@#$%" for c in str(args[0])):')
                code_lines.append('            return "special"')
                code_lines.append('        else:')
                code_lines.append('            return str(args[0])[:100]  # Truncate large inputs')
                code_lines.append('')
        else:
            # Function-based implementation
            code_lines.append(f'def {func_name}(input_value):')
            code_lines.append(f'    """Implementation of {func_name}"""')
            code_lines.append('    if input_value is None:')
            code_lines.append('        raise ValueError("Input cannot be None")')
            code_lines.append('    ')
            code_lines.append('    if input_value == "":')
            code_lines.append('        return "empty"')
            code_lines.append('    elif any(c in "!@#$%" for c in input_value):')
            code_lines.append('        return "special"')
            code_lines.append('    else:')
            code_lines.append('        return input_value[:100]  # Truncate large inputs')
        
        return '\n'.join(code_lines)
    
    def get_implementation_code(self) -> str:
        """Get the generated implementation code"""
        return getattr(self, '_implementation_code', '')
    
    def create_phase_result(self, success: bool = True, error: str = None) -> PhaseResult:
        """Create a PhaseResult for this agent's execution"""
        return PhaseResult(
            phase=self.phase,
            success=success,
            agent=self.agent_type,
            output=self.get_implementation_code(),
            error=error,
            metadata={
                "implementation_type": "minimal",
                "tdd_compliant": True
            }
        )