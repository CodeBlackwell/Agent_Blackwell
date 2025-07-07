"""
Tests for RequirementsExpander
"""
import pytest
from workflows.mvp_incremental.requirements_expander import RequirementsExpander


class TestRequirementsExpander:
    """Test the requirements expansion functionality"""
    
    def test_detect_vague_requirements(self):
        """Test detection of vague requirements"""
        vague_requirements = [
            "Create a REST API",
            "Build a web app",
            "Make a CLI tool",
            "Implement an API",
            "Develop a simple application"
        ]
        
        for req in vague_requirements:
            assert RequirementsExpander._is_vague(req) == True, f"Should detect '{req}' as vague"
        
        detailed_requirements = [
            """Create a REST API with user authentication, task management endpoints,
            database persistence, input validation, and comprehensive error handling""",
            
            """Build a web application with React frontend, Node.js backend,
            user authentication, real-time updates, and PostgreSQL database""",
            
            """Develop a CLI tool for file processing with commands for compress,
decompress, encrypt, decrypt, and batch operations with progress tracking"""
        ]
        
        for req in detailed_requirements:
            assert RequirementsExpander._is_vague(req) == False, f"Should not detect as vague: {req[:50]}..."
    
    def test_project_type_detection(self):
        """Test correct project type detection"""
        test_cases = [
            ("Create a REST API for managing tasks", "rest_api"),
            ("Build a RESTful API with CRUD operations", "rest_api"),
            ("Implement an HTTP API endpoint", "rest_api"),
            ("Create a web application with React", "web_app"),
            ("Build a website with frontend and backend", "web_app"),
            ("Make a Vue.js web app", "web_app"),
            ("Create a CLI tool for file processing", "cli_tool"),
            ("Build a command line utility", "cli_tool"),
            ("Make a terminal application", "cli_tool")
        ]
        
        for req, expected_type in test_cases:
            detected_type = RequirementsExpander._detect_project_type(req)
            assert detected_type == expected_type, f"Expected {expected_type} for '{req}', got {detected_type}"
    
    def test_expand_vague_api_requirement(self):
        """Test expansion of vague API requirement"""
        original = "Create a REST API"
        expanded, was_expanded = RequirementsExpander.expand_requirements(original)
        
        assert was_expanded == True
        assert len(expanded) > len(original) * 10  # Should be much longer
        
        # Check for key sections
        assert "Project Setup and Configuration" in expanded
        assert "Data Models and Database" in expanded
        assert "Authentication and Authorization" in expanded
        assert "Core API Endpoints" in expanded
        assert "Input Validation and Error Handling" in expanded
        assert "Testing Suite" in expanded
        assert "API Documentation" in expanded
    
    def test_expand_vague_web_app_requirement(self):
        """Test expansion of vague web app requirement"""
        original = "Build a web app"
        expanded, was_expanded = RequirementsExpander.expand_requirements(original)
        
        assert was_expanded == True
        assert len(expanded) > len(original) * 10
        
        # Check for key sections
        assert "Frontend Setup" in expanded
        assert "UI Components and Layout" in expanded
        assert "Backend API" in expanded
        assert "State Management" in expanded
        assert "Testing and Quality" in expanded
    
    def test_expand_vague_cli_requirement(self):
        """Test expansion of vague CLI requirement"""
        original = "Make a CLI tool"
        expanded, was_expanded = RequirementsExpander.expand_requirements(original)
        
        assert was_expanded == True
        assert len(expanded) > len(original) * 10
        
        # Check for key sections
        assert "CLI Framework Setup" in expanded
        assert "Core Commands" in expanded
        assert "Input/Output Handling" in expanded
        assert "Configuration Management" in expanded
        assert "Error Handling and Logging" in expanded
        assert "Testing and Documentation" in expanded
    
    def test_no_expansion_for_detailed_requirements(self):
        """Test that detailed requirements are not expanded"""
        detailed = """
        Create a task management API with the following endpoints:
        - POST /auth/register - User registration
        - POST /auth/login - User login with JWT
        - GET /tasks - List user's tasks with pagination
        - POST /tasks - Create new task
        - PUT /tasks/:id - Update task
        - DELETE /tasks/:id - Delete task
        
        Include proper validation, error handling, and unit tests.
        """
        
        expanded, was_expanded = RequirementsExpander.expand_requirements(detailed)
        
        assert was_expanded == False
        assert expanded == detailed
    
    def test_extract_key_requirements(self):
        """Test extraction of key requirement points"""
        expanded = """
1. **Project Setup**
   - Details here
   
2. **Database Models**
   - More details
   
3. **API Endpoints**
   - Even more details
"""
        
        key_points = RequirementsExpander.extract_key_requirements(expanded)
        
        assert len(key_points) == 3
        assert "Project Setup" in key_points
        assert "Database Models" in key_points
        assert "API Endpoints" in key_points
    
    def test_generic_expansion_fallback(self):
        """Test generic expansion for unclear project types"""
        # Requirement that doesn't clearly match any project type
        vague = "Create a program"  # More neutral requirement
        expanded, was_expanded = RequirementsExpander.expand_requirements(vague)
        
        assert was_expanded == True
        # Should use generic expansion
        assert ("Project Setup" in expanded or 
                "Frontend Setup" in expanded or
                "CLI Framework Setup" in expanded)
        assert ("Testing" in expanded or 
                "Testing and Quality" in expanded or
                "Testing and Documentation" in expanded)
        assert len(expanded) > len(vague) * 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])