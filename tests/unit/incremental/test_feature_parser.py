"""
Unit tests for feature parser following ACP testing patterns
"""
import pytest
from shared.utils.feature_parser import FeatureParser, Feature, ComplexityLevel


class TestFeatureParser:
    """Test suite for FeatureParser"""
    
    def test_parse_single_feature(self):
        """Test parsing a single feature"""
        test_output = """
        IMPLEMENTATION PLAN:
        ===================
        
        FEATURE[1]: Project Setup
        Description: Initialize project structure
        Files: app.py, config.py
        Validation: App starts without errors
        Dependencies: None
        Estimated Complexity: Low
        """
        
        parser = FeatureParser()
        features = parser.parse(test_output)
        
        assert len(features) == 1
        assert features[0].id == "FEATURE[1]"
        assert features[0].title == "Project Setup"
        assert features[0].complexity == ComplexityLevel.LOW
        assert features[0].dependencies == []
    
    def test_parse_multiple_features_with_dependencies(self):
        """Test parsing multiple features with dependencies"""
        test_output = """
        IMPLEMENTATION PLAN:
        ===================
        
        FEATURE[1]: Project Setup
        Description: Initialize project structure
        Files: app.py, config.py
        Validation: App starts without errors
        Dependencies: None
        Estimated Complexity: Low
        
        FEATURE[2]: Data Models
        Description: Create database models
        Files: models/user.py, models/product.py
        Validation: Models can be instantiated
        Dependencies: FEATURE[1]
        Estimated Complexity: Medium
        
        FEATURE[3]: API Endpoints
        Description: Implement REST endpoints
        Files: api/users.py, api/products.py
        Validation: Endpoints respond correctly
        Dependencies: FEATURE[1], FEATURE[2]
        Estimated Complexity: High
        """
        
        parser = FeatureParser()
        features = parser.parse(test_output)
        
        assert len(features) == 3
        
        # Check topological order
        feature_ids = [f.id for f in features]
        assert feature_ids.index("FEATURE[1]") < feature_ids.index("FEATURE[2]")
        assert feature_ids.index("FEATURE[2]") < feature_ids.index("FEATURE[3]")
        
        # Check dependencies
        assert features[2].dependencies == ["FEATURE[1]", "FEATURE[2]"]
    
    def test_generate_default_features(self):
        """Test default feature generation when no plan provided"""
        test_output = """
        Technical design with models, services, and API endpoints
        but no explicit implementation plan.
        """
        
        parser = FeatureParser()
        features = parser.parse(test_output)
        
        assert len(features) >= 1  # At least foundation feature
        assert features[0].title == "Project Foundation"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
