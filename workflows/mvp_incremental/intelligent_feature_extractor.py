"""
Intelligent Feature Extractor for MVP Incremental Workflow
Handles vague requirements and expands them into comprehensive feature sets
"""
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from workflows.mvp_incremental.testable_feature_parser import TestableFeature, TestCriteria, parse_testable_features
from workflows.logger import workflow_logger as logger


# Common project templates
PROJECT_TEMPLATES = {
    "rest_api": {
        "features": [
            {
                "title": "Project Setup and Configuration",
                "description": "Initialize project structure with dependencies and configuration management",
                "components": ["app structure", "config files", "dependencies", "environment setup"],
                "complexity": "Low"
            },
            {
                "title": "Database Models and Schema",
                "description": "Create data models, database schema, and ORM setup",
                "components": ["user model", "resource models", "database migrations", "relationships"],
                "complexity": "Medium"
            },
            {
                "title": "Authentication System",
                "description": "Implement user authentication with JWT tokens",
                "components": ["login endpoint", "register endpoint", "token generation", "password hashing"],
                "complexity": "High"
            },
            {
                "title": "CRUD API Endpoints",
                "description": "Create RESTful endpoints for resource management",
                "components": ["create endpoint", "read endpoints", "update endpoint", "delete endpoint"],
                "complexity": "Medium"
            },
            {
                "title": "Input Validation and Error Handling",
                "description": "Add request validation, error responses, and exception handling",
                "components": ["request schemas", "validation middleware", "error handlers", "status codes"],
                "complexity": "Medium"
            },
            {
                "title": "API Testing Suite",
                "description": "Write comprehensive unit and integration tests",
                "components": ["unit tests", "integration tests", "test fixtures", "test client"],
                "complexity": "Medium"
            },
            {
                "title": "API Documentation",
                "description": "Generate OpenAPI/Swagger documentation",
                "components": ["endpoint docs", "schema docs", "example requests", "README"],
                "complexity": "Low"
            }
        ]
    },
    "web_app": {
        "features": [
            {
                "title": "Frontend Setup",
                "description": "Initialize frontend framework and build configuration",
                "components": ["React/Vue setup", "webpack config", "development server", "dependencies"],
                "complexity": "Low"
            },
            {
                "title": "UI Components",
                "description": "Create reusable UI components and layouts",
                "components": ["header", "navigation", "forms", "buttons", "layout"],
                "complexity": "Medium"
            },
            {
                "title": "State Management",
                "description": "Implement application state management",
                "components": ["store setup", "actions", "reducers", "context"],
                "complexity": "Medium"
            },
            {
                "title": "Backend API",
                "description": "Create backend API for data operations",
                "components": ["server setup", "routes", "controllers", "database"],
                "complexity": "High"
            },
            {
                "title": "User Interface Pages",
                "description": "Build main application pages",
                "components": ["home page", "list page", "detail page", "forms"],
                "complexity": "Medium"
            },
            {
                "title": "Testing",
                "description": "Add frontend and backend tests",
                "components": ["component tests", "integration tests", "e2e tests"],
                "complexity": "Medium"
            }
        ]
    },
    "cli_tool": {
        "features": [
            {
                "title": "CLI Framework Setup",
                "description": "Initialize CLI tool with argument parsing",
                "components": ["main entry", "argument parser", "help system", "config"],
                "complexity": "Low"
            },
            {
                "title": "Core Commands",
                "description": "Implement main CLI commands",
                "components": ["command handlers", "subcommands", "options", "flags"],
                "complexity": "Medium"
            },
            {
                "title": "Input/Output Handling",
                "description": "Handle file I/O and console output",
                "components": ["file readers", "output formatters", "progress bars", "colors"],
                "complexity": "Medium"
            },
            {
                "title": "Configuration Management",
                "description": "Add configuration file support",
                "components": ["config parser", "defaults", "user settings", "validation"],
                "complexity": "Low"
            },
            {
                "title": "Error Handling",
                "description": "Implement robust error handling and logging",
                "components": ["exception handlers", "logging", "debug mode", "error messages"],
                "complexity": "Low"
            },
            {
                "title": "Testing and Documentation",
                "description": "Add tests and user documentation",
                "components": ["unit tests", "integration tests", "man page", "examples"],
                "complexity": "Medium"
            }
        ]
    }
}


class IntelligentFeatureExtractor:
    """
    Extracts features from design output using multiple strategies.
    Handles vague requirements by expanding them into comprehensive feature sets.
    """
    
    @staticmethod
    def extract_features(plan: str, design: str, requirements: str) -> List[Dict[str, Any]]:
        """
        Extract features using multiple strategies.
        
        Args:
            plan: The planner agent's output
            design: The designer agent's output
            requirements: The original user requirements
            
        Returns:
            List of feature dictionaries
        """
        features = []
        
        # Strategy 1: Try standard FEATURE[n] extraction
        logger.info("Attempting standard feature extraction...")
        features = parse_testable_features(design)
        
        # Strategy 2: If only one feature, check if we need expansion
        if len(features) <= 1:
            logger.warning(f"Only {len(features)} feature(s) found, attempting expansion...")
            
            # Detect project type
            project_type = IntelligentFeatureExtractor._detect_project_type(requirements, plan, design)
            logger.info(f"Detected project type: {project_type}")
            
            if project_type and IntelligentFeatureExtractor._is_vague_requirement(requirements):
                # Expand using template
                logger.info(f"Expanding features using {project_type} template")
                features = IntelligentFeatureExtractor._expand_using_template(
                    project_type, plan, design, features
                )
            else:
                # Try extracting from task breakdown
                logger.info("Attempting to extract features from task breakdown...")
                task_features = IntelligentFeatureExtractor._extract_from_task_breakdown(plan)
                if len(task_features) > len(features):
                    features = task_features
        
        # Strategy 3: Ensure minimum features for API projects (only if requirements are vague)
        if (IntelligentFeatureExtractor._is_api_project(requirements, plan, design) and 
            IntelligentFeatureExtractor._is_vague_requirement(requirements)):
            min_features = 5
            if len(features) < min_features:
                logger.warning(f"Vague API project has only {len(features)} features, expanding to {min_features}...")
                features = IntelligentFeatureExtractor._ensure_api_completeness(features, plan, design)
        
        # Add feature IDs if missing
        for i, feature in enumerate(features):
            if 'id' not in feature:
                feature['id'] = f"feature_{i + 1}"
        
        logger.info(f"Final feature count: {len(features)}")
        return features
    
    @staticmethod
    def _detect_project_type(requirements: str, plan: str, design: str) -> Optional[str]:
        """Detect the type of project from requirements and plans."""
        combined_text = f"{requirements} {plan} {design}".lower()
        
        # Check for REST API indicators
        api_keywords = ["rest api", "restful", "api endpoint", "crud api", "http api", "web api"]
        if any(keyword in combined_text for keyword in api_keywords):
            return "rest_api"
        
        # Check for web app indicators
        web_keywords = ["web application", "web app", "frontend", "ui components", "react app", "vue app"]
        if any(keyword in combined_text for keyword in web_keywords):
            return "web_app"
        
        # Check for CLI tool indicators
        cli_keywords = ["cli tool", "command line", "terminal app", "console application", "cli utility"]
        if any(keyword in combined_text for keyword in cli_keywords):
            return "cli_tool"
        
        # Check for generic API
        if "api" in combined_text and any(word in combined_text for word in ["create", "build", "implement"]):
            return "rest_api"
        
        return None
    
    @staticmethod
    def _is_vague_requirement(requirements: str) -> bool:
        """Check if requirements are too vague and need expansion."""
        # Remove whitespace and check length
        clean_req = requirements.strip()
        
        # Very short requirements are likely vague
        if len(clean_req) < 100:
            return True
        
        # Check for vague patterns
        vague_patterns = [
            r"^create\s+(?:a\s+)?(?:simple\s+)?(?:rest\s+)?api$",
            r"^build\s+(?:a\s+)?web\s+app$",
            r"^make\s+(?:a\s+)?cli\s+tool$",
            r"^implement\s+(?:a\s+)?.*?(?:api|app|tool)$"
        ]
        
        for pattern in vague_patterns:
            if re.match(pattern, clean_req, re.IGNORECASE):
                return True
        
        # Count specific features mentioned
        feature_words = ["endpoint", "model", "schema", "authentication", "database", "crud", "test"]
        feature_count = sum(1 for word in feature_words if word in clean_req.lower())
        
        # If few specific features mentioned, it's vague
        return feature_count < 2
    
    @staticmethod
    def _is_api_project(requirements: str, plan: str, design: str) -> bool:
        """Check if this is an API project."""
        combined_text = f"{requirements} {plan} {design}".lower()
        api_indicators = ["api", "endpoint", "rest", "http", "crud", "swagger", "openapi"]
        return sum(1 for indicator in api_indicators if indicator in combined_text) >= 2
    
    @staticmethod
    def _expand_using_template(
        project_type: str, 
        plan: str, 
        design: str, 
        existing_features: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Expand features using project template."""
        if project_type not in PROJECT_TEMPLATES:
            return existing_features
        
        template = PROJECT_TEMPLATES[project_type]
        expanded_features = []
        
        for i, template_feature in enumerate(template["features"], 1):
            # Create testable feature
            test_criteria = TestCriteria(
                description=template_feature["description"],
                input_examples=[{"component": comp} for comp in template_feature["components"][:2]],
                expected_outputs=[f"{comp} implemented" for comp in template_feature["components"][:2]],
                edge_cases=[f"Invalid {template_feature['title'].lower()}", "Missing configuration"],
                error_conditions=["Configuration error", "Import error"]
            )
            
            # Determine dependencies
            dependencies = []
            if i > 1:  # All features depend on setup
                dependencies.append("feature_1")
            if "auth" in template_feature["title"].lower() and i > 2:
                dependencies.append("feature_2")  # Auth depends on models
            
            feature = {
                "id": f"feature_{i}",
                "title": template_feature["title"],
                "description": template_feature["description"],
                "test_criteria": {
                    "description": test_criteria.description,
                    "input_examples": test_criteria.input_examples,
                    "expected_outputs": test_criteria.expected_outputs,
                    "edge_cases": test_criteria.edge_cases,
                    "error_conditions": test_criteria.error_conditions
                },
                "dependencies": dependencies,
                "complexity": template_feature.get("complexity", "Medium")
            }
            
            expanded_features.append(feature)
        
        return expanded_features
    
    @staticmethod
    def _extract_from_task_breakdown(plan: str) -> List[Dict[str, Any]]:
        """Extract features from planner's task breakdown."""
        features = []
        
        # Look for numbered tasks or sections
        task_patterns = [
            r'(?:^|\n)\s*(?:Task\s+)?(\d+)[\.)]\s*([^\n]+)',
            r'(?:^|\n)\s*[-*]\s+([^\n]+)',
            r'(?:^|\n)\s*(?:Step\s+)?(\d+):\s*([^\n]+)'
        ]
        
        for pattern in task_patterns:
            matches = re.findall(pattern, plan, re.MULTILINE)
            if matches:
                for match in matches:
                    if isinstance(match, tuple):
                        title = match[-1]  # Last group is usually the title
                    else:
                        title = match
                    
                    # Filter out non-feature items
                    if any(skip in title.lower() for skip in ['risk', 'timeline', 'overview', 'summary']):
                        continue
                    
                    # Create feature from task
                    feature = {
                        "id": f"feature_{len(features) + 1}",
                        "title": title.strip()[:100],
                        "description": title.strip(),
                        "test_criteria": {
                            "description": f"Implement and test {title.strip()}",
                            "input_examples": [{"task": "implementation"}],
                            "expected_outputs": ["Task completed successfully"],
                            "edge_cases": ["Edge case handling"],
                            "error_conditions": ["Error handling"]
                        },
                        "dependencies": []
                    }
                    features.append(feature)
        
        return features
    
    @staticmethod
    def _ensure_api_completeness(
        features: List[Dict[str, Any]], 
        plan: str, 
        design: str
    ) -> List[Dict[str, Any]]:
        """Ensure API projects have all essential features."""
        # Check what's already covered
        existing_titles = [f.get('title', '').lower() for f in features]
        
        # Essential API features
        essential_features = [
            ("Setup", "Project setup and configuration"),
            ("Models", "Database models and schema"),
            ("Auth", "Authentication and authorization"),
            ("CRUD", "CRUD endpoints for resources"),
            ("Validation", "Input validation and error handling"),
            ("Tests", "API testing suite"),
            ("Docs", "API documentation")
        ]
        
        # Add missing essential features
        for keyword, full_title in essential_features:
            if not any(keyword.lower() in title for title in existing_titles):
                feature = {
                    "id": f"feature_{len(features) + 1}",
                    "title": full_title,
                    "description": f"Implement {full_title.lower()} for the API",
                    "test_criteria": {
                        "description": f"Test {full_title.lower()}",
                        "input_examples": [{"test": "implementation"}],
                        "expected_outputs": ["Feature working correctly"],
                        "edge_cases": ["Edge cases handled"],
                        "error_conditions": ["Errors handled gracefully"]
                    },
                    "dependencies": []
                }
                features.append(feature)
        
        return features