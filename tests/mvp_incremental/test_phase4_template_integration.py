"""
Test Phase 4: Template System Integration
Verifies that templates in IntelligentFeatureExtractor and RequirementsExpander work together
"""
import pytest
from workflows.mvp_incremental.intelligent_feature_extractor import IntelligentFeatureExtractor
from workflows.mvp_incremental.requirements_expander import RequirementsExpander


class TestTemplateIntegration:
    """Test that the template systems work together correctly"""
    
    def test_rest_api_template_flow(self):
        """Test REST API template expansion → feature extraction"""
        # Start with vague requirement
        original = "Create a REST API"
        
        # Expand requirements
        expanded, was_expanded = RequirementsExpander.expand_requirements(original)
        assert was_expanded == True
        
        # Create mock plan and design based on expanded requirements
        mock_plan = f"""
        Project Plan based on: {expanded[:100]}...
        
        1. Project Setup and Configuration
        2. Database Models and Schema  
        3. Authentication System
        4. Core API Endpoints
        5. Input Validation
        6. Testing Suite
        7. API Documentation
        """
        
        # Use simpler design format that parser can handle
        mock_design = """
        Technical Design:
        
        Based on expanded requirements, here are the features:
        
        1. Project Foundation - Set up Flask/FastAPI application with configuration
        2. Database Models - User and resource models with SQLAlchemy  
        3. Authentication System - JWT-based auth with login/register endpoints
        4. CRUD API Endpoints - RESTful endpoints for resource management
        5. Input Validation - Request validation schemas and error handling
        6. Test Suite - Unit and integration tests with pytest
        7. API Documentation - OpenAPI/Swagger documentation
        """
        
        # Extract features
        features = IntelligentFeatureExtractor.extract_features(
            plan=mock_plan,
            design=mock_design,
            requirements=original
        )
        
        # Should get all 7 features from design
        assert len(features) >= 7
        
        # Verify feature titles match template expectations
        feature_titles = [f['title'] for f in features]
        assert any('foundation' in t.lower() or 'setup' in t.lower() for t in feature_titles)
        assert any('database' in t.lower() or 'model' in t.lower() for t in feature_titles)
        assert any('auth' in t.lower() for t in feature_titles)
        assert any('crud' in t.lower() or 'endpoint' in t.lower() for t in feature_titles)
        assert any('validation' in t.lower() for t in feature_titles)
        assert any('test' in t.lower() for t in feature_titles)
        assert any('doc' in t.lower() for t in feature_titles)
    
    def test_web_app_template_flow(self):
        """Test web app template expansion → feature extraction"""
        original = "Build a web app"
        
        # Expand requirements
        expanded, was_expanded = RequirementsExpander.expand_requirements(original)
        assert was_expanded == True
        assert "Frontend Setup" in expanded
        assert "UI Components and Layout" in expanded
        assert "Backend API" in expanded
        assert "State Management" in expanded
        
        # Create mock design with web app features
        mock_design = """
        Based on web app requirements:
        
        1. Frontend Setup - Initialize React with routing and build tools
        2. UI Components - Reusable components with responsive design
        3. Backend API - Express server with data endpoints
        4. State Management - Redux store for application state
        5. Core Features - Main application pages and functionality
        6. Testing - Component and integration tests
        """
        
        # Extract features
        features = IntelligentFeatureExtractor.extract_features(
            plan="Web app development plan",
            design=mock_design,
            requirements=original
        )
        
        # Should get at least 6 features
        assert len(features) >= 6
        
        # Verify web app specific features
        feature_titles = [f['title'] for f in features]
        assert any('frontend' in t.lower() or 'ui' in t.lower() for t in feature_titles)
        assert any('backend' in t.lower() or 'api' in t.lower() for t in feature_titles)
        assert any('state' in t.lower() for t in feature_titles)
    
    def test_cli_tool_template_flow(self):
        """Test CLI tool template expansion → feature extraction"""
        original = "Make a CLI tool"
        
        # Expand requirements
        expanded, was_expanded = RequirementsExpander.expand_requirements(original)
        assert was_expanded == True
        assert "CLI Framework Setup" in expanded
        assert "Core Commands" in expanded
        assert "Input/Output Handling" in expanded
        assert "Configuration Management" in expanded
        
        # Create mock design
        mock_design = """
        CLI tool features:
        
        1. CLI Framework - Set up Click framework with main entry point
        2. Core Commands - Main command handlers with subcommands
        3. I/O Handling - File operations and progress indicators
        4. Configuration - Config file and environment variable support
        5. Error Handling - Comprehensive error handling and logging
        6. Documentation - Help system and usage examples
        """
        
        # Extract features
        features = IntelligentFeatureExtractor.extract_features(
            plan="CLI tool development plan",
            design=mock_design,
            requirements=original
        )
        
        # Should get at least 6 features
        assert len(features) >= 6
        
        # Verify CLI specific features
        feature_titles = [f['title'] for f in features]
        assert any('cli' in t.lower() or 'command' in t.lower() for t in feature_titles)
        assert any('config' in t.lower() for t in feature_titles)
        assert any('error' in t.lower() or 'handling' in t.lower() for t in feature_titles)
    
    def test_template_fallback_for_edge_cases(self):
        """Test that vague non-standard requirements still get expanded"""
        original = "Create something"
        
        # Should use generic expansion
        expanded, was_expanded = RequirementsExpander.expand_requirements(original)
        assert was_expanded == True
        assert "Project Setup" in expanded
        assert "Core Functionality" in expanded
        assert "Testing" in expanded
        assert "Documentation" in expanded
        
        # Extract features from generic template
        mock_design = """
        Based on generic requirements, implementing:
        
        FEATURE[1]: Setup the project structure
        FEATURE[2]: Implement core functionality 
        FEATURE[3]: Add data management
        FEATURE[4]: Create user interface
        FEATURE[5]: Add error handling
        FEATURE[6]: Write tests
        FEATURE[7]: Create documentation
        """
        
        features = IntelligentFeatureExtractor.extract_features(
            plan="Generic project plan",
            design=mock_design,
            requirements=original
        )
        
        # Should still get multiple features
        assert len(features) >= 5
    
    def test_template_consistency(self):
        """Test that templates produce consistent feature counts"""
        test_cases = [
            ("Create a REST API", 7),  # REST API should have 7 features
            ("Build a web application", 6),  # Web app should have 6 features
            ("Make a CLI tool", 6),  # CLI should have 6 features
        ]
        
        for requirement, expected_min_features in test_cases:
            # Expand requirements
            expanded, was_expanded = RequirementsExpander.expand_requirements(requirement)
            assert was_expanded == True
            
            # Extract key requirements
            key_points = RequirementsExpander.extract_key_requirements(expanded)
            
            # Should have at least the expected number of key points
            assert len(key_points) >= expected_min_features, \
                f"Expected at least {expected_min_features} key points for '{requirement}', got {len(key_points)}"
    
    def test_template_does_not_override_detailed_requirements(self):
        """Test that detailed requirements bypass templates"""
        detailed = """
        Create a task management API with:
        - User registration and authentication (JWT)
        - Task CRUD operations with categories
        - Real-time notifications via WebSocket
        - Advanced search and filtering
        - Analytics dashboard
        - Export functionality (CSV, JSON)
        - Rate limiting and caching
        - Comprehensive test suite
        """
        
        # Should NOT expand detailed requirements
        expanded, was_expanded = RequirementsExpander.expand_requirements(detailed)
        assert was_expanded == False
        assert expanded == detailed
        
        # But feature extraction should still work
        mock_design = """
        FEATURE[1]: User Authentication
        FEATURE[2]: Task Management
        FEATURE[3]: Real-time Notifications
        FEATURE[4]: Search System
        FEATURE[5]: Analytics
        FEATURE[6]: Export System
        FEATURE[7]: Performance Features
        FEATURE[8]: Testing
        """
        
        features = IntelligentFeatureExtractor.extract_features(
            plan="Detailed plan",
            design=mock_design,
            requirements=detailed
        )
        
        # Should extract all features from detailed requirements
        assert len(features) >= 8
    
    def test_template_keywords_match_extractor_patterns(self):
        """Test that template keywords align with extractor detection"""
        # Get REST API template
        api_template = RequirementsExpander.EXPANSION_TEMPLATES["rest_api"]
        
        # Check that template contains keywords the extractor looks for
        api_keywords = ["endpoint", "crud", "authentication", "api", "rest"]
        for keyword in api_keywords:
            assert keyword.lower() in api_template.lower(), \
                f"API template should contain keyword '{keyword}'"
        
        # Get web app template
        web_template = RequirementsExpander.EXPANSION_TEMPLATES["web_app"]
        
        # Check web app keywords
        web_keywords = ["frontend", "backend", "component", "ui", "state"]
        for keyword in web_keywords:
            assert keyword.lower() in web_template.lower(), \
                f"Web app template should contain keyword '{keyword}'"
        
        # Get CLI template
        cli_template = RequirementsExpander.EXPANSION_TEMPLATES["cli_tool"]
        
        # Check CLI keywords (use keywords that are actually in the template)
        cli_keywords = ["command", "cli", "argument", "option"]
        for keyword in cli_keywords:
            assert keyword.lower() in cli_template.lower(), \
                f"CLI template should contain keyword '{keyword}'"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])