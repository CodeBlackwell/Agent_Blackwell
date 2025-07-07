"""
Unit tests for enhanced feature parser and intelligent extractor
"""
import pytest
from workflows.mvp_incremental.testable_feature_parser import TestableFeatureParser, parse_testable_features
from workflows.mvp_incremental.intelligent_feature_extractor import IntelligentFeatureExtractor


class TestEnhancedFeatureParser:
    """Test the enhanced TestableFeatureParser"""
    
    def test_parse_multiple_features(self):
        """Test parsing multiple FEATURE blocks correctly"""
        design_output = """
FEATURE[1]: Project Setup
Description: Initialize Flask application with configuration
Files: app.py, config.py, requirements.txt
Validation: Application starts without errors
Dependencies: None

FEATURE[2]: User Model
Description: Create User model with password hashing
Files: models/user.py, utils/security.py
Validation: User creation and password verification work
Dependencies: FEATURE[1]

FEATURE[3]: Authentication Endpoints
Description: Implement login and register endpoints
Files: routes/auth.py, schemas/auth.py
Validation: Users can register and login successfully
Dependencies: FEATURE[1], FEATURE[2]
"""
        features = parse_testable_features(design_output)
        
        assert len(features) == 3
        assert features[0]['id'] == 'feature_1'
        assert features[0]['title'] == 'Project Setup'
        assert features[1]['id'] == 'feature_2'
        assert features[1]['title'] == 'User Model'
        assert features[2]['dependencies'] == ['feature_1', 'feature_2']
    
    def test_force_extraction_when_standard_fails(self):
        """Test force extraction when standard pattern misses features"""
        # Simulate a case where features are not well-formatted
        design_output = """
The system will have multiple features:

FEATURE[1]: Basic Setup - Get the project running
Some description here without proper formatting

FEATURE[2]: Database Models
Another description

FEATURE[3]: API Endpoints
Final feature description
"""
        features = parse_testable_features(design_output)
        
        # Should extract all 3 features even with poor formatting
        assert len(features) >= 3
        assert any('Setup' in f['title'] for f in features)
        assert any('Database' in f['title'] for f in features)
        assert any('API' in f['title'] for f in features)
    
    def test_single_feature_detection(self):
        """Test that single feature triggers expansion check"""
        design_output = """
FEATURE[1]: Complete API Implementation
Description: Build the entire REST API with all functionality
Validation: All endpoints work correctly
Dependencies: None
"""
        features = parse_testable_features(design_output)
        
        # Should detect only 1 feature (triggering expansion in real workflow)
        assert len(features) == 1
        assert features[0]['title'] == 'Complete API Implementation'


class TestIntelligentFeatureExtractor:
    """Test the IntelligentFeatureExtractor"""
    
    def test_detect_rest_api_project(self):
        """Test REST API project type detection"""
        requirements = "Create a REST API for managing tasks"
        plan = "Build a RESTful API with CRUD operations"
        design = "Design includes API endpoints and database models"
        
        project_type = IntelligentFeatureExtractor._detect_project_type(requirements, plan, design)
        assert project_type == "rest_api"
    
    def test_detect_web_app_project(self):
        """Test web app project type detection"""
        requirements = "Build a web application with React frontend"
        plan = "Create a full-stack web app with UI components"
        design = "Frontend components and backend API design"
        
        project_type = IntelligentFeatureExtractor._detect_project_type(requirements, plan, design)
        assert project_type == "web_app"
    
    def test_detect_cli_tool_project(self):
        """Test CLI tool project type detection"""
        requirements = "Create a command line tool for file processing"
        plan = "Build a CLI utility with multiple commands"
        design = "Command structure and argument parsing"
        
        project_type = IntelligentFeatureExtractor._detect_project_type(requirements, plan, design)
        assert project_type == "cli_tool"
    
    def test_vague_requirement_detection(self):
        """Test detection of vague requirements"""
        vague_reqs = [
            "Create a REST API",
            "Build a web app",
            "Make a CLI tool",
            "Implement an API"
        ]
        
        for req in vague_reqs:
            assert IntelligentFeatureExtractor._is_vague_requirement(req) == True
        
        specific_req = """
        Create a REST API with the following endpoints:
        - POST /users/register for user registration
        - POST /users/login for authentication
        - GET /tasks to list all tasks
        - POST /tasks to create a new task
        - PUT /tasks/:id to update a task
        - DELETE /tasks/:id to delete a task
        Include proper authentication and validation.
        """
        assert IntelligentFeatureExtractor._is_vague_requirement(specific_req) == False
    
    def test_expand_vague_api_requirement(self):
        """Test expansion of vague API requirement into multiple features"""
        requirements = "Create a REST API"
        plan = "Build a simple REST API"
        design = """
FEATURE[1]: API Implementation
Description: Create the complete REST API
"""
        
        features = IntelligentFeatureExtractor.extract_features(plan, design, requirements)
        
        # Should expand to multiple features
        assert len(features) >= 5
        
        # Check for essential API features
        feature_titles = [f['title'].lower() for f in features]
        assert any('setup' in title or 'config' in title for title in feature_titles)
        assert any('model' in title or 'schema' in title for title in feature_titles)
        assert any('auth' in title for title in feature_titles)
        assert any('crud' in title or 'endpoint' in title for title in feature_titles)
        assert any('test' in title for title in feature_titles)
    
    def test_preserve_well_structured_features(self):
        """Test that well-structured features are preserved"""
        requirements = "Create a task management API with user authentication"
        plan = "Detailed plan with multiple phases"
        design = """
FEATURE[1]: Project Foundation
Description: Set up Flask application structure
Validation: App starts without errors
Dependencies: None

FEATURE[2]: User Authentication Model
Description: Implement User model with secure password
Validation: User can be created and authenticated
Dependencies: FEATURE[1]

FEATURE[3]: Task Model
Description: Create Task model with relationships
Validation: Tasks can be created and linked to users
Dependencies: FEATURE[1], FEATURE[2]

FEATURE[4]: Authentication Endpoints
Description: Create login and register endpoints
Validation: Users can register and receive JWT tokens
Dependencies: FEATURE[1], FEATURE[2]

FEATURE[5]: Task CRUD Endpoints
Description: Implement task management endpoints
Validation: All CRUD operations work correctly
Dependencies: FEATURE[1], FEATURE[3], FEATURE[4]
"""
        
        features = IntelligentFeatureExtractor.extract_features(plan, design, requirements)
        
        # Should preserve the 5 well-structured features
        assert len(features) == 5
        assert features[0]['title'] == 'Project Foundation'
        assert features[4]['dependencies'] == ['feature_1', 'feature_3', 'feature_4']
    
    def test_extract_from_task_breakdown(self):
        """Test extraction from planner's task breakdown"""
        plan = """
Project Plan:

1. Set up project structure and dependencies
2. Create database models for users and tasks
3. Implement authentication system
4. Build CRUD endpoints for task management
5. Add input validation and error handling
6. Write comprehensive tests
7. Create API documentation
"""
        
        features = IntelligentFeatureExtractor._extract_from_task_breakdown(plan)
        
        assert len(features) >= 6  # Should extract most tasks as features
        assert any('project structure' in f['title'].lower() for f in features)
        assert any('database models' in f['title'].lower() for f in features)
        assert any('authentication' in f['title'].lower() for f in features)


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])