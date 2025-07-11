"""Enhanced Coder Agent for multi-file implementation

WARNING: This file contains hardcoded calculator templates and should not be used
for general code generation. This is an experimental/legacy version in the Flagship directory.
Use the main coder agent at agents/coder/coder_agent.py instead.
"""

import asyncio
from typing import AsyncGenerator, Dict, Any, List
import re

from models.flagship_models import AgentType, TDDPhase


class CoderEnhancedFlagship:
    """Enhanced coder that generates multi-file implementations"""
    
    def __init__(self, file_manager=None):
        self.agent_type = AgentType.CODER
        self.phase = TDDPhase.YELLOW
        self.file_manager = file_manager
    
    async def generate_multi_file_implementation(self, test_code: str, context: Dict[str, Any] = None) -> AsyncGenerator[str, None]:
        """
        Generate multi-file implementation to pass tests
        
        Args:
            test_code: The test code to implement against
            context: Enhanced context with architecture, features, etc.
            
        Yields:
            Implementation code chunks with file markers
        """
        yield f"🟡 YELLOW Phase: Implementing to pass tests...\n\n"
        
        # Extract context
        current_feature = context.get("current_feature", {})
        architecture = context.get("architecture", {})
        existing_files = context.get("existing_files", {})
        
        if current_feature:
            yield f"📋 Implementing Feature: {current_feature.get('title', 'Unknown')}\n"
            yield f"Components: {', '.join(current_feature.get('components', []))}\n\n"
        
        # Analyze tests to understand what to implement
        test_analysis = self._analyze_test_code(test_code)
        yield f"📊 Test Analysis:\n"
        yield f"  - Test Classes: {len(test_analysis['test_classes'])}\n"
        yield f"  - Test Methods: {len(test_analysis['test_methods'])}\n"
        yield f"  - Imports Needed: {', '.join(test_analysis['imports'])}\n\n"
        
        # Generate implementation based on feature and tests
        if current_feature and architecture:
            implementation_files = await self._generate_feature_implementation(
                current_feature, architecture, test_analysis, existing_files
            )
        else:
            # Fallback to simple implementation
            implementation_files = self._generate_simple_implementation(test_analysis)
        
        # Yield each file
        for filepath, content in implementation_files.items():
            yield f"\n{'='*60}\n"
            yield f"FILE: {filepath}\n"
            yield f"{'='*60}\n"
            for line in content.split('\n'):
                yield line + '\n'
                await asyncio.sleep(0.001)
        
        yield f"\n✅ Generated {len(implementation_files)} files for implementation\n"
        
        # Store files
        self._implementation_files = implementation_files
    
    def _analyze_test_code(self, test_code: str) -> Dict[str, Any]:
        """Analyze test code to understand what needs to be implemented"""
        analysis = {
            "test_classes": [],
            "test_methods": [],
            "imports": [],
            "assertions": [],
            "fixtures": []
        }
        
        # Find test classes
        class_pattern = r'class\s+(\w+).*?:'
        analysis["test_classes"] = re.findall(class_pattern, test_code)
        
        # Find test methods
        method_pattern = r'def\s+(test_\w+)\s*\('
        analysis["test_methods"] = re.findall(method_pattern, test_code)
        
        # Find imports to understand dependencies
        import_pattern = r'from\s+([\w.]+)\s+import|import\s+([\w.]+)'
        import_matches = re.findall(import_pattern, test_code)
        for match in import_matches:
            module = match[0] or match[1]
            if module and not module.startswith(('pytest', 'unittest')):
                analysis["imports"].append(module)
        
        # Find assertions to understand expected behavior
        assertion_pattern = r'assert\s+(.+?)(?:\n|$)'
        analysis["assertions"] = re.findall(assertion_pattern, test_code, re.MULTILINE)
        
        # Find fixtures
        fixture_pattern = r'@pytest\.fixture.*?\n\s*def\s+(\w+)'
        analysis["fixtures"] = re.findall(fixture_pattern, test_code, re.DOTALL)
        
        return analysis
    
    async def _generate_feature_implementation(self, feature: Dict[str, Any], 
                                             architecture: Dict[str, Any],
                                             test_analysis: Dict[str, Any],
                                             existing_files: Dict[str, str]) -> Dict[str, str]:
        """Generate implementation files for a specific feature"""
        
        feature_title = feature.get("title", "").lower()
        files = {}
        
        # Generate based on feature type
        if "setup" in feature_title or "structure" in feature_title:
            # Project setup - mostly configuration files
            files.update(self._generate_setup_files(architecture))
            
        elif "backend" in feature_title or "api" in feature_title:
            # Backend API implementation
            files.update(self._generate_backend_api_files(feature, architecture, test_analysis))
            
        elif "frontend" in feature_title or "ui" in feature_title:
            # Frontend UI implementation
            files.update(self._generate_frontend_files(feature, architecture, test_analysis))
            
        elif "operation" in feature_title or "calculation" in feature_title:
            # Calculator operations
            files.update(self._generate_calculator_logic_files(feature, architecture, test_analysis))
            
        else:
            # Generic implementation
            files.update(self._generate_generic_implementation_files(feature, test_analysis))
        
        return files
    
    def _generate_setup_files(self, architecture: Dict[str, Any]) -> Dict[str, str]:
        """Generate project setup files"""
        files = {}
        
        # Backend config
        files["backend/config.py"] = '''"""Configuration for application"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5000))
    
    # CORS settings
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*')
    
    # API settings
    API_PREFIX = '/api'
    MAX_EXPRESSION_LENGTH = 1000
'''

        # Environment example
        files[".env.example"] = '''# Flask Configuration
FLASK_APP=backend/app.py
FLASK_ENV=development
DEBUG=True

# Server Configuration
HOST=0.0.0.0
PORT=5000

# Security
SECRET_KEY=your-secret-key-here

# CORS
CORS_ORIGINS=*
'''

        # Requirements
        files["requirements.txt"] = '''Flask==2.3.2
flask-cors==4.0.0
python-dotenv==1.0.0
pytest==7.4.0
pytest-flask==1.2.0
'''

        # Package.json for frontend
        files["package.json"] = '''{
  "name": "calculator-frontend",
  "version": "1.0.0",
  "description": "Calculator application frontend",
  "scripts": {
    "start": "python -m http.server 8080 -d frontend",
    "test": "jest"
  },
  "devDependencies": {
    "jest": "^29.0.0",
    "eslint": "^8.0.0"
  }
}'''

        # Docker files if in architecture
        if any("docker" in str(v).lower() for v in architecture.get("technology_stack", {}).values()):
            files["Dockerfile"] = '''FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "backend/app.py"]
'''

            files["docker-compose.yml"] = '''version: '3.8'

services:
  calculator-app:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
    volumes:
      - ./frontend:/app/frontend
'''

        return files
    
    def _generate_backend_api_files(self, feature: Dict[str, Any], 
                                   architecture: Dict[str, Any],
                                   test_analysis: Dict[str, Any]) -> Dict[str, str]:
        """Generate backend API files"""
        files = {}
        
        # Main app file
        files["backend/app.py"] = '''"""Calculator REST API application"""
from flask import Flask, jsonify
from flask_cors import CORS
from config import Config

# Import routes after app creation to avoid circular imports
app = Flask(__name__)
app.config.from_object(Config)
CORS(app, origins=app.config['CORS_ORIGINS'])


@app.route('/')
def index():
    """Root endpoint"""
    return jsonify({
        "message": "Calculator API",
        "version": "1.0.0",
        "endpoints": {
            "calculate": "/api/calculate",
            "operations": "/api/operations"
        }
    })


# Import and register blueprints
from api.routes import api_bp
app.register_blueprint(api_bp, url_prefix='/api')


if __name__ == '__main__':
    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config['DEBUG']
    )
'''

        # Calculator module (basic for now)
        files["backend/calculator.py"] = '''"""Core calculator logic"""


class Calculator:
    """Calculator with basic and advanced operations"""
    
    def __init__(self):
        """Initialize calculator"""
        self.history = []
        self.memory = 0
    
    def calculate(self, expression: str) -> float:
        """
        Calculate mathematical expression safely
        Args:
            expression: Math expression as string
        Returns:
            Calculation result
        Raises:
            ValueError: If expression is invalid
        """
        # Clean and validate expression
        expression = expression.strip()
        if not expression:
            raise ValueError("Empty expression")
        
        # For now, use eval with safety checks
        # In production, use a proper expression parser
        allowed_chars = set('0123456789+-*/()., ')
        if not all(c in allowed_chars for c in expression):
            raise ValueError("Invalid characters in expression")
        
        try:
            result = eval(expression)
            self.history.append((expression, result))
            return float(result)
        except (SyntaxError, NameError, ZeroDivisionError) as e:
            raise ValueError(f"Invalid expression: {str(e)}")
    
    def add(self, a: float, b: float) -> float:
        """Add two numbers"""
        return a + b
    
    def subtract(self, a: float, b: float) -> float:
        """Subtract b from a"""
        return a - b
    
    def multiply(self, a: float, b: float) -> float:
        """Multiply two numbers"""
        return a * b
    
    def divide(self, a: float, b: float) -> float:
        """Divide a by b"""
        if b == 0:
            raise ValueError("Division by zero")
        return a / b
    
    # Memory functions
    def memory_clear(self):
        """Clear memory"""
        self.memory = 0
    
    def memory_add(self, value: float):
        """Add to memory"""
        self.memory += value
    
    def memory_subtract(self, value: float):
        """Subtract from memory"""
        self.memory -= value
    
    def memory_recall(self) -> float:
        """Recall memory value"""
        return self.memory
'''

        # API routes
        files["backend/api/__init__.py"] = '"""API package"""'
        
        files["backend/api/routes.py"] = '''"""API route definitions"""
from flask import Blueprint, request, jsonify
from datetime import datetime
from backend.calculator import Calculator

api_bp = Blueprint('api', __name__)
calculator = Calculator()


@api_bp.route('/calculate', methods=['POST'])
def calculate():
    """Calculate expression endpoint"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        expression = data.get('expression', '')
        if not expression:
            return jsonify({"error": "No expression provided"}), 400
        
        # Calculate result
        result = calculator.calculate(expression)
        
        return jsonify({
            'result': result,
            'expression': expression,
            'timestamp': datetime.now().isoformat()
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@api_bp.route('/operations', methods=['GET'])
def get_operations():
    """Get supported operations"""
    return jsonify({
        'operations': ['+', '-', '*', '/', '(', ')'],
        'categories': {
            'basic': ['+', '-', '*', '/'],
            'grouping': ['(', ')']
        }
    })


@api_bp.route('/history', methods=['GET'])
def get_history():
    """Get calculation history"""
    history_data = [
        {
            'expression': expr,
            'result': result,
            'timestamp': datetime.now().isoformat()
        }
        for expr, result in calculator.history[-10:]  # Last 10 calculations
    ]
    
    return jsonify({'history': history_data})
'''

        # Validators
        files["backend/api/validators.py"] = '''"""Input validators for API"""


def validate_expression(expression: str) -> bool:
    """Validate mathematical expression"""
    if not expression or not isinstance(expression, str):
        return False
    
    # Check length
    if len(expression) > 1000:
        return False
    
    # Check for valid characters
    allowed_chars = set('0123456789+-*/()., ')
    return all(c in allowed_chars for c in expression)
'''

        return files
    
    def _generate_frontend_files(self, feature: Dict[str, Any],
                                architecture: Dict[str, Any],
                                test_analysis: Dict[str, Any]) -> Dict[str, str]:
        """Generate frontend files"""
        files = {}
        
        # HTML
        files["frontend/index.html"] = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Calculator App</title>
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <div class="container">
        <h1>Calculator</h1>
        <div class="calculator">
            <div class="display">
                <input type="text" id="display" readonly value="0">
            </div>
            <div class="buttons" id="button-grid">
                <!-- Buttons will be generated by JavaScript -->
            </div>
        </div>
    </div>
    
    <script src="js/api.js"></script>
    <script src="js/calculator.js"></script>
    <script src="js/app.js"></script>
</body>
</html>'''

        # CSS
        files["frontend/css/style.css"] = '''/* Calculator styles */
* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    font-family: Arial, sans-serif;
    background-color: #f0f0f0;
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
}

.container {
    text-align: center;
}

h1 {
    margin-bottom: 20px;
    color: #333;
}

.calculator {
    background-color: #333;
    padding: 20px;
    border-radius: 10px;
    box-shadow: 0 0 20px rgba(0, 0, 0, 0.2);
    width: 320px;
}

.display {
    margin-bottom: 10px;
}

#display {
    width: 100%;
    padding: 10px;
    font-size: 24px;
    text-align: right;
    border: none;
    border-radius: 5px;
    background-color: #444;
    color: white;
}

.buttons {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
}

.button {
    padding: 20px;
    font-size: 18px;
    border: none;
    border-radius: 5px;
    background-color: #666;
    color: white;
    cursor: pointer;
    transition: background-color 0.2s;
}

.button:hover {
    background-color: #777;
}

.button:active {
    background-color: #555;
}

.button.operator {
    background-color: #ff9500;
}

.button.operator:hover {
    background-color: #ffb143;
}

.button.equals {
    background-color: #4CAF50;
    grid-column: span 2;
}

.button.equals:hover {
    background-color: #5cbf60;
}

.button.clear {
    background-color: #f44336;
}

.button.clear:hover {
    background-color: #f66;
}'''

        # JavaScript files
        files["frontend/js/api.js"] = '''// API communication module
const API_BASE_URL = 'http://localhost:5000/api';

class CalculatorAPI {
    async calculate(expression) {
        try {
            const response = await fetch(`${API_BASE_URL}/calculate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ expression })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Calculation failed');
            }

            const data = await response.json();
            return data.result;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    async getOperations() {
        try {
            const response = await fetch(`${API_BASE_URL}/operations`);
            const data = await response.json();
            return data.operations;
        } catch (error) {
            console.error('API Error:', error);
            return ['+', '-', '*', '/'];
        }
    }
}

const calculatorAPI = new CalculatorAPI();
'''

        files["frontend/js/calculator.js"] = '''// Calculator UI logic
class CalculatorUI {
    constructor() {
        this.display = document.getElementById('display');
        this.currentExpression = '0';
        this.shouldResetDisplay = false;
    }

    updateDisplay(value) {
        this.display.value = value;
    }

    appendToExpression(value) {
        if (this.shouldResetDisplay) {
            this.currentExpression = '0';
            this.shouldResetDisplay = false;
        }

        if (this.currentExpression === '0' && value !== '.') {
            this.currentExpression = value;
        } else {
            this.currentExpression += value;
        }

        this.updateDisplay(this.currentExpression);
    }

    clear() {
        this.currentExpression = '0';
        this.updateDisplay(this.currentExpression);
    }

    async calculate() {
        try {
            const result = await calculatorAPI.calculate(this.currentExpression);
            this.currentExpression = result.toString();
            this.updateDisplay(this.currentExpression);
            this.shouldResetDisplay = true;
        } catch (error) {
            this.updateDisplay('Error');
            this.shouldResetDisplay = true;
        }
    }

    handleButtonClick(value) {
        switch (value) {
            case 'C':
                this.clear();
                break;
            case '=':
                this.calculate();
                break;
            default:
                this.appendToExpression(value);
        }
    }
}
'''

        files["frontend/js/app.js"] = '''// Main application entry point
document.addEventListener('DOMContentLoaded', () => {
    const calculator = new CalculatorUI();
    const buttonGrid = document.getElementById('button-grid');

    // Define calculator buttons
    const buttons = [
        'C', '(', ')', '/',
        '7', '8', '9', '*',
        '4', '5', '6', '-',
        '1', '2', '3', '+',
        '0', '.', '='
    ];

    // Create buttons
    buttons.forEach(value => {
        const button = document.createElement('button');
        button.className = 'button';
        button.textContent = value;

        // Add special classes
        if (['+', '-', '*', '/'].includes(value)) {
            button.classList.add('operator');
        } else if (value === '=') {
            button.classList.add('equals');
        } else if (value === 'C') {
            button.classList.add('clear');
        }

        // Add click handler
        button.addEventListener('click', () => {
            calculator.handleButtonClick(value);
        });

        buttonGrid.appendChild(button);
    });

    // Add keyboard support
    document.addEventListener('keydown', (event) => {
        const key = event.key;
        const validKeys = {
            'Enter': '=',
            'Escape': 'C',
            'Backspace': 'C',
            '+': '+',
            '-': '-',
            '*': '*',
            '/': '/',
            '.': '.',
            '(': '(',
            ')': ')'
        };

        if (key >= '0' && key <= '9') {
            calculator.handleButtonClick(key);
        } else if (validKeys[key]) {
            calculator.handleButtonClick(validKeys[key]);
        }
    });
});
'''

        return files
    
    def _generate_calculator_logic_files(self, feature: Dict[str, Any],
                                       architecture: Dict[str, Any],
                                       test_analysis: Dict[str, Any]) -> Dict[str, str]:
        """Generate calculator logic files"""
        # Most logic is already in calculator.py from backend
        # This could generate additional calculation modules
        files = {}
        
        # Advanced operations module
        files["backend/advanced_calculator.py"] = '''"""Advanced calculator operations"""
import math


class AdvancedCalculator:
    """Advanced mathematical operations"""
    
    @staticmethod
    def square_root(n: float) -> float:
        """Calculate square root"""
        if n < 0:
            raise ValueError("Cannot calculate square root of negative number")
        return math.sqrt(n)
    
    @staticmethod
    def power(base: float, exponent: float) -> float:
        """Calculate power"""
        return math.pow(base, exponent)
    
    @staticmethod
    def percentage(value: float, percentage: float) -> float:
        """Calculate percentage"""
        return (value * percentage) / 100
    
    @staticmethod
    def factorial(n: int) -> int:
        """Calculate factorial"""
        if n < 0:
            raise ValueError("Cannot calculate factorial of negative number")
        if n > 20:
            raise ValueError("Factorial too large")
        return math.factorial(int(n))
'''

        return files
    
    def _generate_generic_implementation_files(self, feature: Dict[str, Any],
                                             test_analysis: Dict[str, Any]) -> Dict[str, str]:
        """Generate generic implementation for unknown features"""
        files = {}
        
        # Create a basic implementation file
        feature_name = feature.get("title", "feature").lower().replace(" ", "_")
        
        files[f"{feature_name}.py"] = f'''"""Implementation for {feature.get("title", "feature")}"""


class {self._to_class_name(feature.get("title", "Feature"))}:
    """Implementation of {feature.get("title", "feature")}"""
    
    def __init__(self):
        """Initialize {feature.get("title", "feature")}"""
        # TODO: Initialize based on requirements
        pass
    
    # TODO: Implement methods based on test requirements
    # Components to implement: {", ".join(feature.get("components", []))}
'''
        
        return files
    
    def _generate_simple_implementation(self, test_analysis: Dict[str, Any]) -> Dict[str, str]:
        """Generate simple implementation based only on test analysis"""
        files = {}
        
        # Create implementation for each test class
        for test_class in test_analysis["test_classes"]:
            if test_class.startswith("Test"):
                class_name = test_class[4:]  # Remove "Test" prefix
            else:
                class_name = test_class
            
            files[f"{class_name.lower()}.py"] = f'''"""Implementation for {class_name}"""


class {class_name}:
    """Auto-generated implementation for {class_name}"""
    
    def __init__(self):
        """Initialize {class_name}"""
        pass
    
    # TODO: Implement methods based on test assertions
'''
        
        return files
    
    def _to_class_name(self, text: str) -> str:
        """Convert text to ClassName format"""
        words = text.split()
        return ''.join(word.capitalize() for word in words)
    
    def get_implementation_files(self) -> Dict[str, str]:
        """Get the generated implementation files"""
        return getattr(self, '_implementation_files', {})