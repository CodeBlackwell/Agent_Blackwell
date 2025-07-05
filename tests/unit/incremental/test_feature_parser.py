"""
Unit tests for feature parser following ACP testing patterns
"""
import pytest
from shared.utils.feature_parser import FeatureParser, Feature, ComplexityLevel


class TestFeatureParser:
    """Test suite for FeatureParser"""
    
    @pytest.fixture
    def parser(self):
        """Create a FeatureParser instance"""
        return FeatureParser()
    
    def test_parse_single_feature(self, parser):
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
        
        features = parser.parse(test_output)
        
        assert len(features) == 1
        assert features[0].id == "FEATURE[1]"
        assert features[0].title == "Project Setup"
        assert features[0].complexity == ComplexityLevel.LOW
        assert features[0].dependencies == []
        assert features[0].files == ["app.py", "config.py"]
        assert features[0].validation_criteria == "App starts without errors"
        assert features[0].estimated_tokens == 2000  # Low complexity
    
    def test_parse_multiple_features_with_dependencies(self, parser):
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
        
        features = parser.parse(test_output)
        
        assert len(features) == 3
        
        # Check topological order
        feature_ids = [f.id for f in features]
        assert feature_ids.index("FEATURE[1]") < feature_ids.index("FEATURE[2]")
        assert feature_ids.index("FEATURE[2]") < feature_ids.index("FEATURE[3]")
        
        # Check dependencies
        assert features[2].dependencies == ["FEATURE[1]", "FEATURE[2]"]
        
        # Check complexity-based token allocation
        assert features[0].estimated_tokens == 2000  # Low
        assert features[1].estimated_tokens == 3000  # Medium (1.5x)
        assert features[2].estimated_tokens == 4000  # High (2x)
    
    def test_generate_default_features(self, parser):
        """Test default feature generation when no plan provided"""
        test_output = """
        Technical design with models, services, and API endpoints
        but no explicit implementation plan.
        """
        
        features = parser.parse(test_output)
        
        assert len(features) >= 1  # At least foundation feature
        assert features[0].title == "Project Foundation"
        assert features[0].id == "FEATURE[1]"
        assert features[0].dependencies == []
    
    def test_edge_case_missing_fields(self, parser):
        """Test parsing with missing fields"""
        test_output = """
        IMPLEMENTATION PLAN:
        ===================
        
        FEATURE[1]: Minimal Feature
        Description: This feature has missing fields
        """
        
        features = parser.parse(test_output)
        
        assert len(features) == 1
        assert features[0].title == "Minimal Feature"
        # Check defaults are applied
        assert features[0].files == ["implementation files"]
        assert features[0].validation_criteria == "Code executes without errors"
        assert features[0].dependencies == []
        assert features[0].complexity == ComplexityLevel.MEDIUM
    
    def test_edge_case_various_dependency_formats(self, parser):
        """Test various dependency format variations"""
        test_output = """
        IMPLEMENTATION PLAN:
        ===================
        
        FEATURE[1]: Base
        Description: Base feature
        Files: base.py
        Validation: Works
        Dependencies: none
        Complexity: Low
        
        FEATURE[2]: Middle
        Description: Middle feature
        Files: middle.py
        Validation: Works
        Dependencies: N/A
        Complexity: Low
        
        FEATURE[3]: Top
        Description: Top feature
        Files: top.py
        Validation: Works
        Dependencies: -
        Complexity: Low
        
        FEATURE[4]: Dependent
        Description: Has dependencies
        Files: dep.py
        Validation: Works
        Dependencies: FEATURE[1], FEATURE[2], and FEATURE[3]
        Complexity: Low
        """
        
        features = parser.parse(test_output)
        
        # Check that various "no dependency" formats are handled
        assert features[0].dependencies == []  # "none"
        assert features[1].dependencies == []  # "N/A"
        assert features[2].dependencies == []  # "-"
        # Check that dependencies are extracted correctly with "and"
        assert set(features[3].dependencies) == {"FEATURE[1]", "FEATURE[2]", "FEATURE[3]"}
    
    def test_edge_case_complexity_variations(self, parser):
        """Test various complexity format variations"""
        test_cases = [
            ("Low", ComplexityLevel.LOW),
            ("HIGH", ComplexityLevel.HIGH),
            ("medium", ComplexityLevel.MEDIUM),
            ("MEDIUM", ComplexityLevel.MEDIUM),
            ("Very High", ComplexityLevel.HIGH),
            ("low complexity", ComplexityLevel.LOW),
            ("Super duper high", ComplexityLevel.HIGH),
            ("Unknown", ComplexityLevel.MEDIUM),  # Default
        ]
        
        for complexity_str, expected in test_cases:
            test_output = f"""
            IMPLEMENTATION PLAN:
            ===================
            
            FEATURE[1]: Test Feature
            Description: Testing complexity parsing
            Files: test.py
            Validation: Works
            Dependencies: None
            Complexity: {complexity_str}
            """
            
            features = parser.parse(test_output)
            assert features[0].complexity == expected
    
    def test_edge_case_files_parsing(self, parser):
        """Test various file list formats"""
        test_output = """
        IMPLEMENTATION PLAN:
        ===================
        
        FEATURE[1]: File Test
        Description: Testing file parsing
        Files: single.py
        Validation: Works
        Dependencies: None
        Complexity: Low
        
        FEATURE[2]: Multiple Files
        Description: Multiple files with spaces
        Files: file1.py, file2.py, file3.py
        Validation: Works
        Dependencies: None
        Complexity: Low
        
        FEATURE[3]: Files with Paths
        Description: Files with directory paths
        Files: src/main.py, tests/test_main.py, docs/readme.md
        Validation: Works
        Dependencies: None
        Complexity: Low
        """
        
        features = parser.parse(test_output)
        
        assert features[0].files == ["single.py"]
        assert features[1].files == ["file1.py", "file2.py", "file3.py"]
        assert features[2].files == ["src/main.py", "tests/test_main.py", "docs/readme.md"]
    
    def test_edge_case_circular_dependencies(self, parser):
        """Test handling of circular dependencies"""
        test_output = """
        IMPLEMENTATION PLAN:
        ===================
        
        FEATURE[1]: First
        Description: First feature
        Files: first.py
        Validation: Works
        Dependencies: FEATURE[3]
        Complexity: Low
        
        FEATURE[2]: Second
        Description: Second feature
        Files: second.py
        Validation: Works
        Dependencies: FEATURE[1]
        Complexity: Low
        
        FEATURE[3]: Third
        Description: Third feature
        Files: third.py
        Validation: Works
        Dependencies: FEATURE[2]
        Complexity: Low
        """
        
        features = parser.parse(test_output)
        
        # Parser should still handle circular dependencies gracefully
        assert len(features) == 3
        # Each feature should appear exactly once
        feature_ids = [f.id for f in features]
        assert len(set(feature_ids)) == 3
    
    def test_edge_case_multiline_descriptions(self, parser):
        """Test multiline field parsing"""
        test_output = """
        IMPLEMENTATION PLAN:
        ===================
        
        FEATURE[1]: Complex Feature
        Description: This is a multiline description
                    that spans multiple lines
                    and contains various details
        Files: complex.py
        Validation: Multiple validation criteria:
                   - Code compiles
                   - Tests pass
                   - No runtime errors
        Dependencies: None
        Complexity: High
        """
        
        features = parser.parse(test_output)
        
        assert "multiline description" in features[0].description
        assert "various details" in features[0].description
        assert "Multiple validation criteria" in features[0].validation_criteria
        assert "Tests pass" in features[0].validation_criteria
    
    def test_edge_case_non_sequential_feature_ids(self, parser):
        """Test non-sequential feature IDs"""
        test_output = """
        IMPLEMENTATION PLAN:
        ===================
        
        FEATURE[5]: Fifth
        Description: Jump to 5
        Files: five.py
        Validation: Works
        Dependencies: None
        Complexity: Low
        
        FEATURE[10]: Tenth
        Description: Jump to 10
        Files: ten.py
        Validation: Works
        Dependencies: FEATURE[5]
        Complexity: Low
        
        FEATURE[2]: Second
        Description: Back to 2
        Files: two.py
        Validation: Works
        Dependencies: None
        Complexity: Low
        """
        
        features = parser.parse(test_output)
        
        assert len(features) == 3
        assert "FEATURE[5]" in [f.id for f in features]
        assert "FEATURE[10]" in [f.id for f in features]
        assert "FEATURE[2]" in [f.id for f in features]
    
    def test_default_feature_generation_models(self, parser):
        """Test default generation detects models"""
        test_output = """
        Design includes User model, Product schema, and database connections.
        """
        
        features = parser.parse(test_output)
        
        # Should have foundation + models
        assert len(features) >= 2
        assert any("Data Models" in f.title for f in features)
    
    def test_default_feature_generation_services(self, parser):
        """Test default generation detects services"""
        test_output = """
        Implementation includes UserService for business logic and processing.
        """
        
        features = parser.parse(test_output)
        
        # Should have foundation + services
        assert any("Business Logic" in f.title for f in features)
    
    def test_default_feature_generation_api(self, parser):
        """Test default generation detects API"""
        test_output = """
        REST API with endpoints for user management and product catalog.
        """
        
        features = parser.parse(test_output)
        
        # Should have foundation + API
        assert any("API Layer" in f.title for f in features)
    
    def test_default_feature_generation_full_stack(self, parser):
        """Test default generation for full stack application"""
        test_output = """
        Full stack application with:
        - Database models for users and products
        - Service layer for business logic
        - RESTful API endpoints
        """
        
        features = parser.parse(test_output)
        
        # Should generate all layers
        assert len(features) >= 4
        titles = [f.title for f in features]
        assert "Project Foundation" in titles
        assert "Data Models" in titles
        assert "Business Logic" in titles
        assert "API Layer" in titles
        
        # Check dependencies are correct
        api_feature = next(f for f in features if "API" in f.title)
        assert len(api_feature.dependencies) > 0
    
    def test_edge_case_empty_implementation_plan(self, parser):
        """Test empty implementation plan section"""
        test_output = """
        IMPLEMENTATION PLAN:
        ===================
        
        (No features listed)
        """
        
        features = parser.parse(test_output)
        
        # Should return empty list when plan exists but has no features
        assert features == []
    
    def test_edge_case_malformed_feature(self, parser):
        """Test handling of malformed feature entries"""
        test_output = """
        IMPLEMENTATION PLAN:
        ===================
        
        FEATURE[1]: Good Feature
        Description: This is well-formed
        Files: good.py
        Validation: Works
        Dependencies: None
        Complexity: Low
        
        This is some random text that shouldn't be parsed
        
        FEATURE[2 Missing bracket
        Description: Malformed
        
        FEATURE[3]: Another Good Feature
        Description: This is also well-formed
        Files: another.py
        Validation: Works
        Dependencies: FEATURE[1]
        Complexity: Medium
        """
        
        features = parser.parse(test_output)
        
        # Should only parse well-formed features
        assert len(features) == 2
        assert features[0].id == "FEATURE[1]"
        assert features[1].id == "FEATURE[3]"
    
    def test_feature_token_allocation(self, parser):
        """Test that token allocation is based on complexity"""
        test_output = """
        IMPLEMENTATION PLAN:
        ===================
        
        FEATURE[1]: Low Complexity
        Description: Simple feature
        Files: simple.py
        Validation: Works
        Dependencies: None
        Complexity: Low
        
        FEATURE[2]: Medium Complexity
        Description: Moderate feature
        Files: moderate.py
        Validation: Works
        Dependencies: None
        Complexity: Medium
        
        FEATURE[3]: High Complexity
        Description: Complex feature
        Files: complex.py
        Validation: Works
        Dependencies: None
        Complexity: High
        """
        
        features = parser.parse(test_output)
        
        # Verify token allocation
        low = next(f for f in features if f.complexity == ComplexityLevel.LOW)
        medium = next(f for f in features if f.complexity == ComplexityLevel.MEDIUM)
        high = next(f for f in features if f.complexity == ComplexityLevel.HIGH)
        
        assert low.estimated_tokens == 2000
        assert medium.estimated_tokens == 3000  # 1.5x
        assert high.estimated_tokens == 4000    # 2x


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
