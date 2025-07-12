# Incremental Workflow Guide

## Overview

The Incremental Workflow is designed to break down complex software projects into manageable features that are implemented one at a time. This approach ensures steady progress, early error detection, and better handling of complex dependencies.

**Key Component**: The `feature_orchestrator.py` is the heart of this workflow. It parses features from the design phase and manages their incremental implementation.

## Quick Start

### Option 1: Understanding the Feature Orchestrator

To understand how the feature orchestrator works:

```bash
# Learn about the feature orchestrator component
python examples/feature_orchestrator_demo.py
```

### Option 2: Running Without External Dependencies

For a demo that uses mock agents (no orchestrator service needed):

```bash
# Run with mock agents
python examples/direct_incremental_blog_demo.py --mock
```

### Option 3: Full Integration (Requires Orchestrator Service)

For the complete experience with real AI agents:

```bash
# First, start the orchestrator service (in a separate terminal)
python orchestrator/orchestrator_agent.py

# Then run the demo
python examples/direct_incremental_blog_demo.py
```

### How It Works

The incremental workflow follows this pattern:

```
Requirements → Planning → Design → Feature-by-Feature Implementation → Review
```

Key components:

1. **Feature Parser**: Extracts discrete features from the designer's output
2. **Feature Orchestrator**: Manages the incremental implementation
3. **Validation System**: Validates each feature before moving to the next
4. **Retry Strategies**: Smart retry logic for failed features
5. **Progress Monitor**: Tracks and visualizes progress
6. **Stagnation Detector**: Identifies when development is stuck

## Understanding the Feature Orchestrator

The Feature Orchestrator (`workflows/incremental/feature_orchestrator.py`) is the core component that:

1. **Parses Features**: Extracts feature definitions from designer output
2. **Manages Dependencies**: Ensures features are built in the correct order
3. **Handles Validation**: Validates each feature before proceeding
4. **Implements Retry Logic**: Intelligently retries failed features
5. **Tracks Progress**: Monitors and reports on implementation progress

### Key Functions:

```python
# Parse features from designer output
parser = FeatureParser()
features = parser.parse(designer_output)

# Execute features incrementally
completed_features, final_codebase = await execute_features_incrementally(
    features=features,
    requirements=requirements,
    design=design,
    tests=tests,
    tracer=tracer,
    max_retries=3
)
```

## Using the Workflow for Your Project

### 1. Direct API Usage

```python
from shared.data_models import CodingTeamInput, TeamMember
from workflows.workflow_manager import execute_workflow
from examples.orchestrator_manager import OrchestratorManager

async def build_my_app():
    # Define your requirements
    requirements = """
    Create a task management application with:
    - User authentication
    - Task CRUD operations
    - Due date tracking
    - Priority levels
    - Email notifications
    """
    
    # Create input
    input_data = CodingTeamInput(
        requirements=requirements,
        workflow_type="incremental",
        team_members=[
            TeamMember.planner,
            TeamMember.designer,
            TeamMember.coder,
            TeamMember.reviewer
        ]
    )
    
    # Execute with orchestrator management
    with OrchestratorManager() as manager:
        results, report = await execute_workflow(input_data)
        
        # Process results
        for result in results:
            print(f"{result.team_member.value}: {len(result.output)} chars generated")

# Run it
import asyncio
asyncio.run(build_my_app())
```

### 2. Command Line Usage

```bash
# Start orchestrator (handled automatically by demos)
python orchestrator/orchestrator_agent.py

# Use the run.py script
python run.py workflow incremental --task "Create a REST API for user management"
```

### 3. Custom Feature Format

For best results, structure your requirements with clear feature definitions:

```
FEATURE[1]: User Registration
Description: Implement user signup with email verification
Files: models/user.py, api/auth.py, utils/email.py
Validation: Users can register and receive verification emails
Dependencies: []
Complexity: medium

FEATURE[2]: Login System
Description: JWT-based authentication
Files: api/auth.py, middleware/auth.py
Validation: Users can login and receive valid JWT tokens
Dependencies: [FEATURE[1]]
Complexity: medium
```

## Features of the Incremental Workflow

### 1. Smart Feature Parsing
- Automatically extracts features from designer output
- Supports multiple formats (markdown, structured text)
- Falls back to auto-generation if no explicit features found

### 2. Dependency Management
- Respects feature dependencies
- Builds features in the correct order
- Skips features if dependencies fail

### 3. Validation & Retry
- Validates each feature after implementation
- Retries failed features with different strategies
- Detects stagnation and suggests alternatives

### 4. Progress Tracking
- Real-time progress visualization
- Detailed metrics for each feature
- Comprehensive execution reports

### 5. Error Recovery
- Analyzes errors to suggest fixes
- Adjusts approach based on failure patterns
- Prevents infinite loops with stagnation detection

## Troubleshooting

### Common Issues

1. **"No features found in designer output"**
   - Ensure your requirements are clear and structured
   - The designer agent needs to output a clear implementation plan

2. **"Import error: run_team_member_with_tracking"**
   - Make sure the orchestrator is running
   - Check that all dependencies are installed

3. **"Feature validation failed"**
   - Check the validation criteria are reasonable
   - Review error messages for specific issues
   - The workflow will retry with different approaches

### Debug Mode

Set environment variables for more verbose output:
```bash
export DEBUG=1
export LOG_LEVEL=DEBUG
python run_incremental_blog.py
```

## Advanced Configuration

### Workflow Parameters

You can customize the workflow behavior:

```python
# In feature_orchestrator.py
orchestrator.execute_incremental_development(
    designer_output=design,
    requirements=requirements,
    tests=None,  # Optional: pre-written tests
    max_retries=5,  # Increase retry attempts
    stagnation_threshold=0.8  # Adjust stagnation sensitivity
)
```

### Custom Validation

Implement custom validation logic by extending the validation system:

```python
from workflows.incremental.validation_system import GranularValidator

class MyValidator(GranularValidator):
    async def validate_custom_criteria(self, feature, files):
        # Your custom validation logic
        pass
```

## Best Practices

1. **Clear Requirements**: Write detailed, structured requirements
2. **Feature Granularity**: Keep features focused and single-purpose
3. **Validation Criteria**: Make criteria specific and testable
4. **Dependencies**: Clearly define feature dependencies
5. **Complexity Estimates**: Be realistic about feature complexity

## Example Projects

The incremental workflow works well for:
- 🌐 Web applications (REST APIs, full-stack apps)
- 📱 Mobile app backends
- 🤖 Automation tools
- 📊 Data processing pipelines
- 🎮 Game servers
- 🛠️ Developer tools

## Comparison with Other Workflows

| Workflow | Best For | Approach |
|----------|---------|----------|
| Incremental | Complex projects with many features | Feature-by-feature with validation |
| TDD | Test-critical applications | Tests first, then implementation |
| Full | Simple, well-defined projects | All-at-once implementation |
| MVP Incremental | Rapid prototyping | Phases with minimal validation |

## Next Steps

1. Try the blog demo: `python run_incremental_blog.py`
2. Modify the requirements in the demo to build something else
3. Create your own project using the workflow
4. Explore the workflow source code in `workflows/incremental/`

For more information, see the documentation in `docs/workflows/`.