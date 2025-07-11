"""Designer Agent Adapter for Flagship TDD Workflow"""

import asyncio
from typing import AsyncGenerator, Dict, Any, List
import json

from models.flagship_models import AgentType


class DesignerFlagship:
    """Adapter for designer agent to work with Flagship TDD workflow"""
    
    def __init__(self):
        self.agent_type = AgentType.DESIGNER
    
    async def design_architecture(self, requirements: str, expanded_requirements: Dict[str, Any] = None, 
                                 context: Dict[str, Any] = None) -> AsyncGenerator[str, None]:
        """
        Design system architecture based on requirements
        
        Args:
            requirements: Original requirements
            expanded_requirements: Expanded requirements from planner
            context: Additional context
            
        Yields:
            Architecture design and file structure
        """
        yield f"🏗️ Designing architecture for: {requirements}\n\n"
        
        project_type = expanded_requirements.get("project_type", "web_app") if expanded_requirements else "web_app"
        
        if "calculator" in requirements.lower():
            yield "## System Architecture Design\n\n"
            
            # Generate architecture
            architecture = self._design_calculator_architecture()
            
            yield "### Technology Stack\n"
            for layer, tech in architecture["technology_stack"].items():
                yield f"- **{layer.title()}**: {tech}\n"
            yield "\n"
            
            yield "### Component Architecture\n\n"
            for component in architecture["components"]:
                yield f"#### {component['name']}\n"
                yield f"**Type**: {component['type']}\n"
                yield f"**Description**: {component['description']}\n"
                yield f"**Files**:\n"
                for file in component['files']:
                    yield f"  - {file}\n"
                if component.get('interfaces'):
                    yield f"**Interfaces**:\n"
                    for interface in component['interfaces']:
                        yield f"  - {interface}\n"
                yield "\n"
            
            yield "### Project Structure\n```\n"
            yield self._generate_tree_structure(architecture["structure"])
            yield "```\n\n"
            
            yield "### API Design\n\n"
            for api in architecture["api_contracts"]:
                yield f"#### {api['method']} {api['path']}\n"
                yield f"**Description**: {api['description']}\n"
                if api.get('request_schema'):
                    yield f"**Request Body**:\n```json\n{json.dumps(api['request_schema'], indent=2)}\n```\n"
                if api.get('response_schema'):
                    yield f"**Response**:\n```json\n{json.dumps(api['response_schema'], indent=2)}\n```\n"
                yield "\n"
            
            yield "### File Templates\n\n"
            # Generate file templates
            templates = self._generate_file_templates(architecture)
            for filename, content in templates.items():
                yield f"#### FILE: {filename}\n"
                yield "```" + self._get_file_language(filename) + "\n"
                yield content
                yield "```\n\n"
            
            # Store architecture for later use
            self._architecture = architecture
        else:
            yield "🏗️ Designing generic architecture...\n"
            yield "Please provide more specific requirements for detailed architecture.\n"
    
    def _design_calculator_architecture(self) -> Dict[str, Any]:
        """Design architecture for calculator app"""
        return {
            "project_type": "web_app",
            "technology_stack": {
                "frontend": "HTML5/CSS3/Vanilla JavaScript",
                "backend": "Python 3.8+ with Flask 2.0+",
                "testing": "pytest for backend, Jest for frontend",
                "deployment": "Docker containers"
            },
            "structure": {
                "frontend": [
                    "index.html",
                    "css/style.css", 
                    "js/app.js",
                    "js/calculator.js",
                    "js/api.js"
                ],
                "backend": [
                    "app.py",
                    "calculator.py",
                    "api/routes.py",
                    "api/validators.py",
                    "config.py"
                ],
                "tests": [
                    "test_calculator.py",
                    "test_api.py",
                    "test_integration.py",
                    "frontend/test_calculator.js"
                ],
                "config": [
                    "requirements.txt",
                    "package.json",
                    ".env.example",
                    "Dockerfile",
                    "docker-compose.yml"
                ]
            },
            "components": [
                {
                    "name": "Frontend UI",
                    "type": "frontend",
                    "description": "Calculator user interface with responsive design",
                    "files": ["index.html", "css/style.css", "js/app.js", "js/calculator.js"],
                    "interfaces": ["DOM manipulation", "Event handling", "API calls"]
                },
                {
                    "name": "API Client",
                    "type": "frontend",
                    "description": "JavaScript module for backend communication",
                    "files": ["js/api.js"],
                    "interfaces": ["HTTP requests", "Response handling", "Error management"]
                },
                {
                    "name": "Flask Server",
                    "type": "backend",
                    "description": "REST API server with Flask",
                    "files": ["app.py", "config.py"],
                    "interfaces": ["HTTP endpoints", "CORS handling", "Request routing"]
                },
                {
                    "name": "Calculator Engine",
                    "type": "backend",
                    "description": "Core calculation logic",
                    "files": ["calculator.py"],
                    "interfaces": ["calculate()", "validate_expression()", "format_result()"]
                },
                {
                    "name": "API Routes",
                    "type": "backend",
                    "description": "REST API endpoint definitions",
                    "files": ["api/routes.py", "api/validators.py"],
                    "interfaces": ["/api/calculate", "/api/operations", "/api/history"]
                }
            ],
            "api_contracts": [
                {
                    "method": "POST",
                    "path": "/api/calculate",
                    "description": "Perform calculation",
                    "request_schema": {
                        "expression": "string",
                        "precision": "integer (optional)"
                    },
                    "response_schema": {
                        "result": "number",
                        "expression": "string",
                        "timestamp": "string"
                    },
                    "auth_required": False
                },
                {
                    "method": "GET",
                    "path": "/api/operations",
                    "description": "Get supported operations",
                    "response_schema": {
                        "operations": ["array of strings"],
                        "categories": {"basic": ["array"], "advanced": ["array"]}
                    },
                    "auth_required": False
                },
                {
                    "method": "GET",
                    "path": "/api/history",
                    "description": "Get calculation history",
                    "response_schema": {
                        "history": [
                            {
                                "expression": "string",
                                "result": "number",
                                "timestamp": "string"
                            }
                        ]
                    },
                    "auth_required": False
                }
            ],
            "dependencies": {
                "python": ["flask>=2.0.0", "flask-cors>=3.0.0", "python-dotenv>=0.19.0"],
                "javascript": ["jest", "eslint"],
                "deployment": ["docker", "docker-compose"]
            }
        }
    
    def _generate_tree_structure(self, structure: Dict[str, List[str]]) -> str:
        """Generate ASCII tree structure"""
        lines = []
        lines.append("calculator-app/")
        
        categories = list(structure.keys())
        for i, category in enumerate(categories):
            is_last_category = i == len(categories) - 1
            prefix = "└── " if is_last_category else "├── "
            lines.append(f"{prefix}{category}/")
            
            files = structure[category]
            for j, file in enumerate(files):
                is_last_file = j == len(files) - 1
                cat_prefix = "    " if is_last_category else "│   "
                file_prefix = "└── " if is_last_file else "├── "
                
                # Handle nested paths
                if "/" in file:
                    parts = file.split("/")
                    # First part (subdirectory)
                    if j == 0 or not files[j-1].startswith(parts[0]):
                        lines.append(f"{cat_prefix}├── {parts[0]}/")
                    # File in subdirectory
                    lines.append(f"{cat_prefix}│   └── {parts[1]}")
                else:
                    lines.append(f"{cat_prefix}{file_prefix}{file}")
        
        return "\n".join(lines)
    
    def _generate_file_templates(self, architecture: Dict[str, Any]) -> Dict[str, str]:
        """Generate starter templates for key files"""
        templates = {}
        
        # Backend app.py
        templates["backend/app.py"] = '''from flask import Flask, jsonify
from flask_cors import CORS
from api.routes import api_bp
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Register blueprints
app.register_blueprint(api_bp, url_prefix='/api')

@app.route('/')
def index():
    return jsonify({"message": "Calculator API", "version": "1.0.0"})

if __name__ == '__main__':
    app.run(debug=True)
'''
        
        # Calculator module
        templates["backend/calculator.py"] = '''"""Core calculator logic"""

class Calculator:
    """Calculator with basic and advanced operations"""
    
    def __init__(self):
        self.history = []
        self.memory = 0
    
    def calculate(self, expression: str) -> float:
        """
        Calculate mathematical expression
        Args:
            expression: Math expression as string
        Returns:
            Calculation result
        """
        # TODO: Implement safe expression evaluation
        pass
    
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
'''
        
        # Frontend HTML
        templates["frontend/index.html"] = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Calculator App</title>
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <div class="calculator">
        <div class="display">
            <input type="text" id="display" readonly value="0">
        </div>
        <div class="buttons">
            <!-- Calculator buttons will be generated by JavaScript -->
        </div>
    </div>
    
    <script src="js/api.js"></script>
    <script src="js/calculator.js"></script>
    <script src="js/app.js"></script>
</body>
</html>
'''
        
        # API routes
        templates["backend/api/routes.py"] = '''from flask import Blueprint, request, jsonify
from calculator import Calculator

api_bp = Blueprint('api', __name__)
calculator = Calculator()

@api_bp.route('/calculate', methods=['POST'])
def calculate():
    """Calculate expression endpoint"""
    try:
        data = request.get_json()
        expression = data.get('expression', '')
        
        # TODO: Validate and calculate expression
        result = calculator.calculate(expression)
        
        return jsonify({
            'result': result,
            'expression': expression,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@api_bp.route('/operations', methods=['GET'])
def get_operations():
    """Get supported operations"""
    return jsonify({
        'operations': ['+', '-', '*', '/', '^', '√', '%'],
        'categories': {
            'basic': ['+', '-', '*', '/'],
            'advanced': ['^', '√', '%']
        }
    })
'''
        
        return templates
    
    def _get_file_language(self, filename: str) -> str:
        """Get language identifier for syntax highlighting"""
        if filename.endswith('.py'):
            return 'python'
        elif filename.endswith('.js'):
            return 'javascript'
        elif filename.endswith('.html'):
            return 'html'
        elif filename.endswith('.css'):
            return 'css'
        elif filename.endswith('.json'):
            return 'json'
        else:
            return ''
    
    def get_architecture(self) -> Dict[str, Any]:
        """Get the stored architecture"""
        return getattr(self, '_architecture', {})