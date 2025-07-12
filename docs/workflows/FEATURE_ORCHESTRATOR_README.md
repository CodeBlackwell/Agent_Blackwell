# Feature Orchestrator - Quick Start Guide

The Feature Orchestrator is the core component of the incremental workflow that manages feature-by-feature implementation of software projects.

## What is the Feature Orchestrator?

Located at `workflows/incremental/feature_orchestrator.py`, it:
- Parses feature definitions from design documents
- Implements features one at a time in dependency order
- Validates each feature before proceeding
- Handles retries with intelligent strategies
- Tracks progress throughout execution

## Quick Demos

### 1. Understanding How It Works (No Dependencies)
```bash
python examples/standalone_feature_orchestrator.py
```
This shows the core concepts with mock implementations.

### 2. See the Components
```bash
python examples/feature_orchestrator_demo.py
```
This demonstrates the key functions and how to use them.

### 3. Build a Real Blog App
```bash
# Start the orchestrator service first
python orchestrator/orchestrator_agent.py

# In another terminal, run:
python examples/direct_incremental_blog_demo.py
```

## Using in Your Project

### Basic Usage
```python
from workflows.incremental.feature_orchestrator import FeatureOrchestrator
from workflows.monitoring import WorkflowExecutionTracer

# Create orchestrator
tracer = WorkflowExecutionTracer("my_project")
orchestrator = FeatureOrchestrator(tracer)

# Execute incremental development
results, codebase, summary = await orchestrator.execute_incremental_development(
    designer_output=design_with_features,
    requirements=project_requirements,
    tests=None,
    max_retries=3
)
```

### Feature Format
The orchestrator expects features in this format:
```
FEATURE[1]: Feature Name
Description: What this feature does
Files: file1.py, file2.py
Validation: How to verify it works
Dependencies: [FEATURE[N], ...]
Complexity: low|medium|high
```

## Key Components

- **FeatureParser**: Extracts features from designer output
- **FeatureOrchestrator**: Main orchestration logic
- **ValidationSystem**: Validates each feature implementation
- **RetryStrategies**: Smart retry logic for failures
- **ProgressMonitor**: Tracks and visualizes progress
- **StagnationDetector**: Identifies when stuck

## Workflow Integration

The feature orchestrator is used by the incremental workflow:
1. Planner creates high-level plan
2. Designer outputs feature definitions
3. **Feature Orchestrator** implements each feature
4. Reviewer evaluates the final result

## Troubleshooting

### "No features found"
- Ensure designer output includes FEATURE[N] markers
- Check the format matches expected pattern

### "Import errors"
- The orchestrator needs the main service running
- Start with: `python orchestrator/orchestrator_agent.py`

### "Validation failures"
- Features automatically retry with different approaches
- Check validation criteria are reasonable
- Review error messages for specific issues

## Files Created

- `examples/standalone_feature_orchestrator.py` - Standalone demo
- `examples/feature_orchestrator_demo.py` - Component demonstration  
- `examples/direct_incremental_blog_demo.py` - Full blog example
- `INCREMENTAL_WORKFLOW_GUIDE.md` - Complete workflow guide
- `INCREMENTAL_WORKFLOW_BUGS.md` - Known issues and fixes

## Next Steps

1. Run the standalone demo to understand concepts
2. Try building a blog app with the full demo
3. Use the incremental workflow for your own projects
4. Customize retry strategies and validation logic as needed