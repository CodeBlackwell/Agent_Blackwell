# Operation TDD - System Optimization Notes

## Overview
These notes outline strategies to optimize the MVP Incremental TDD workflow to better handle vague requirements without requiring users to provide excessive detail.

## Core Problem
When users provide simple requirements like "Create a REST API", the system currently:
- Only extracts 1 feature instead of the full implementation
- Requires very specific requirements to work properly
- Doesn't leverage common patterns for standard project types

## Optimization Strategies

### 1. Enhanced Agent Prompts

#### Designer Agent Improvements
```python
# In designer agent prompt
"""
CRITICAL: You MUST format ALL features using this exact structure:

FEATURE[1]: <Feature Title>
Description: <Clear description of what to implement>
Implementation: <Specific components/files to create>
Validation: <How to verify it works>
Dependencies: None or FEATURE[n]

Ensure EVERY feature from the plan is included with a FEATURE[n] block.
"""
```

#### Planner Agent Enhancement
```python
# In planner agent prompt
"""
For each task, specify:
- Concrete deliverables (files, endpoints, functions)
- Testable acceptance criteria
- Clear dependencies

Example:
Task: Authentication
Deliverables: 
  - POST /auth/login endpoint
  - POST /auth/register endpoint
  - JWT token generation
  - User model with password hashing
"""
```

### 2. Intelligent Feature Extraction

Create a more sophisticated feature parser that can handle multiple formats:

```python
class IntelligentFeatureExtractor:
    def extract_features(self, plan: str, design: str) -> List[Feature]:
        features = []
        
        # Try multiple extraction strategies
        features = self._extract_feature_blocks(design)  # FEATURE[n] format
        
        if not features:
            features = self._extract_from_task_breakdown(plan)  # From planner
            
        if not features:
            features = self._infer_from_requirements(plan, design)  # AI inference
            
        if len(features) == 1 and "api" in plan.lower():
            # Expand single API feature into standard components
            features = self._expand_api_feature(features[0])
            
        return features
    
    def _expand_api_feature(self, feature: Feature) -> List[Feature]:
        """Automatically expand 'Create API' into standard features"""
        return [
            Feature("Project Setup", "Initialize Flask app with configuration"),
            Feature("Database Models", "Create User and Resource models"),
            Feature("Authentication", "Implement JWT auth endpoints"),
            Feature("CRUD Endpoints", "Create resource management endpoints"),
            Feature("Error Handling", "Add validation and error responses"),
            Feature("Testing", "Write unit and integration tests"),
            Feature("Documentation", "Generate API documentation")
        ]
```

### 3. Requirements Expansion Agent

Add a new agent or step that expands vague requirements:

```python
async def expand_requirements(original_requirements: str) -> str:
    """Use AI to expand vague requirements into detailed specs"""
    
    prompt = f"""
    The user provided this requirement: {original_requirements}
    
    This seems vague or high-level. Expand it into detailed requirements by:
    1. Identifying the type of application (API, web app, CLI, etc.)
    2. Listing standard components for that type
    3. Adding common best practices
    4. Including testing and documentation needs
    
    Format as numbered requirements list.
    """
    
    expanded = await requirement_expansion_agent(prompt)
    return expanded
```

### 4. Template-Based Feature Generation

Create templates for common project types:

```python
PROJECT_TEMPLATES = {
    "rest_api": {
        "features": [
            {"title": "Project Setup", "components": ["app structure", "config", "dependencies"]},
            {"title": "Data Models", "components": ["user model", "resource models", "database setup"]},
            {"title": "Authentication", "components": ["login", "register", "JWT tokens"]},
            {"title": "CRUD Operations", "components": ["create", "read", "update", "delete"]},
            {"title": "Validation", "components": ["input validation", "error handling"]},
            {"title": "Testing", "components": ["unit tests", "integration tests"]},
            {"title": "Documentation", "components": ["API docs", "README"]}
        ]
    },
    "web_app": {...},
    "cli_tool": {...}
}

def detect_project_type(requirements: str) -> str:
    """Detect project type from requirements"""
    req_lower = requirements.lower()
    if any(word in req_lower for word in ["api", "rest", "endpoint"]):
        return "rest_api"
    elif any(word in req_lower for word in ["website", "web app", "frontend"]):
        return "web_app"
    # etc...
```

### 5. Interactive Clarification

Add a clarification step when requirements are too vague:

```python
def get_clarification(requirements: str, detected_type: str):
    """Ask user for clarification on vague requirements"""
    
    questions = {
        "rest_api": [
            "What type of resources will the API manage?",
            "Do you need user authentication?",
            "What database would you prefer?",
            "Should it include tests and documentation?"
        ]
    }
    
    # Could be automated or interactive
    return clarified_requirements
```

### 6. Improve Testable Feature Parser

Update the testable feature parser to be more intelligent:

```python
def parse_testable_features(design_output: str) -> List[Dict[str, Any]]:
    """Enhanced parser that ensures all features are captured"""
    
    # First try structured extraction
    features = TestableFeatureParser.parse_features_with_criteria(design_output)
    
    # If only one feature found but design mentions multiple
    if len(features) == 1 and design_output.count("FEATURE[") > 1:
        # Force re-parse with different strategy
        features = force_extract_all_features(design_output)
    
    # Validate we got reasonable number of features
    if len(features) < 3 and "api" in design_output.lower():
        logger.warning(f"Only found {len(features)} features for API project, attempting expansion...")
        features = expand_api_features(features, design_output)
    
    return [f.to_dict() for f in features]
```

### 7. Configuration-Driven Approach

Add configuration to control feature generation:

```yaml
# mvp_incremental_config.yaml
feature_generation:
  min_features_for_api: 5
  auto_expand_vague_requirements: true
  use_templates: true
  require_testable_criteria: true
  
prompts:
  designer:
    enforce_feature_format: true
    require_validation_criteria: true
  planner:
    require_concrete_deliverables: true
```

## Implementation Priority

1. **Quick Win**: Fix the feature parser to properly extract FEATURE[n] blocks
2. **Medium Term**: Enhance agent prompts for better structure
3. **Long Term**: Add requirements expansion and template system

## Key Insight
The system should be more "opinionated" about what constitutes a complete implementation while remaining flexible for different project types. This means:
- Recognizing common patterns (REST API, web app, CLI tool)
- Automatically expanding to include standard components
- Ensuring comprehensive test coverage by default
- Making reasonable assumptions that can be overridden

## Next Steps for Operation TDD
1. Implement the IntelligentFeatureExtractor
2. Update agent prompts to enforce structured output
3. Add project type detection and templates
4. Create requirements expansion capability
5. Test with various vague inputs to ensure robustness