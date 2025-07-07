# MVP Incremental Workflow Examples

This directory contains example scripts demonstrating various features and capabilities of the MVP Incremental workflow.

## Available Examples

### 1. Calculator with Tests (`calculator_with_tests.py`)
**Demonstrates:** Phase 9 - Test Execution
- Automatic test generation and execution
- Test-driven development workflow
- Fixing code based on test failures
- Comprehensive test coverage

```bash
python calculator_with_tests.py
```

### 2. TODO API with Validation (`todo_api_with_validation.py`)
**Demonstrates:** Validation and Retry Mechanisms
- Using configuration presets
- Complex feature implementation
- API development with FastAPI
- Automatic error detection and fixing

```bash
python todo_api_with_validation.py
```

### 3. File Processor with Error Recovery (`file_processor_retry.py`)
**Demonstrates:** Error Recovery and Retry Logic
- Handling validation failures
- Context-aware error fixing
- Edge case management
- Progressive refinement

```bash
python file_processor_retry.py
```

### 4. Data Pipeline with Dependencies (`data_pipeline_dependencies.py`)
**Demonstrates:** Feature Dependency Management
- Automatic dependency detection
- Ordered feature implementation
- Complex multi-stage workflows
- Full pipeline integration

```bash
python data_pipeline_dependencies.py
```

## Learning Path

1. **Start with Calculator**: Simple example to understand the basic workflow
2. **Try TODO API**: See how presets and validation work
3. **Run File Processor**: Understand error recovery mechanisms
4. **Build Data Pipeline**: Experience complex dependency management

## Key Features Highlighted

- **Feature-by-Feature Implementation**: See how requirements are broken down
- **Validation and Testing**: Automatic code validation and test execution
- **Error Recovery**: Smart retry mechanisms with context
- **Dependency Management**: Automatic ordering of related features
- **Configuration Presets**: Using pre-configured settings
- **Progress Tracking**: Real-time visibility into workflow execution

## Tips for Running Examples

1. Ensure the orchestrator is running:
   ```bash
   python orchestrator/orchestrator_agent.py
   ```

2. Examples create output in the `generated/` directory

3. Watch the console output to see:
   - Feature parsing and ordering
   - Validation results
   - Retry attempts
   - Test execution
   - Final results

4. Check the generated code to see the final implementation

## Customizing Examples

Feel free to modify the requirements in any example to see how the workflow adapts:
- Add more complex features
- Introduce intentional challenges
- Change configuration settings
- Combine features from different examples