"""Feature-based Test Generator for Enhanced TDD Workflow"""

import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path
import re

from .enhanced_models import (
    TestableFeature, TestCriteria, EnhancedAgentContext,
    ProjectArchitecture, ArchitectureComponent
)


class FeatureBasedTestGenerator:
    """Generates comprehensive tests based on testable features"""
    
    def __init__(self):
        """Initialize test generator"""
        self.test_templates = self._load_test_templates()
    
    async def generate_tests_for_feature(self, feature: TestableFeature, 
                                       context: EnhancedAgentContext) -> str:
        """
        Generate comprehensive tests for a feature
        Args:
            feature: The testable feature to generate tests for
            context: Enhanced context with architecture and requirements
        Returns:
            Generated test code
        """
        # Determine test framework and language
        test_framework = "pytest"  # Default, could be from config
        language = self._determine_language(context.architecture)
        
        # Generate test structure
        test_code = []
        
        # Add imports
        test_code.append(self._generate_imports(feature, language, test_framework))
        test_code.append("")
        
        # Generate test class
        test_class_name = self._get_test_class_name(feature)
        test_code.append(f"class {test_class_name}:")
        test_code.append(f'    """Tests for {feature.title}"""')
        test_code.append("")
        
        # Generate setup if needed
        if self._needs_setup(feature):
            test_code.append(self._generate_setup(feature, context))
            test_code.append("")
        
        # Generate tests for each component
        for component in feature.components:
            component_tests = await self._generate_component_tests(
                component, feature, context
            )
            test_code.extend(component_tests)
            test_code.append("")
        
        # Generate integration tests if applicable
        if len(feature.components) > 1:
            integration_tests = self._generate_integration_tests(feature, context)
            test_code.extend(integration_tests)
            test_code.append("")
        
        # Generate edge case tests
        edge_case_tests = self._generate_edge_case_tests(feature, context)
        if edge_case_tests:
            test_code.extend(edge_case_tests)
        
        return "\n".join(test_code)
    
    async def _generate_component_tests(self, component: str, 
                                      feature: TestableFeature,
                                      context: EnhancedAgentContext) -> List[str]:
        """Generate tests for a specific component"""
        tests = []
        
        # Analyze component type
        component_type = self._analyze_component_type(component, context)
        
        if component_type == "api_endpoint":
            tests.extend(self._generate_api_tests(component, feature))
        elif component_type == "ui_component":
            tests.extend(self._generate_ui_tests(component, feature))
        elif component_type == "data_model":
            tests.extend(self._generate_model_tests(component, feature))
        elif component_type == "business_logic":
            tests.extend(self._generate_logic_tests(component, feature))
        else:
            # Generate generic tests
            tests.extend(self._generate_generic_tests(component, feature))
        
        return tests
    
    def _generate_api_tests(self, component: str, feature: TestableFeature) -> List[str]:
        """Generate tests for API endpoints"""
        tests = []
        test_name = self._sanitize_test_name(component)
        
        # Basic endpoint test
        tests.append(f"    def test_{test_name}_endpoint_exists(self, client):")
        tests.append(f'        """Test that {component} endpoint exists"""')
        tests.append(f"        # TODO: Implement endpoint existence test")
        tests.append(f"        assert False, 'Test not implemented'")
        tests.append("")
        
        # Success case
        tests.append(f"    def test_{test_name}_success(self, client):")
        tests.append(f'        """Test successful {component} operation"""')
        tests.append(f"        # TODO: Implement success test")
        tests.append(f"        assert False, 'Test not implemented'")
        tests.append("")
        
        # Error cases
        tests.append(f"    def test_{test_name}_invalid_input(self, client):")
        tests.append(f'        """Test {component} with invalid input"""')
        tests.append(f"        # TODO: Implement error handling test")
        tests.append(f"        assert False, 'Test not implemented'")
        
        return tests
    
    def _generate_ui_tests(self, component: str, feature: TestableFeature) -> List[str]:
        """Generate tests for UI components"""
        tests = []
        test_name = self._sanitize_test_name(component)
        
        # Render test
        tests.append(f"    def test_{test_name}_renders(self):")
        tests.append(f'        """Test that {component} renders correctly"""')
        tests.append(f"        # TODO: Implement render test")
        tests.append(f"        assert False, 'Test not implemented'")
        tests.append("")
        
        # Interaction test
        tests.append(f"    def test_{test_name}_user_interaction(self):")
        tests.append(f'        """Test {component} user interactions"""')
        tests.append(f"        # TODO: Implement interaction test")
        tests.append(f"        assert False, 'Test not implemented'")
        
        return tests
    
    def _generate_model_tests(self, component: str, feature: TestableFeature) -> List[str]:
        """Generate tests for data models"""
        tests = []
        test_name = self._sanitize_test_name(component)
        
        # Creation test
        tests.append(f"    def test_{test_name}_creation(self):")
        tests.append(f'        """Test {component} model creation"""')
        tests.append(f"        # TODO: Implement model creation test")
        tests.append(f"        assert False, 'Test not implemented'")
        tests.append("")
        
        # Validation test
        tests.append(f"    def test_{test_name}_validation(self):")
        tests.append(f'        """Test {component} model validation"""')
        tests.append(f"        # TODO: Implement validation test")
        tests.append(f"        assert False, 'Test not implemented'")
        
        return tests
    
    def _generate_logic_tests(self, component: str, feature: TestableFeature) -> List[str]:
        """Generate tests for business logic"""
        tests = []
        test_name = self._sanitize_test_name(component)
        
        # Function test
        tests.append(f"    def test_{test_name}_logic(self):")
        tests.append(f'        """Test {component} business logic"""')
        tests.append(f"        # TODO: Implement logic test")
        tests.append(f"        assert False, 'Test not implemented'")
        tests.append("")
        
        # Edge cases
        tests.append(f"    def test_{test_name}_edge_cases(self):")
        tests.append(f'        """Test {component} edge cases"""')
        tests.append(f"        # TODO: Implement edge case tests")
        tests.append(f"        assert False, 'Test not implemented'")
        
        return tests
    
    def _generate_generic_tests(self, component: str, feature: TestableFeature) -> List[str]:
        """Generate generic tests for unknown component types"""
        tests = []
        test_name = self._sanitize_test_name(component)
        
        tests.append(f"    def test_{test_name}_exists(self):")
        tests.append(f'        """Test that {component} exists and is accessible"""')
        tests.append(f"        # TODO: Implement existence test for {component}")
        tests.append(f"        assert False, 'Test not implemented'")
        tests.append("")
        
        tests.append(f"    def test_{test_name}_functionality(self):")
        tests.append(f'        """Test {component} functionality"""')
        tests.append(f"        # TODO: Implement functionality test")
        tests.append(f"        assert False, 'Test not implemented'")
        
        return tests
    
    def _generate_integration_tests(self, feature: TestableFeature, 
                                  context: EnhancedAgentContext) -> List[str]:
        """Generate integration tests for multiple components"""
        tests = []
        
        tests.append(f"    def test_{self._sanitize_test_name(feature.title)}_integration(self):")
        tests.append(f'        """Test integration of all components in {feature.title}"""')
        tests.append(f"        # Test that components work together:")
        for component in feature.components:
            tests.append(f"        # - {component}")
        tests.append(f"        # TODO: Implement integration test")
        tests.append(f"        assert False, 'Test not implemented'")
        
        return tests
    
    def _generate_edge_case_tests(self, feature: TestableFeature,
                                 context: EnhancedAgentContext) -> List[str]:
        """Generate edge case tests"""
        tests = []
        
        # Identify potential edge cases based on feature
        edge_cases = self._identify_edge_cases(feature, context)
        
        if edge_cases:
            tests.append(f"    # Edge case tests")
            for edge_case in edge_cases:
                test_name = self._sanitize_test_name(edge_case)
                tests.append(f"    def test_edge_case_{test_name}(self):")
                tests.append(f'        """Test edge case: {edge_case}"""')
                tests.append(f"        # TODO: Implement edge case test")
                tests.append(f"        assert False, 'Test not implemented'")
                tests.append("")
        
        return tests
    
    def _generate_imports(self, feature: TestableFeature, language: str, framework: str) -> str:
        """Generate import statements"""
        imports = []
        
        if language == "python":
            if framework == "pytest":
                imports.append("import pytest")
            imports.append("import unittest")
            
            # Add feature-specific imports
            if any("api" in comp.lower() for comp in feature.components):
                imports.append("from flask import Flask")
                imports.append("from flask.testing import FlaskClient")
            
            if any("model" in comp.lower() for comp in feature.components):
                imports.append("from sqlalchemy import create_engine")
            
            # Add imports for the actual implementation
            # This would be determined by the architecture
            imports.append("")
            imports.append("# Import implementation modules")
            imports.append("# TODO: Add actual imports based on implementation")
        
        return "\n".join(imports)
    
    def _generate_setup(self, feature: TestableFeature, context: EnhancedAgentContext) -> str:
        """Generate test setup/fixtures"""
        setup = []
        
        setup.append("    @pytest.fixture")
        setup.append("    def setup(self):")
        setup.append('        """Set up test fixtures"""')
        setup.append("        # TODO: Implement test setup")
        setup.append("        pass")
        
        # Add specific fixtures based on components
        if any("api" in comp.lower() for comp in feature.components):
            setup.append("")
            setup.append("    @pytest.fixture")
            setup.append("    def client(self):")
            setup.append('        """Create test client"""')
            setup.append("        # TODO: Create and return test client")
            setup.append("        pass")
        
        return "\n".join(setup)
    
    def _determine_language(self, architecture: Optional[ProjectArchitecture]) -> str:
        """Determine programming language from architecture"""
        if not architecture:
            return "python"  # Default
        
        # Check technology stack
        backend = architecture.technology_stack.get("backend", "").lower()
        
        if any(lang in backend for lang in ["python", "flask", "django", "fastapi"]):
            return "python"
        elif any(lang in backend for lang in ["javascript", "node", "express"]):
            return "javascript"
        elif any(lang in backend for lang in ["java", "spring"]):
            return "java"
        elif any(lang in backend for lang in ["ruby", "rails"]):
            return "ruby"
        else:
            return "python"  # Default
    
    def _analyze_component_type(self, component: str, context: EnhancedAgentContext) -> str:
        """Analyze what type of component this is"""
        component_lower = component.lower()
        
        # API endpoints
        if any(keyword in component_lower for keyword in ["endpoint", "api", "route", "controller"]):
            return "api_endpoint"
        
        # UI components
        elif any(keyword in component_lower for keyword in ["ui", "component", "page", "view", "form"]):
            return "ui_component"
        
        # Data models
        elif any(keyword in component_lower for keyword in ["model", "schema", "entity", "table"]):
            return "data_model"
        
        # Business logic
        elif any(keyword in component_lower for keyword in ["service", "logic", "algorithm", "calculator"]):
            return "business_logic"
        
        # Default
        return "generic"
    
    def _needs_setup(self, feature: TestableFeature) -> bool:
        """Determine if feature tests need setup/fixtures"""
        # Check if any components suggest need for setup
        needs_setup_keywords = ["database", "api", "server", "client", "fixture"]
        
        for component in feature.components:
            if any(keyword in component.lower() for keyword in needs_setup_keywords):
                return True
        
        return len(feature.components) > 2  # Complex features likely need setup
    
    def _identify_edge_cases(self, feature: TestableFeature, 
                           context: EnhancedAgentContext) -> List[str]:
        """Identify potential edge cases for the feature"""
        edge_cases = []
        
        # Common edge cases based on feature type
        feature_desc_lower = feature.description.lower()
        
        if "calculator" in feature_desc_lower:
            edge_cases.extend([
                "division by zero",
                "very large numbers",
                "negative numbers",
                "decimal precision"
            ])
        
        if "api" in feature_desc_lower:
            edge_cases.extend([
                "empty request body",
                "malformed JSON",
                "missing required fields",
                "unauthorized access"
            ])
        
        if "database" in feature_desc_lower:
            edge_cases.extend([
                "duplicate entries",
                "null values",
                "foreign key constraints",
                "transaction rollback"
            ])
        
        # Filter to relevant edge cases based on components
        relevant_edge_cases = []
        for edge_case in edge_cases:
            if any(comp.lower() in edge_case or edge_case in comp.lower() 
                   for comp in feature.components):
                relevant_edge_cases.append(edge_case)
        
        return relevant_edge_cases[:3]  # Limit to top 3 most relevant
    
    def _get_test_class_name(self, feature: TestableFeature) -> str:
        """Generate test class name from feature"""
        # Convert feature title to PascalCase
        words = re.findall(r'\w+', feature.title)
        class_name = "Test" + "".join(word.capitalize() for word in words)
        return class_name
    
    def _sanitize_test_name(self, name: str) -> str:
        """Sanitize name for use in test method names"""
        # Convert to snake_case and remove special characters
        name = re.sub(r'[^\w\s]', '', name)
        name = re.sub(r'\s+', '_', name)
        return name.lower()
    
    def _load_test_templates(self) -> Dict[str, str]:
        """Load test templates for different scenarios"""
        return {
            "api_endpoint": """
    def test_{name}_endpoint(self, client):
        response = client.{method}('{path}')
        assert response.status_code == {expected_status}
""",
            "model_validation": """
    def test_{name}_validation(self):
        # Test valid case
        valid_data = {valid_data}
        instance = {model_class}(**valid_data)
        assert instance.validate()
        
        # Test invalid case
        invalid_data = {invalid_data}
        with pytest.raises(ValidationError):
            {model_class}(**invalid_data)
""",
            "ui_component": """
    def test_{name}_render(self):
        component = {component_class}()
        rendered = component.render()
        assert '{expected_element}' in rendered
"""
        }