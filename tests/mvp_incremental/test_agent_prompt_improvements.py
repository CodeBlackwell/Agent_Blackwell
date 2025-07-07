"""
Test the agent prompt improvements without running full workflow
"""
import pytest
from agents.designer.prompt_templates import ENHANCED_DESIGNER_TEMPLATE
from agents.planner.planner_agent import planner_agent


class TestAgentPromptImprovements:
    """Test that agent prompts have been enhanced correctly"""
    
    def test_designer_prompt_has_critical_requirements(self):
        """Test designer prompt includes critical requirements for features"""
        assert "CRITICAL REQUIREMENTS FOR FEATURES:" in ENHANCED_DESIGNER_TEMPLATE
        assert "You MUST include ALL features necessary" in ENHANCED_DESIGNER_TEMPLATE
        assert "For API projects: Include AT LEAST 5-7 features" in ENHANCED_DESIGNER_TEMPLATE
        assert "NEVER combine multiple major functionalities" in ENHANCED_DESIGNER_TEMPLATE
        
        # Check for examples
        assert "FEATURE[1]: Project Foundation" in ENHANCED_DESIGNER_TEMPLATE
        assert "FEATURE[7]: API Documentation" in ENHANCED_DESIGNER_TEMPLATE
    
    def test_designer_prompt_has_structured_format(self):
        """Test designer prompt enforces structured FEATURE format"""
        assert "Structure EVERY feature using this EXACT format:" in ENHANCED_DESIGNER_TEMPLATE
        assert "Description: <What functionality this implements - be specific>" in ENHANCED_DESIGNER_TEMPLATE
        assert "Validation: <Specific criteria to verify this feature works>" in ENHANCED_DESIGNER_TEMPLATE
        assert "Dependencies: <List of FEATURE[N] IDs this depends on, or \"None\">" in ENHANCED_DESIGNER_TEMPLATE
    
    def test_planner_prompt_has_concrete_deliverables(self):
        """Test planner prompt requires concrete deliverables"""
        # Get the planner agent module
        import inspect
        planner_source = inspect.getsource(planner_agent)
        
        assert "CRITICAL REQUIREMENTS:" in planner_source
        assert "Each task must have CONCRETE DELIVERABLES" in planner_source
        assert "Include TESTABLE ACCEPTANCE CRITERIA" in planner_source
        assert "Deliverables:" in planner_source
        assert "Acceptance Criteria:" in planner_source
    
    def test_planner_prompt_expands_vague_requirements(self):
        """Test planner prompt handles vague requirements"""
        import inspect
        planner_source = inspect.getsource(planner_agent)
        
        assert "When requirements are vague" in planner_source
        assert "expand them into a COMPLETE project plan" in planner_source
        assert "APIs: Setup, Models, Auth, Endpoints, Validation, Testing, Documentation" in planner_source
        assert "assume the user wants an MVP implementation" in planner_source
    
    def test_prompts_have_complete_examples(self):
        """Test that prompts include complete examples"""
        # Designer should have 7 example features for API
        designer_features = ENHANCED_DESIGNER_TEMPLATE.count("FEATURE[")
        assert designer_features >= 7, f"Designer prompt should have at least 7 example features, found {designer_features}"
        
        # Check feature dependencies in examples
        assert "Dependencies: FEATURE[1], FEATURE[2]" in ENHANCED_DESIGNER_TEMPLATE
        assert "Dependencies: None" in ENHANCED_DESIGNER_TEMPLATE


if __name__ == "__main__":
    pytest.main([__file__, "-v"])