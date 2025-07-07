# MVP Incremental TDD Workflow Enhancement

## Overview

The MVP Incremental TDD workflow has been enhanced to properly handle vague requirements by expanding them into multiple well-defined features. Previously, a vague requirement like "Create a REST API" would result in a single monolithic implementation. Now, it intelligently expands to 7+ modular features, each with its own TDD cycle.

## Key Enhancements

### 1. Requirements Expansion (Phase 3)
- **Module**: `workflows/mvp_incremental/requirements_expander.py`
- **Purpose**: Detects vague requirements and expands them into detailed specifications
- **Features**:
  - Automatic detection of vague requirements (< 10 words or lacking technical details)
  - Project type detection (REST API, Web App, CLI Tool)
  - Template-based expansion with industry best practices
  - Preserves detailed requirements unchanged

### 2. Intelligent Feature Extraction (Phase 1)
- **Module**: `workflows/mvp_incremental/intelligent_feature_extractor.py`
- **Purpose**: Extracts multiple features from design output using multiple strategies
- **Features**:
  - Primary strategy: Parse FEATURE[n] blocks
  - Fallback strategy: Extract numbered lists
  - AI inference strategy: Analyze unstructured text
  - Force extraction for stubborn cases

### 3. Enhanced Agent Prompts (Phase 2)
- **Designer Agent**: Strict FEATURE[n] formatting requirements
- **Planner Agent**: Concrete deliverables and structured output
- **Both**: Better handling of expanded requirements

### 4. Template System (Phase 4)
- **REST API Template**: 7 features (setup, models, auth, endpoints, validation, tests, docs)
- **Web App Template**: 6 features (frontend, UI, backend, features, state, testing)
- **CLI Tool Template**: 6 features (framework, commands, I/O, config, errors, testing)

## Usage

### Before Enhancement
```python
# Input
"Create a REST API"

# Result
- 1 feature: "Complete Implementation"
- Single file with all code
- Minimal or no tests
```

### After Enhancement
```python
# Input
"Create a REST API"

# Result
- 7+ features:
  1. Project Foundation
  2. Database Models
  3. Authentication System
  4. CRUD API Endpoints
  5. Input Validation
  6. Test Suite
  7. API Documentation

# Each feature includes:
- Test-first implementation (TDD)
- Clear acceptance criteria
- Edge case handling
- Error conditions
- Review and validation
```

## How It Works

### 1. Requirements Expansion Flow
```
Vague Requirement → Detect Project Type → Apply Template → Expanded Requirements
```

### 2. Feature Extraction Flow
```
Design Output → Try FEATURE[n] → Try Numbered Lists → Try AI Inference → Features
```

### 3. TDD Implementation Flow
```
For each feature:
  Write Tests → Run Tests (Fail) → Implement → Run Tests (Pass) → Review
```

## Examples

### REST API Expansion
```python
# Original
"Create a REST API"

# Expanded to:
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

# ... and 5 more features
```

### Web App Expansion
```python
# Original
"Build a web app"

# Expanded to:
1. **Frontend Setup**
   - Initialize modern frontend framework (React/Vue/Angular)
   - Set up build tools and development server
   - Configure routing and navigation
   - Set up state management solution

# ... and 5 more features
```

## Running the Enhanced Workflow

### 1. Using the Orchestrator
```bash
# Start orchestrator
python orchestrator/orchestrator_agent.py

# Submit request
curl -X POST http://localhost:8080/acp/submit \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "EnhancedCodingTeamTool",
    "arguments": {
      "requirements": "Create a REST API",
      "workflow_type": "mvp_incremental_tdd"
    }
  }'
```

### 2. Using the API
```bash
# Start API server
python api/orchestrator_api.py

# Submit request
curl -X POST http://localhost:8000/execute-workflow \
  -H "Content-Type: application/json" \
  -d '{
    "requirements": "Create a REST API",
    "workflow_type": "mvp_incremental_tdd"
  }'
```

### 3. Running Tests
```bash
# Test requirements expansion
pytest tests/mvp_incremental/test_requirements_expander.py

# Test feature extraction
pytest tests/mvp_incremental/test_intelligent_feature_extractor.py

# Test template integration
pytest tests/mvp_incremental/test_phase4_template_integration.py

# Run comprehensive integration tests
pytest tests/mvp_incremental/test_phase5_comprehensive_integration.py
```

### 4. Running the Demo
```bash
# See the enhancement in action
python demo_mvp_incremental_enhancement.py
```

## Benefits

1. **Better Structure**: Vague requirements are expanded into well-organized features
2. **Comprehensive Testing**: Each feature gets its own test suite
3. **Modular Implementation**: Features are implemented independently
4. **Clear Dependencies**: Features are ordered by dependencies
5. **Quality Assurance**: Each feature goes through review cycles
6. **Industry Standards**: Templates follow best practices

## Configuration

### Customizing Templates
Edit `workflows/mvp_incremental/requirements_expander.py`:
```python
EXPANSION_TEMPLATES = {
    "rest_api": "...",  # Customize REST API template
    "web_app": "...",   # Customize Web App template
    "cli_tool": "..."   # Customize CLI tool template
}
```

### Adjusting Vagueness Detection
```python
# In RequirementsExpander._is_vague()
if word_count < 10:  # Adjust threshold
    return True
```

### Adding New Project Types
1. Add detection logic in `_detect_project_type()`
2. Add template in `EXPANSION_TEMPLATES`
3. Update tests

## Troubleshooting

### Issue: Features Not Extracted
- Check design output format
- Ensure FEATURE[n] blocks are properly formatted
- Review logs for extraction strategy used

### Issue: Requirements Not Expanded
- Check if requirements are already detailed
- Verify project type detection
- Review vagueness detection criteria

### Issue: TDD Tests Failing
- Check test writer prompts
- Verify executor agent is working
- Review retry configuration

## Future Enhancements

See `workflows/mvp_incremental/ENHANCEMENT_PLAN.md` for planned improvements:
- Interactive mode for template customization
- Preset configurations for common project types
- Configuration helper utility
- Example gallery
- Enhanced documentation