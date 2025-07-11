"""Planner Agent Adapter for Flagship TDD Workflow"""

import asyncio
from typing import AsyncGenerator, Dict, Any
import json

from models.flagship_models import AgentType


class PlannerFlagship:
    """Adapter for planner agent to work with Flagship TDD workflow"""
    
    def __init__(self):
        self.agent_type = AgentType.PLANNER
    
    async def analyze_requirements(self, requirements: str, context: Dict[str, Any] = None) -> AsyncGenerator[str, None]:
        """
        Analyze and expand requirements into detailed project plan
        
        Args:
            requirements: The project requirements to analyze
            context: Additional context
            
        Yields:
            Analysis results and expanded requirements
        """
        yield f"📋 Analyzing requirements: {requirements}\n\n"
        
        # Analyze project type
        project_type = self._identify_project_type(requirements)
        yield f"Identified project type: {project_type}\n\n"
        
        # Expand requirements based on type
        if "calculator" in requirements.lower() and "front end" in requirements.lower() and "back end" in requirements.lower():
            yield "📊 Expanding requirements for full-stack calculator application...\n\n"
            
            expanded = self._expand_calculator_app_requirements()
            
            yield "## Expanded Requirements\n\n"
            yield "### Project Overview\n"
            yield "A full-stack calculator application with separate frontend and backend components.\n\n"
            
            yield "### Technical Architecture\n"
            yield "- **Frontend**: HTML/CSS/JavaScript for user interface\n"
            yield "- **Backend**: Python Flask API for calculation logic\n"
            yield "- **API**: RESTful endpoints for calculation operations\n\n"
            
            yield "### Feature Breakdown\n\n"
            for i, feature in enumerate(expanded["features"], 1):
                yield f"#### Feature {i}: {feature['title']}\n"
                yield f"**Description**: {feature['description']}\n"
                yield f"**Components**:\n"
                for component in feature['components']:
                    yield f"  - {component}\n"
                yield f"**Complexity**: {feature['complexity']}\n\n"
            
            yield "### Technical Requirements\n"
            for req in expanded["technical_requirements"]:
                yield f"- {req}\n"
            yield "\n"
            
            yield "### Non-Functional Requirements\n"
            for req in expanded["non_functional_requirements"]:
                yield f"- {req}\n"
            yield "\n"
            
            # Store the expanded requirements for later use
            self._expanded_requirements = expanded
        else:
            # Generic web app expansion
            yield "📊 Expanding requirements for web application...\n\n"
            
            expanded = self._expand_generic_web_app_requirements(requirements)
            
            yield "## Expanded Requirements\n\n"
            yield "### Project Overview\n"
            yield f"{requirements}\n\n"
            
            yield "### Feature Breakdown\n\n"
            for i, feature in enumerate(expanded["features"], 1):
                yield f"#### Feature {i}: {feature['title']}\n"
                yield f"**Description**: {feature['description']}\n"
                yield f"**Components**:\n"
                for component in feature['components']:
                    yield f"  - {component}\n"
                yield f"**Complexity**: {feature['complexity']}\n\n"
            
            yield "### Technical Requirements\n"
            for req in expanded["technical_requirements"]:
                yield f"- {req}\n"
            yield "\n"
            
            # Store the expanded requirements for later use
            self._expanded_requirements = expanded
    
    def _identify_project_type(self, requirements: str) -> str:
        """Identify the type of project from requirements"""
        req_lower = requirements.lower()
        
        if "api" in req_lower and "rest" in req_lower:
            return "rest_api"
        elif any(word in req_lower for word in ["web", "frontend", "backend", "app", "application"]):
            return "web_app"
        elif "cli" in req_lower or "command" in req_lower:
            return "cli_tool"
        elif "calculator" in req_lower:
            return "calculator_app"
        elif "todo" in req_lower:
            return "todo_app"
        else:
            return "generic"
    
    def _expand_generic_web_app_requirements(self, requirements: str) -> Dict[str, Any]:
        """Expand requirements for a generic web application"""
        # Extract key entities from requirements
        req_lower = requirements.lower()
        
        # Determine app name and main entity
        app_name = "Web Application"
        main_entity = "item"
        
        if "todo" in req_lower:
            app_name = "Todo List Application"
            main_entity = "todo"
        elif "blog" in req_lower:
            app_name = "Blog Application"
            main_entity = "post"
        elif "user" in req_lower:
            app_name = "User Management Application"
            main_entity = "user"
        
        return {
            "project_type": "web_app",
            "features": [
                {
                    "id": "feature_1",
                    "title": "Project Setup and Structure",
                    "description": f"Initialize {app_name} with proper directory structure",
                    "components": [
                        "Directory structure (frontend/, backend/, tests/)",
                        "Configuration files",
                        "Package management setup",
                        "Environment configuration"
                    ],
                    "complexity": "low"
                },
                {
                    "id": "feature_2",
                    "title": "Backend API Development",
                    "description": f"Create REST API for {main_entity} management",
                    "components": [
                        "Flask/FastAPI server setup",
                        f"CRUD endpoints for {main_entity}s",
                        "Data models and schemas",
                        "Database integration",
                        "Input validation"
                    ],
                    "complexity": "medium"
                },
                {
                    "id": "feature_3",
                    "title": "Frontend User Interface",
                    "description": f"Build interactive UI for {app_name}",
                    "components": [
                        "HTML structure and layout",
                        "CSS styling and responsive design",
                        "JavaScript for interactivity",
                        "API integration layer",
                        "Form handling and validation"
                    ],
                    "complexity": "medium"
                },
                {
                    "id": "feature_4",
                    "title": "Core Functionality Implementation",
                    "description": f"Implement main {main_entity} operations",
                    "components": [
                        f"Create new {main_entity}s",
                        f"Read/display {main_entity}s",
                        f"Update existing {main_entity}s",
                        f"Delete {main_entity}s",
                        "Search and filtering"
                    ],
                    "complexity": "medium"
                },
                {
                    "id": "feature_5",
                    "title": "Testing and Quality Assurance",
                    "description": "Comprehensive testing for all components",
                    "components": [
                        "Backend unit tests",
                        "API integration tests",
                        "Frontend component tests",
                        "End-to-end tests",
                        "Error handling tests"
                    ],
                    "complexity": "medium"
                }
            ],
            "technical_requirements": [
                "Python 3.8+ for backend development",
                "HTML5, CSS3, and ES6+ JavaScript for frontend",
                "RESTful API design principles",
                "JSON data exchange format",
                "Cross-Origin Resource Sharing (CORS) configuration",
                "Environment-based configuration",
                "Error handling and logging"
            ],
            "non_functional_requirements": [
                "Responsive design for multiple screen sizes",
                "Clean and intuitive user interface",
                "Fast page load times",
                "Proper error messages and user feedback",
                "Code documentation and comments",
                "Modular and maintainable code structure"
            ]
        }
    
    def _expand_calculator_app_requirements(self) -> Dict[str, Any]:
        """Expand requirements for calculator app"""
        return {
            "project_type": "web_app",
            "features": [
                {
                    "id": "feature_1",
                    "title": "Project Setup and Structure",
                    "description": "Initialize project with proper structure for frontend and backend",
                    "components": [
                        "Directory structure (frontend/, backend/, tests/)",
                        "Package configuration files",
                        "Environment setup",
                        "Development server configuration"
                    ],
                    "complexity": "Low"
                },
                {
                    "id": "feature_2", 
                    "title": "Calculator Backend API",
                    "description": "Create REST API with calculation endpoints",
                    "components": [
                        "Flask server setup",
                        "Calculator logic module",
                        "API endpoints (/calculate, /operations)",
                        "Input validation",
                        "Error handling"
                    ],
                    "complexity": "Medium"
                },
                {
                    "id": "feature_3",
                    "title": "Calculator Frontend UI",
                    "description": "Build interactive calculator user interface",
                    "components": [
                        "HTML structure with calculator layout",
                        "CSS styling for calculator buttons and display",
                        "JavaScript for user interactions",
                        "API integration for calculations",
                        "Result display and error handling"
                    ],
                    "complexity": "Medium"
                },
                {
                    "id": "feature_4",
                    "title": "Calculator Operations",
                    "description": "Implement core calculator functionality",
                    "components": [
                        "Basic operations (add, subtract, multiply, divide)",
                        "Advanced operations (square root, percentage)",
                        "Memory functions (M+, M-, MR, MC)",
                        "History tracking",
                        "Keyboard support"
                    ],
                    "complexity": "High"
                },
                {
                    "id": "feature_5",
                    "title": "Testing and Validation",
                    "description": "Comprehensive test coverage for all components",
                    "components": [
                        "Backend unit tests",
                        "API integration tests",
                        "Frontend component tests",
                        "End-to-end tests",
                        "Error scenario tests"
                    ],
                    "complexity": "Medium"
                }
            ],
            "technical_requirements": [
                "Python 3.8+ with Flask for backend",
                "Modern JavaScript (ES6+) for frontend",
                "RESTful API design principles",
                "Responsive design for different screen sizes",
                "Cross-browser compatibility",
                "Proper error handling and validation"
            ],
            "non_functional_requirements": [
                "Response time < 100ms for calculations",
                "Support for decimal precision up to 10 digits",
                "Accessible UI following WCAG guidelines",
                "Clear error messages for user guidance",
                "Clean, maintainable code structure"
            ]
        }
    
    def get_expanded_requirements(self) -> Dict[str, Any]:
        """Get the stored expanded requirements"""
        return getattr(self, '_expanded_requirements', {})