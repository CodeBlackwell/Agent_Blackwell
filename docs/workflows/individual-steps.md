# Individual Steps Workflow

## Overview

The Individual Steps workflow allows you to execute specific phases of the development process independently. This provides maximum flexibility for custom workflows, debugging, and iterative development where you need fine-grained control over each step.

## Available Steps

### 1. Planning Step
Execute only the planning phase to analyze requirements and create implementation plans.

```bash
python run.py workflow individual --step planning --task "Design a user authentication system"
```

**Output**: Detailed implementation plan with architecture decisions

### 2. Design Step
Run the design phase to create technical specifications and system design.

```bash
python run.py workflow individual --step design --task "Design database schema for e-commerce platform"
```

**Output**: Technical design documents, schemas, and API specifications

### 3. Implementation Step
Execute only the coding phase based on existing plans or requirements.

```bash
python run.py workflow individual --step implementation --task "Implement the user service based on the design document"
```

**Output**: Generated source code files

### 4. Test Writing Step
Generate tests for existing code or specifications.

```bash
python run.py workflow individual --step test-writing --task "Write unit tests for the authentication module"
```

**Output**: Test files with comprehensive test cases

### 5. Review Step
Perform code review on existing code.

```bash
python run.py workflow individual --step review --code-path "./src/auth_service.py"
```

**Output**: Review comments and improvement suggestions

### 6. Execution Step
Run tests and validate code functionality.

```bash
python run.py workflow individual --step execution --test-path "./tests/"
```

**Output**: Test execution results and coverage reports

## Configuration

```python
INDIVIDUAL_STEPS_CONFIG = {
    "planning": {
        "max_depth": 3,
        "include_timeline": True,
        "detail_level": "high"
    },
    "design": {
        "include_diagrams": True,
        "specification_format": "markdown",
        "api_style": "REST"
    },
    "implementation": {
        "code_style": "PEP8",
        "include_comments": True,
        "error_handling": "comprehensive"
    },
    "test_writing": {
        "framework": "pytest",
        "coverage_target": 80,
        "include_edge_cases": True
    },
    "review": {
        "check_security": True,
        "check_performance": True,
        "suggest_refactoring": True
    },
    "execution": {
        "timeout": 300,
        "parallel": True,
        "verbose": True
    }
}
```

## Use Cases

### 1. Iterative Development
```bash
# First, plan the feature
python run.py workflow individual --step planning --task "Add real-time notifications"

# Review and refine the plan, then design
python run.py workflow individual --step design --task "Design notification system based on plan"

# Implement after design approval
python run.py workflow individual --step implementation --task "Implement notification service"
```

### 2. Code Review Pipeline
```bash
# Review existing code
python run.py workflow individual --step review --code-path "./src/"

# Write tests for reviewed code
python run.py workflow individual --step test-writing --task "Write tests for notification service"

# Execute tests
python run.py workflow individual --step execution --test-path "./tests/test_notifications.py"
```

### 3. Test-First Development
```bash
# Write tests first
python run.py workflow individual --step test-writing --task "Tests for payment processing"

# Then implement to pass tests
python run.py workflow individual --step implementation --task "Implement payment processor to pass tests"
```

### 4. Documentation Generation
```bash
# Generate design docs from existing code
python run.py workflow individual --step design --reverse-engineer --code-path "./src/"
```

## Advanced Features

### Chaining Steps
You can chain multiple individual steps:

```python
from workflows.workflow_manager import execute_workflow

# Chain planning and design
result = execute_workflow(
    requirements="Create a chat application",
    workflow_type="individual",
    config={
        "steps": ["planning", "design"],
        "pass_outputs": True  # Pass output from one step to next
    }
)
```

### Custom Step Configuration
Override default configuration per step:

```bash
python run.py workflow individual --step implementation \
  --task "Implement auth service" \
  --config '{"code_style": "Google", "include_type_hints": true}'
```

### Conditional Execution
```python
# Execute review only if tests pass
result = execute_workflow(
    requirements="Review if tests pass",
    workflow_type="individual",
    config={
        "steps": ["execution", "review"],
        "conditional": {
            "review": "execution.success == true"
        }
    }
)
```

## Integration with Other Workflows

Individual steps can be integrated into custom workflows:

```python
# Custom workflow mixing individual steps and full workflows
custom_workflow = {
    "phases": [
        {"type": "individual", "step": "planning"},
        {"type": "full", "skip_planning": True},
        {"type": "individual", "step": "review"}
    ]
}
```

## Best Practices

1. **Use for Debugging**: Isolate problematic phases in larger workflows
2. **Iterative Refinement**: Run steps multiple times with refined inputs
3. **Custom Pipelines**: Build specialized workflows for your needs
4. **Quality Gates**: Use review step as a quality checkpoint
5. **Parallel Execution**: Run independent steps concurrently

## Error Handling

Each step has specific error handling:

- **Planning**: Handles ambiguous requirements with clarification requests
- **Design**: Validates design completeness and consistency
- **Implementation**: Syntax and logic error detection
- **Test Writing**: Ensures test completeness and validity
- **Review**: Categorizes issues by severity
- **Execution**: Timeout and resource management

## Performance Considerations

- Individual steps have lower overhead than full workflows
- Steps can be cached for repeated execution
- Parallel step execution is supported
- Resource usage is optimized per step

## Troubleshooting

### Step Not Producing Output
```bash
# Enable verbose mode
python run.py workflow individual --step planning --task "..." --verbose

# Check step-specific logs
cat logs/individual_step_planning_*.log
```

### Step Failing Repeatedly
1. Check input format matches step expectations
2. Verify prerequisites (e.g., design before implementation)
3. Review step-specific configuration
4. Enable debug mode for detailed errors

### Performance Issues
1. Use caching for repeated executions
2. Optimize step configuration (reduce depth, disable features)
3. Run resource-intensive steps separately
4. Monitor system resources during execution

## Related Documentation

- [Workflows Overview](README.md)
- [Full Workflow](full-workflow.md)
- [TDD Workflow](tdd-workflow.md)
- [Workflow Configuration](../reference/workflow-configuration.md)