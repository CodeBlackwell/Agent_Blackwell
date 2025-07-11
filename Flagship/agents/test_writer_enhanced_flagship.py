"""Enhanced Test Writer Agent for comprehensive test generation"""

import asyncio
from typing import AsyncGenerator, Dict, Any, List
import json

from models.flagship_models import (
    AgentType, TDDPhase, AgentMessage, PhaseResult, TestStatus, TestResult
)


class TestWriterEnhancedFlagship:
    """Enhanced test writer that generates comprehensive tests based on features"""
    
    def __init__(self, file_manager=None):
        self.agent_type = AgentType.TEST_WRITER
        self.phase = TDDPhase.RED
        self.file_manager = file_manager
    
    async def write_comprehensive_tests(self, requirements: str, context: Dict[str, Any] = None) -> AsyncGenerator[str, None]:
        """
        Write comprehensive tests based on features and architecture
        
        Args:
            requirements: The requirements to write tests for
            context: Enhanced context with features, architecture, etc.
            
        Yields:
            Test code chunks as they're generated
        """
        yield f"🔴 RED Phase: Writing comprehensive tests...\n"
        
        # Extract context information
        current_feature = context.get("current_feature", {})
        architecture = context.get("architecture", {})
        existing_files = context.get("existing_files", [])
        
        if current_feature:
            yield f"📋 Feature: {current_feature.get('title', 'Unknown')}\n"
            yield f"Description: {current_feature.get('description', '')}\n"
            yield f"Components: {', '.join(current_feature.get('components', []))}\n\n"
        
        # Determine test framework and structure
        tech_stack = architecture.get("technology_stack", {}) if architecture else {}
        backend_tech = tech_stack.get("backend", "Python").lower()
        
        # Generate appropriate tests
        if "calculator" in requirements.lower() and current_feature:
            test_code = await self._generate_calculator_feature_tests(current_feature, architecture)
        else:
            test_code = await self._generate_generic_feature_tests(current_feature, requirements)
        
        # Yield test code
        yield "Generated Test Code:\n"
        yield "```python\n"
        for line in test_code.split('\n'):
            yield line + '\n'
            await asyncio.sleep(0.005)  # Streaming effect
        yield "```\n"
        
        # Store the test code
        self._test_code = test_code
        
        # Save to file manager if available
        if self.file_manager:
            filename = f"test_{current_feature.get('id', 'generated')}.py"
            self.file_manager.write_file(filename, test_code)
            yield f"\n✅ Test code saved to: {filename}"
    
    async def _generate_calculator_feature_tests(self, feature: Dict[str, Any], architecture: Dict[str, Any]) -> str:
        """Generate tests for calculator features"""
        
        feature_title = feature.get("title", "").lower()
        components = feature.get("components", [])
        
        # Different test generation based on feature
        if "setup" in feature_title or "structure" in feature_title:
            return self._generate_setup_tests(feature, architecture)
        elif "backend" in feature_title or "api" in feature_title:
            return self._generate_api_tests(feature, architecture)
        elif "frontend" in feature_title or "ui" in feature_title:
            return self._generate_ui_tests(feature, architecture)
        elif "operation" in feature_title or "calculation" in feature_title:
            return self._generate_calculation_tests(feature, architecture)
        elif "test" in feature_title or "validation" in feature_title:
            return self._generate_integration_tests(feature, architecture)
        else:
            return self._generate_generic_tests(feature)
    
    def _generate_setup_tests(self, feature: Dict[str, Any], architecture: Dict[str, Any]) -> str:
        """Generate tests for project setup"""
        return '''import pytest
import os
from pathlib import Path


class TestProjectSetup:
    """Test project structure and configuration"""
    
    def test_directory_structure_exists(self):
        """Test that all required directories exist"""
        required_dirs = ["frontend", "backend", "tests"]
        for dir_name in required_dirs:
            assert Path(dir_name).exists(), f"Directory {dir_name} should exist"
    
    def test_backend_configuration_files(self):
        """Test that backend configuration files exist"""
        assert Path("backend/app.py").exists(), "app.py should exist"
        assert Path("backend/config.py").exists(), "config.py should exist"
        assert Path("requirements.txt").exists(), "requirements.txt should exist"
    
    def test_frontend_files(self):
        """Test that frontend files exist"""
        assert Path("frontend/index.html").exists(), "index.html should exist"
        assert Path("frontend/css/style.css").exists(), "style.css should exist"
        assert Path("frontend/js/app.js").exists(), "app.js should exist"
    
    def test_environment_setup(self):
        """Test environment configuration"""
        assert Path(".env.example").exists(), ".env.example should exist"
        # Test that required environment variables are documented
        with open(".env.example", "r") as f:
            env_content = f.read()
            assert "FLASK_APP" in env_content, "FLASK_APP should be in .env.example"
'''
    
    def _generate_api_tests(self, feature: Dict[str, Any], architecture: Dict[str, Any]) -> str:
        """Generate tests for API endpoints"""
        return '''import pytest
import json
from flask import Flask
from backend.app import app
from backend.calculator import Calculator


@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def calculator():
    """Create calculator instance"""
    return Calculator()


class TestCalculatorAPI:
    """Test calculator REST API endpoints"""
    
    def test_api_root_endpoint(self, client):
        """Test root API endpoint"""
        response = client.get('/')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "message" in data
        assert "Calculator API" in data["message"]
    
    def test_calculate_endpoint_exists(self, client):
        """Test that calculate endpoint exists"""
        response = client.post('/api/calculate', 
                             json={"expression": "2+2"})
        # Should not return 404
        assert response.status_code != 404
    
    def test_calculate_simple_expression(self, client):
        """Test calculation of simple expression"""
        response = client.post('/api/calculate',
                             json={"expression": "2+2"})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "result" in data
        assert data["result"] == 4
    
    def test_calculate_invalid_expression(self, client):
        """Test calculation with invalid expression"""
        response = client.post('/api/calculate',
                             json={"expression": "2++2"})
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data
    
    def test_calculate_missing_expression(self, client):
        """Test calculation without expression"""
        response = client.post('/api/calculate', json={})
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data
    
    def test_operations_endpoint(self, client):
        """Test operations listing endpoint"""
        response = client.get('/api/operations')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "operations" in data
        assert isinstance(data["operations"], list)
        assert "+" in data["operations"]
    
    def test_cors_headers(self, client):
        """Test CORS headers are present"""
        response = client.get('/')
        assert "Access-Control-Allow-Origin" in response.headers
'''
    
    def _generate_ui_tests(self, feature: Dict[str, Any], architecture: Dict[str, Any]) -> str:
        """Generate tests for UI components"""
        return '''import pytest
from pathlib import Path


class TestCalculatorUI:
    """Test calculator user interface components"""
    
    def test_html_structure(self):
        """Test HTML file has proper structure"""
        html_path = Path("frontend/index.html")
        assert html_path.exists(), "index.html should exist"
        
        with open(html_path, "r") as f:
            html_content = f.read()
            
        # Check for essential elements
        assert "<div class=\"calculator\">" in html_content or "<div class='calculator'>" in html_content
        assert "<div class=\"display\">" in html_content or "<div class='display'>" in html_content
        assert "<div class=\"buttons\">" in html_content or "<div class='buttons'>" in html_content
        assert "id=\"display\"" in html_content or "id='display'" in html_content
    
    def test_css_styles(self):
        """Test CSS file contains calculator styles"""
        css_path = Path("frontend/css/style.css")
        assert css_path.exists(), "style.css should exist"
        
        with open(css_path, "r") as f:
            css_content = f.read()
        
        # Check for essential styles
        assert ".calculator" in css_content
        assert ".display" in css_content
        assert ".buttons" in css_content or ".button" in css_content
    
    def test_javascript_files(self):
        """Test JavaScript files exist and have content"""
        js_files = ["app.js", "calculator.js", "api.js"]
        
        for js_file in js_files:
            js_path = Path(f"frontend/js/{js_file}")
            assert js_path.exists(), f"{js_file} should exist"
            
            with open(js_path, "r") as f:
                content = f.read()
                assert len(content) > 10, f"{js_file} should have content"
    
    def test_calculator_ui_functions(self):
        """Test that calculator UI functions are defined"""
        calc_js_path = Path("frontend/js/calculator.js")
        
        with open(calc_js_path, "r") as f:
            js_content = f.read()
        
        # Check for essential functions
        assert "function" in js_content or "const" in js_content or "let" in js_content
        assert "display" in js_content.lower()
'''
    
    def _generate_calculation_tests(self, feature: Dict[str, Any], architecture: Dict[str, Any]) -> str:
        """Generate tests for calculation operations"""
        return '''import pytest
from backend.calculator import Calculator


class TestCalculatorOperations:
    """Test calculator core functionality"""
    
    @pytest.fixture
    def calculator(self):
        """Create calculator instance"""
        return Calculator()
    
    def test_calculator_instantiation(self, calculator):
        """Test calculator can be instantiated"""
        assert calculator is not None
        assert hasattr(calculator, 'add')
        assert hasattr(calculator, 'subtract')
        assert hasattr(calculator, 'multiply')
        assert hasattr(calculator, 'divide')
    
    def test_addition(self, calculator):
        """Test addition operation"""
        assert calculator.add(2, 3) == 5
        assert calculator.add(-1, 1) == 0
        assert calculator.add(0, 0) == 0
        assert calculator.add(1.5, 2.5) == 4.0
    
    def test_subtraction(self, calculator):
        """Test subtraction operation"""
        assert calculator.subtract(5, 3) == 2
        assert calculator.subtract(0, 5) == -5
        assert calculator.subtract(-1, -1) == 0
        assert calculator.subtract(10.5, 0.5) == 10.0
    
    def test_multiplication(self, calculator):
        """Test multiplication operation"""
        assert calculator.multiply(3, 4) == 12
        assert calculator.multiply(0, 100) == 0
        assert calculator.multiply(-2, 3) == -6
        assert calculator.multiply(2.5, 4) == 10.0
    
    def test_division(self, calculator):
        """Test division operation"""
        assert calculator.divide(10, 2) == 5
        assert calculator.divide(7, 2) == 3.5
        assert calculator.divide(-10, 2) == -5
        assert calculator.divide(1, 3) == pytest.approx(0.333333, rel=1e-5)
    
    def test_division_by_zero(self, calculator):
        """Test division by zero raises error"""
        with pytest.raises(ValueError, match="Division by zero"):
            calculator.divide(10, 0)
    
    def test_calculate_expression(self, calculator):
        """Test expression calculation"""
        # Basic expressions
        assert calculator.calculate("2+2") == 4
        assert calculator.calculate("10-5") == 5
        assert calculator.calculate("3*4") == 12
        assert calculator.calculate("15/3") == 5
        
        # Complex expressions
        assert calculator.calculate("2+3*4") == 14
        assert calculator.calculate("(2+3)*4") == 20
        assert calculator.calculate("10/2+3") == 8
    
    def test_memory_functions(self, calculator):
        """Test memory functions if implemented"""
        if hasattr(calculator, 'memory_add'):
            calculator.memory_clear()
            calculator.memory_add(5)
            assert calculator.memory_recall() == 5
            
            calculator.memory_add(3)
            assert calculator.memory_recall() == 8
            
            calculator.memory_subtract(2)
            assert calculator.memory_recall() == 6
            
            calculator.memory_clear()
            assert calculator.memory_recall() == 0
'''
    
    def _generate_integration_tests(self, feature: Dict[str, Any], architecture: Dict[str, Any]) -> str:
        """Generate integration tests"""
        return '''import pytest
import json
import time
from flask import Flask
from backend.app import app


@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestCalculatorIntegration:
    """Integration tests for calculator application"""
    
    def test_end_to_end_calculation(self, client):
        """Test complete calculation flow"""
        # Test simple calculation
        response = client.post('/api/calculate',
                             json={"expression": "5+3"})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["result"] == 8
        assert data["expression"] == "5+3"
        assert "timestamp" in data
    
    def test_multiple_calculations(self, client):
        """Test multiple calculations in sequence"""
        expressions = [
            ("2+2", 4),
            ("10-5", 5),
            ("3*4", 12),
            ("20/4", 5),
            ("2+3*4", 14)
        ]
        
        for expression, expected in expressions:
            response = client.post('/api/calculate',
                                 json={"expression": expression})
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["result"] == expected
    
    def test_error_handling_integration(self, client):
        """Test error handling across the application"""
        # Invalid expression
        response = client.post('/api/calculate',
                             json={"expression": "2++2"})
        assert response.status_code == 400
        assert "error" in json.loads(response.data)
        
        # Division by zero
        response = client.post('/api/calculate',
                             json={"expression": "10/0"})
        assert response.status_code == 400
        assert "error" in json.loads(response.data)
        
        # Empty expression
        response = client.post('/api/calculate',
                             json={"expression": ""})
        assert response.status_code == 400
        assert "error" in json.loads(response.data)
    
    def test_api_performance(self, client):
        """Test API response time"""
        start_time = time.time()
        
        response = client.post('/api/calculate',
                             json={"expression": "2+2"})
        
        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # Convert to ms
        
        assert response.status_code == 200
        assert response_time < 100, f"Response time {response_time}ms exceeds 100ms limit"
    
    def test_concurrent_requests(self, client):
        """Test handling of concurrent requests"""
        import concurrent.futures
        
        def make_request(expression):
            return client.post('/api/calculate',
                             json={"expression": expression})
        
        expressions = ["1+1", "2+2", "3+3", "4+4", "5+5"]
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request, expr) for expr in expressions]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # All requests should succeed
        for response in results:
            assert response.status_code == 200
'''
    
    def _generate_generic_tests(self, feature: Dict[str, Any]) -> str:
        """Generate generic tests for unknown features"""
        components = feature.get("components", [])
        
        test_methods = []
        for component in components:
            method_name = self._sanitize_name(component)
            test_methods.append(f'''
    def test_{method_name}_exists(self):
        """Test that {component} exists and is functional"""
        # TODO: Implement test for {component}
        assert False, "Test not implemented"
    
    def test_{method_name}_functionality(self):
        """Test {component} functionality"""
        # TODO: Test specific functionality of {component}
        assert False, "Test not implemented"
''')
        
        return f'''import pytest


class Test{self._sanitize_name(feature.get("title", "Feature"))}:
    """Test suite for {feature.get("title", "feature")}"""
    
    def test_feature_setup(self):
        """Test feature can be set up"""
        # TODO: Implement setup test
        assert False, "Test not implemented"
{"".join(test_methods)}
    
    def test_feature_integration(self):
        """Test feature components work together"""
        # Components to test: {", ".join(components)}
        # TODO: Implement integration test
        assert False, "Test not implemented"
'''
    
    async def _generate_generic_feature_tests(self, feature: Dict[str, Any], requirements: str) -> str:
        """Generate generic feature tests"""
        if not feature:
            # No feature context, generate basic tests
            return self._generate_basic_tests(requirements)
        
        return self._generate_generic_tests(feature)
    
    def _generate_basic_tests(self, requirements: str) -> str:
        """Generate basic tests when no feature context"""
        return f'''import pytest


class TestImplementation:
    """Test suite for: {requirements}"""
    
    def test_implementation_exists(self):
        """Test that implementation exists"""
        # TODO: Import and test implementation
        assert False, "Test not implemented"
    
    def test_basic_functionality(self):
        """Test basic functionality"""
        # TODO: Test core functionality based on requirements
        assert False, "Test not implemented"
    
    def test_error_handling(self):
        """Test error handling"""
        # TODO: Test error cases
        assert False, "Test not implemented"
'''
    
    def _sanitize_name(self, name: str) -> str:
        """Sanitize name for use in test methods"""
        import re
        # Remove special characters and convert to snake_case
        name = re.sub(r'[^\w\s]', '', name)
        name = re.sub(r'\s+', '_', name)
        return name.lower()