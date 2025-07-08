# Workflows Directory

This directory contains all workflow implementations that orchestrate agents to complete software development tasks.

## Workflow Overview

Workflows define how agents collaborate to transform requirements into working code. Each workflow represents a different development methodology or approach.

## Available Workflows

### 🔄 TDD Workflow (`tdd/`)
**Test-Driven Development approach**
- Write tests first, then implementation
- Red-green-refactor cycle
- Ensures high code quality and test coverage
- **Flow**: Planning → Design → Test Writing → Implementation → Execution → Review

### 📦 Full Workflow (`full/`)
**Complete development cycle**
- Traditional waterfall-style approach
- All phases executed sequentially
- Comprehensive but less iterative
- **Flow**: Planning → Design → Implementation → Review

### 🚀 MVP Incremental Workflow (`mvp_incremental/`)
**Feature-by-feature development** (Most Advanced)
- Breaks project into small, implementable features
- Validates each feature before moving to next
- 10 phases including error recovery and progress tracking
- Includes retry logic and intelligent error analysis
- **Flow**: Planning → Design → Feature Breakdown → Incremental Implementation with Validation

### 🎯 MVP Incremental TDD (`mvp_incremental/`)
**Combines MVP approach with TDD**
- Each feature goes through TDD cycle
- Test-first for every feature
- Maximum quality and iterative development
- **Flow**: For each feature: Write Tests → Implement → Validate → Review

### 🔧 Individual Steps (`individual/`)
**Execute single workflow phases**
- Run only planning, design, or implementation
- Maximum flexibility for specific tasks
- Useful for debugging or targeted operations
- **Options**: planning_step, design_step, implementation_step, review_step

## Workflow Components

### Core Files

#### workflow_manager.py
Central dispatcher that:
- Routes requests to appropriate workflows
- Handles workflow type selection
- Manages execution flow
- Returns results to orchestrator

#### workflow_config.py
Configuration for all workflows:
- Retry limits and strategies
- Timeout settings
- File paths
- Execution parameters

### Workflow Structure

Each workflow directory contains:
```
workflow_name/
├── __init__.py              # Workflow initialization
├── workflow_name.py         # Main workflow logic
├── README.md                # Workflow-specific docs
└── specialized_modules/     # Workflow-specific components
```

## Adding New Workflows

To create a new workflow:
1. Create a directory under `workflows/`
2. Implement the workflow following existing patterns
3. Register in `workflow_manager.py`
4. Add configuration to `workflow_config.py`
5. Create comprehensive tests
6. Document the workflow

## Workflow Selection

Choose a workflow based on your needs:
- **TDD**: When code quality is paramount
- **Full**: For traditional, sequential development
- **MVP Incremental**: For iterative development with validation
- **MVP Incremental TDD**: For maximum quality with iteration
- **Individual**: For specific, targeted tasks

## Testing Workflows

```bash
# Test all workflows
python run.py test workflow

# Test specific workflow
python tests/test_workflows.py --workflow mvp_incremental

# Run workflow with example
python run.py workflow mvp_incremental --task "Create a calculator"
```

## Advanced Features

### MVP Incremental Specialties
- **Requirement Expansion**: Automatically expands vague requirements
- **Feature Dependencies**: Orders features based on dependencies
- **Error Recovery**: Intelligent retry with different approaches
- **Progress Monitoring**: Real-time progress tracking
- **Stagnation Detection**: Prevents infinite loops

### Workflow Visualization
Generate workflow diagrams:
```bash
python workflows/workflow_visualizer.py
```

## Related Documentation

- [Workflows Overview](../docs/workflows/README.md)
- [MVP Incremental Guide](../docs/workflows/mvp-incremental/README.md)
- [Data Flow](../docs/workflows/data-flow.md)
- [Architecture](../docs/developer-guide/architecture/README.md)