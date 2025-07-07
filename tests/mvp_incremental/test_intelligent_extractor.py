"""
Integration tests for IntelligentFeatureExtractor
"""
import pytest
from workflows.mvp_incremental.intelligent_feature_extractor import IntelligentFeatureExtractor, PROJECT_TEMPLATES


class TestIntelligentExtractorIntegration:
    """Integration tests for the intelligent feature extractor"""
    
    def test_template_expansion_rest_api(self):
        """Test REST API template expansion"""
        existing_features = [{
            "id": "feature_1",
            "title": "Complete API",
            "description": "Build the entire API"
        }]
        
        expanded = IntelligentFeatureExtractor._expand_using_template(
            "rest_api", 
            "API plan", 
            "API design",
            existing_features
        )
        
        # Should have all template features
        assert len(expanded) == len(PROJECT_TEMPLATES["rest_api"]["features"])
        assert expanded[0]["title"] == "Project Setup and Configuration"
        assert expanded[2]["title"] == "Authentication System"
        assert expanded[2]["dependencies"] == ["feature_1", "feature_2"]  # Auth depends on setup and models
    
    def test_template_expansion_web_app(self):
        """Test web app template expansion"""
        expanded = IntelligentFeatureExtractor._expand_using_template(
            "web_app",
            "Web app plan",
            "Web app design", 
            []
        )
        
        assert len(expanded) == len(PROJECT_TEMPLATES["web_app"]["features"])
        assert any("Frontend Setup" in f["title"] for f in expanded)
        assert any("State Management" in f["title"] for f in expanded)
        assert any("Backend API" in f["title"] for f in expanded)
    
    def test_template_expansion_cli_tool(self):
        """Test CLI tool template expansion"""
        expanded = IntelligentFeatureExtractor._expand_using_template(
            "cli_tool",
            "CLI plan",
            "CLI design",
            []
        )
        
        assert len(expanded) == len(PROJECT_TEMPLATES["cli_tool"]["features"])
        assert any("CLI Framework Setup" in f["title"] for f in expanded)
        assert any("Core Commands" in f["title"] for f in expanded)
    
    def test_api_completeness_check(self):
        """Test ensuring API completeness"""
        # Start with incomplete features
        features = [
            {
                "id": "feature_1",
                "title": "Basic Setup",
                "description": "Set up the project"
            },
            {
                "id": "feature_2", 
                "title": "Some endpoints",
                "description": "Create some API endpoints"
            }
        ]
        
        completed = IntelligentFeatureExtractor._ensure_api_completeness(
            features,
            "API plan",
            "API design"
        )
        
        # Should add missing essential features
        assert len(completed) > 2
        feature_titles = [f["title"].lower() for f in completed]
        
        # Check for essential features that should be added
        assert any("auth" in title for title in feature_titles)
        assert any("model" in title or "schema" in title for title in feature_titles)
        assert any("validation" in title for title in feature_titles)
        assert any("test" in title for title in feature_titles)
        assert any("doc" in title for title in feature_titles)
    
    def test_full_extraction_flow_vague_api(self):
        """Test full extraction flow with vague API requirement"""
        requirements = "Create a simple REST API"
        plan = "We'll build a REST API with basic functionality"
        design = """
System Design:

FEATURE[1]: Build API
Description: Create the REST API with all necessary components
"""
        
        features = IntelligentFeatureExtractor.extract_features(plan, design, requirements)
        
        # Should expand to full API feature set
        assert len(features) >= 7
        
        # Verify features have proper structure
        for feature in features:
            assert "id" in feature
            assert "title" in feature
            assert "description" in feature
            assert "test_criteria" in feature
            assert "dependencies" in feature
    
    def test_full_extraction_flow_specific_requirements(self):
        """Test extraction with specific requirements doesn't over-expand"""
        requirements = """
        Create a minimal REST API with just two endpoints:
        1. GET /status - returns server status
        2. GET /version - returns API version
        No authentication needed, no database required.
        """
        plan = "Simple API with two endpoints"
        design = """
FEATURE[1]: API Setup
Description: Set up minimal Flask app
Dependencies: None

FEATURE[2]: Status Endpoint
Description: Create GET /status endpoint
Dependencies: FEATURE[1]

FEATURE[3]: Version Endpoint  
Description: Create GET /version endpoint
Dependencies: FEATURE[1]
"""
        
        features = IntelligentFeatureExtractor.extract_features(plan, design, requirements)
        
        # Should respect the specific requirements and not over-expand
        assert len(features) == 3
        assert features[0]["title"] == "API Setup"
        assert features[1]["title"] == "Status Endpoint"
        assert features[2]["title"] == "Version Endpoint"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])