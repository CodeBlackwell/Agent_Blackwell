"""
Requirements Expander for MVP Incremental Workflow
Expands vague requirements into detailed specifications
"""
import re
from typing import Dict, List, Optional, Tuple
from workflows.logger import workflow_logger as logger


class RequirementsExpander:
    """
    Expands vague requirements into detailed specifications
    to help agents produce comprehensive implementations
    """
    
    # Templates for expanding common project types
    EXPANSION_TEMPLATES = {
        "rest_api": """
Create a production-ready REST API with the following features:

1. **Project Setup and Configuration**
   - Initialize the application framework (Flask/FastAPI/Express)
   - Set up configuration management for different environments
   - Create project structure with proper organization
   - Set up logging and error tracking

2. **Data Models and Database**
   - Design and implement data models/schemas
   - Set up database connections and ORM/ODM
   - Create database migrations or initialization scripts
   - Define relationships between entities

3. **Authentication and Authorization**
   - Implement user registration and login endpoints
   - Add JWT token generation and validation
   - Create middleware for protecting routes
   - Handle password hashing and security

4. **Core API Endpoints**
   - Implement CRUD operations for main resources
   - Add proper HTTP status codes and responses
   - Include pagination for list endpoints
   - Add filtering and sorting capabilities

5. **Input Validation and Error Handling**
   - Create request validation schemas
   - Implement global error handlers
   - Add input sanitization
   - Return consistent error responses

6. **Testing Suite**
   - Write unit tests for business logic
   - Create integration tests for API endpoints
   - Add test fixtures and utilities
   - Ensure good test coverage

7. **API Documentation**
   - Generate OpenAPI/Swagger documentation
   - Include example requests and responses
   - Document authentication requirements
   - Create a comprehensive README

Technical Requirements:
- Use appropriate HTTP methods (GET, POST, PUT, DELETE)
- Follow RESTful conventions
- Include proper CORS configuration
- Add rate limiting for production readiness
""",
        
        "web_app": """
Create a full-stack web application with the following components:

1. **Frontend Setup**
   - Initialize modern frontend framework (React/Vue/Angular)
   - Set up build tools and development server
   - Configure routing and navigation
   - Set up state management solution

2. **UI Components and Layout**
   - Create reusable UI components
   - Implement responsive layout system
   - Add navigation components
   - Style with CSS framework or custom styles

3. **Backend API**
   - Set up backend server
   - Create API endpoints for data operations
   - Implement database integration
   - Add authentication if needed

4. **Core Application Features**
   - Implement main application pages
   - Add data display and manipulation features
   - Create forms with validation
   - Handle user interactions

5. **State Management**
   - Set up application state management
   - Handle async data fetching
   - Manage UI state and user sessions
   - Implement data caching strategies

6. **Testing and Quality**
   - Write component tests
   - Add integration tests
   - Set up linting and formatting
   - Ensure accessibility standards

Technical Requirements:
- Responsive design for mobile and desktop
- Modern browser compatibility
- Optimized performance
- SEO considerations if applicable
""",
        
        "cli_tool": """
Create a command-line interface tool with the following features:

1. **CLI Framework Setup**
   - Initialize CLI framework (Click/argparse/Commander)
   - Set up main entry point
   - Configure command structure
   - Add help documentation system

2. **Core Commands**
   - Implement main command handlers
   - Add subcommands for different operations
   - Include command options and flags
   - Handle command arguments properly

3. **Input/Output Handling**
   - Read from files or stdin
   - Write to files or stdout
   - Add progress indicators for long operations
   - Include colored output for better UX

4. **Configuration Management**
   - Support configuration files
   - Allow environment variable overrides
   - Provide sensible defaults
   - Validate configuration values

5. **Error Handling and Logging**
   - Implement comprehensive error handling
   - Add debug mode with verbose output
   - Create helpful error messages
   - Log operations for troubleshooting

6. **Testing and Documentation**
   - Write unit tests for commands
   - Add integration tests
   - Create man page or help docs
   - Include usage examples

Technical Requirements:
- Cross-platform compatibility
- Efficient performance
- Intuitive command structure
- Proper exit codes
"""
    }
    
    @staticmethod
    def expand_requirements(original_requirements: str) -> Tuple[str, bool]:
        """
        Expand vague requirements into detailed specifications.
        
        Args:
            original_requirements: The original user requirements
            
        Returns:
            Tuple of (expanded_requirements, was_expanded)
        """
        # Check if requirements are vague
        if not RequirementsExpander._is_vague(original_requirements):
            logger.info("Requirements are already detailed, no expansion needed")
            return original_requirements, False
        
        logger.info("Vague requirements detected, expanding...")
        
        # Detect project type
        project_type = RequirementsExpander._detect_project_type(original_requirements)
        
        if project_type and project_type in RequirementsExpander.EXPANSION_TEMPLATES:
            logger.info(f"Detected project type: {project_type}")
            
            # Get the template
            template = RequirementsExpander.EXPANSION_TEMPLATES[project_type]
            
            # Combine original requirements with expanded template
            expanded = f"""
Original Request: {original_requirements}

Expanded Requirements:
{template}
"""
            
            return expanded.strip(), True
        else:
            # Try generic expansion
            logger.info("Using generic expansion for unclear project type")
            expanded = RequirementsExpander._generic_expansion(original_requirements)
            return expanded, True
    
    @staticmethod
    def _is_vague(requirements: str) -> bool:
        """Check if requirements are too vague"""
        # Remove extra whitespace
        clean_req = ' '.join(requirements.split())
        
        # Very short requirements are vague
        word_count = len(clean_req.split())
        if word_count < 10:
            return True
        
        # Check for vague patterns
        vague_patterns = [
            r"^create\s+(?:a\s+)?(?:simple\s+)?(?:rest\s+)?api$",
            r"^build\s+(?:a\s+)?web\s+app(?:lication)?$",
            r"^make\s+(?:a\s+)?cli\s+tool$",
            r"^implement\s+(?:a\s+)?(?:\w+\s+)?(?:api|app|tool)$",
            r"^develop\s+(?:a\s+)?(?:\w+\s+)?(?:api|application|tool)$"
        ]
        
        for pattern in vague_patterns:
            if re.match(pattern, clean_req.lower().strip()):
                return True
        
        # Count specific technical details
        detail_keywords = [
            "endpoint", "route", "database", "model", "schema", "authentication",
            "crud", "rest", "graphql", "component", "page", "feature",
            "command", "function", "class", "module", "test", "documentation",
            "validation", "error", "handling", "frontend", "backend", "jwt",
            "pagination", "real-time", "postgresql", "compress", "encrypt",
            "decrypt", "batch", "operations", "tracking", "progress"
        ]
        
        detail_count = sum(1 for keyword in detail_keywords if keyword in clean_req.lower())
        
        # If few technical details, it's vague
        # Also check for very specific multi-line requirements
        if '\n' in requirements and len(clean_req) > 100:
            return detail_count < 4
        return detail_count < 3
    
    @staticmethod
    def _detect_project_type(requirements: str) -> Optional[str]:
        """Detect the type of project from requirements"""
        req_lower = requirements.lower()
        
        # Check for API indicators
        api_keywords = ["api", "rest", "endpoint", "crud", "restful", "http"]
        api_score = sum(1 for kw in api_keywords if kw in req_lower)
        
        # Check for web app indicators  
        web_keywords = ["web app", "website", "frontend", "ui", "react", "vue", "angular", "web application"]
        web_score = sum(1 for kw in web_keywords if kw in req_lower)
        
        # Check for CLI indicators
        cli_keywords = ["cli", "command line", "terminal", "console", "script", "utility"]
        cli_score = sum(1 for kw in cli_keywords if kw in req_lower)
        
        # Determine project type by highest score
        scores = {
            "rest_api": api_score,
            "web_app": web_score,
            "cli_tool": cli_score
        }
        
        max_score = max(scores.values())
        if max_score > 0:
            return max(scores, key=scores.get)
        
        # Return None for unclear cases
        return None
    
    @staticmethod
    def _generic_expansion(requirements: str) -> str:
        """Generic expansion for unclear project types"""
        return f"""
Original Request: {requirements}

Expanded Requirements:

Based on your request, here's a comprehensive implementation plan:

1. **Project Setup**
   - Initialize project with appropriate framework
   - Set up development environment
   - Configure project structure
   - Add necessary dependencies

2. **Core Functionality**
   - Implement main features as requested
   - Create modular, reusable components
   - Follow best practices for the technology stack
   - Ensure proper separation of concerns

3. **Data Management**
   - Design data structures or models
   - Implement data persistence if needed
   - Add data validation
   - Handle data transformations

4. **User Interface/API**
   - Create appropriate interface (GUI, CLI, or API)
   - Implement input handling
   - Add output formatting
   - Ensure good user experience

5. **Error Handling and Validation**
   - Add comprehensive error handling
   - Validate all inputs
   - Provide helpful error messages
   - Handle edge cases gracefully

6. **Testing**
   - Write unit tests for core functionality
   - Add integration tests
   - Ensure good test coverage
   - Document test scenarios

7. **Documentation**
   - Create comprehensive README
   - Add inline code documentation
   - Include usage examples
   - Document configuration options

Technical Requirements:
- Follow coding best practices
- Ensure maintainable code structure
- Add appropriate logging
- Consider performance implications
"""
    
    @staticmethod
    def extract_key_requirements(expanded_requirements: str) -> List[str]:
        """Extract key requirement points from expanded requirements"""
        key_points = []
        
        # Look for numbered items
        numbered_pattern = r'^\d+\.\s+\*\*([^*]+)\*\*'
        matches = re.findall(numbered_pattern, expanded_requirements, re.MULTILINE)
        
        for match in matches:
            key_points.append(match.strip())
        
        return key_points