# Demo and Example Scripts

This directory contains demonstration and example scripts that showcase various workflow capabilities.

## Overview

These demo scripts provide:
- Quick examples of workflow functionality
- Simple test cases for manual testing
- Demonstration of specific features
- Learning resources for understanding the system

## Demo Scripts

### test_enhanced_tdd_demo.py
Demonstrates the enhanced TDD workflow with comprehensive features.

**Features Demonstrated:**
- Complete TDD cycle with real test execution
- File management and project organization
- Test failure handling and recovery
- Multiple iteration support

**Usage:**
```bash
python tests/demo/test_enhanced_tdd_demo.py
```

### test_tdd_demo.py
Basic TDD workflow demonstration with simple examples.

**Features Demonstrated:**
- Basic RED-GREEN-REFACTOR cycle
- Simple test-first development
- Agent coordination in TDD mode
- Test execution feedback loop

**Usage:**
```bash
python tests/demo/test_tdd_demo.py
```

### test_short_mode_simple.py
Demonstrates the short/simple mode for quick iterations.

**Features Demonstrated:**
- Minimal complexity examples
- Quick workflow execution
- Basic agent interactions
- Simplified output format

**Usage:**
```bash
python tests/demo/test_short_mode_simple.py
```

## Running Demo Scripts

### Using the Test Runner
```bash
# Run all demos
./test_runner.py demo

# Run specific demo category
./test_runner.py demo -v
```

### Direct Execution
```bash
# Run individual demo
python tests/demo/test_tdd_demo.py

# Run with custom parameters (if supported)
python tests/demo/test_enhanced_tdd_demo.py --verbose
```

## Prerequisites

1. **Orchestrator**: Must be running on port 8080
   ```bash
   python orchestrator/orchestrator_agent.py
   ```

2. **API Server** (for some demos): Running on port 8000
   ```bash
   python api/orchestrator_api.py
   ```

3. **Environment**: Virtual environment activated
   ```bash
   source .venv/bin/activate
   ```

## Demo Output

Demo scripts typically create:
- Generated code in `generated/` directory
- Console output with step-by-step progress
- Example artifacts demonstrating features
- Performance metrics and timing information

## Creating New Demos

When adding new demo scripts:
1. Use descriptive names: `test_*_demo.py`
2. Include comprehensive documentation in the script
3. Keep demos focused on specific features
4. Provide clear console output for learning
5. Add usage examples in docstrings

## Tips for Using Demos

1. **Learning**: Start with `test_tdd_demo.py` for basic understanding
2. **Feature Exploration**: Use specific demos to understand features
3. **Debugging**: Demos can help reproduce and debug issues
4. **Customization**: Modify demos to test your own scenarios
5. **Performance**: Use demos to benchmark workflow performance