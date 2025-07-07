# 🧪 Comprehensive Testing Guide

This guide provides complete documentation for all tests in the Multi-Agent System codebase, including how to run them, what they test, and their requirements.

## 🚀 Quick Start

### Using the Unified Test Runner (Recommended)

The easiest way to run tests is using our unified test runner:

```bash
# Run all tests
./test_runner.py

# Run specific test categories
./test_runner.py unit              # Run only unit tests
./test_runner.py unit integration  # Run unit and integration tests
./test_runner.py workflow agent    # Run workflow and agent tests

# Run tests in parallel (faster)
./test_runner.py -p

# Run quick tests only (unit tests)
./test_runner.py --quick

# List all available test categories
./test_runner.py -l

# Verbose output
./test_runner.py -v

# CI mode (no emojis, verbose)
./test_runner.py --ci
```

## 📋 Test Categories

### 🔬 Unit Tests
Fast, isolated tests for individual components.

**Location**: `tests/unit/`  
**Framework**: pytest  
**Files**:
- `test_error_analyzer.py` - Error analysis system tests
- `test_feature_orchestrator.py` - Feature orchestration tests
- `test_feature_parser.py` - Feature parsing tests
- `test_incremental_executor.py` - Incremental executor tests
- `test_progress_monitor.py` - Progress monitoring tests
- `test_retry_strategies.py` - Retry mechanism tests
- `test_stagnation_detector.py` - Stagnation detection tests
- `test_validation_system.py` - Validation system tests

**Run individually**:
```bash
# All unit tests
pytest tests/unit/

# Specific test file
pytest tests/unit/incremental/test_error_analyzer.py

# Specific test class or method
pytest tests/unit/incremental/test_error_analyzer.py::TestErrorContext

# With coverage
pytest tests/unit/ --cov=workflows/incremental
```

### 🔗 Integration Tests
Tests for component interactions and end-to-end flows.

**Location**: `tests/integration/`  
**Framework**: pytest  
**Files**:
- `test_incremental_workflow_basic.py` - Basic incremental workflow tests
- `test_api_incremental_basic.py` - API integration tests
- `incremental/test_incremental_integration.py` - Full incremental integration

**Run individually**:
```bash
# All integration tests
pytest tests/integration/

# Specific integration test
pytest tests/integration/test_incremental_workflow_basic.py
```

### 🔄 Workflow Tests
End-to-end workflow validation with comprehensive monitoring.

**Location**: `tests/`  
**Framework**: Standalone scripts  
**Files**:
- `test_workflows.py` - Main workflow testing framework
- `test_incremental_workflow.py` - Incremental workflow testing
- `test_incremental_simple.py` - Simple incremental tests

**Run individually**:
```bash
# Run workflow tests with default settings
python tests/test_workflows.py

# Run specific workflow with specific complexity
python tests/test_workflows.py --workflow tdd --complexity minimal

# Available workflows: tdd, full, incremental, planning, design, implementation, all
# Available complexities: minimal, standard, complex, stress, all

# List available tests
python tests/test_workflows.py --list

# Save artifacts
python tests/test_workflows.py --save-artifacts

# Run incremental workflow tests
python tests/test_incremental_workflow.py
```

### 🤖 Agent Tests
Individual agent functionality tests.

**Location**: `agents/*/` directories  
**Framework**: Custom test runner  
**Test Runner**: `tests/run_agent_tests.py`

**Agent debug scripts**:
- `agents/planner/test_planner_debug.py` - Planner agent tests
- `agents/designer/test_designer_debug.py` - Designer agent tests
- `agents/coder/test_coder_debug.py` - Coder agent tests
- `agents/test_writer/test_test_writer_debug.py` - Test writer agent tests
- `agents/reviewer/test_reviewer_debug.py` - Reviewer agent tests

**Run individually**:
```bash
# Run all agent tests
python tests/run_agent_tests.py

# Run specific agent test
python tests/run_agent_tests.py planner

# Available agents: planner, designer, coder, test_writer, reviewer

# List available agent tests
python tests/run_agent_tests.py --list

# Run without starting orchestrator server
python tests/run_agent_tests.py --no-server

# Run without saving logs
python tests/run_agent_tests.py --no-logs
```

### ⚡ Executor Tests
Code execution and validation tests.

**Location**: `tests/` and `agents/executor/`  
**Framework**: Mixed (unittest, standalone)  
**Files**:
- `test_executor_direct.py` - Direct executor testing
- `test_executor_docker.py` - Docker executor testing
- `test_executor_integration.py` - Executor integration tests
- `run_executor_tests.py` - Executor test runner
- `agents/executor/test_executor_proof.py` - Proof of concept tests

**Run individually**:
```bash
# Run executor integration tests
python tests/test_executor_direct.py

# Run docker executor tests
python tests/test_executor_docker.py

# Run all executor tests with unittest runner
python tests/run_executor_tests.py

# Run with specific unittest options
python tests/run_executor_tests.py -v -f  # verbose, fail fast
```

### 🌐 API Tests
REST API endpoint tests.

**Location**: `api/`  
**Framework**: Mixed (pytest and standalone)  
**Files**:
- `test_orchestrator_api.py` - Orchestrator API tests (pytest)
- `test_api_simple.py` - Simple API testing script
- `test_api_client.py` - API client testing

**Run individually**:
```bash
# Run pytest API tests
pytest api/test_orchestrator_api.py

# Run simple API test script
python api/test_api_simple.py

# Run API client test
python api/test_api_client.py
```

### 📺 Output Tests
Real-time output display tests.

**Location**: Project root  
**Framework**: Standalone script  
**Files**:
- `test_realtime_output.py` - Tests real-time output display

**Run individually**:
```bash
python test_realtime_output.py
```

### 🔴 TDD Tests
Test-Driven Development workflow specific tests.

**Location**: `tests/tdd/`  
**Framework**: Standalone scripts  
**Files**:
- `test_tdd_integration.py` - Complete TDD workflow integration test
- `test_tdd_single_directory.py` - Verifies single directory generation
- `test_tdd_enhanced.py` - Enhanced TDD workflow tests

**Run individually**:
```bash
# All TDD tests
./test_runner.py tdd

# Specific TDD test
python tests/tdd/test_tdd_integration.py
python tests/tdd/test_tdd_single_directory.py
```

### 🎯 Demo Scripts
Example and demonstration scripts for various workflows.

**Location**: `tests/demo/`  
**Framework**: Standalone scripts  
**Files**:
- `test_enhanced_tdd_demo.py` - Enhanced TDD workflow demo
- `test_short_mode_simple.py` - Simple short mode demo
- `test_tdd_demo.py` - Basic TDD demonstration

**Run individually**:
```bash
# All demo scripts
./test_runner.py demo

# Specific demo
python tests/demo/test_tdd_demo.py
```

## 🔧 Prerequisites & Setup

### Required Services

1. **Orchestrator Server** (Port 8080)
   ```bash
   python orchestrator/orchestrator_agent.py
   ```

2. **REST API Server** (Port 8000) - Required for API tests
   ```bash
   python api/orchestrator_api.py
   ```

### Environment Setup

1. **Virtual Environment**
   ```bash
   # Create and activate virtual environment
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install Dependencies**
   ```bash
   uv pip install -r requirements.txt
   ```

3. **Environment Variables**
   Create a `.env` file with required API keys:
   ```
   OPENAI_API_KEY=your_key_here
   ANTHROPIC_API_KEY=your_key_here
   # Other API keys as needed
   ```

4. **Docker** (for executor tests)
   - Install Docker Desktop or Docker Engine
   - Ensure Docker daemon is running

## 📊 Test Output & Artifacts

### Test Output Locations

- **Agent test logs**: `tests/outputs/run_[TIMESTAMP]/`
- **Workflow test artifacts**: `tests/outputs/session_[TIMESTAMP]/`
- **Test results JSON**: `test_results_[TIMESTAMP].json`
- **Generated code**: `generated/app_generated_[TIMESTAMP]/`

### Output Files Created

1. **Session Reports** (`session_report.json`)
   - Test metadata
   - Execution times
   - Success/failure status
   - Agent interactions

2. **Workflow Observations** (`observations.json`)
   - Agent participation metrics
   - Review patterns
   - Retry analysis
   - Performance insights

3. **Execution Reports** (`execution_report.json`)
   - Detailed execution traces
   - Error logs
   - Step-by-step progress

## 🎯 Testing Strategies

### Running Tests by Speed

1. **Quick Tests** (< 1 minute)
   ```bash
   ./test_runner.py --quick  # Unit tests only
   pytest tests/unit/       # Direct pytest
   ```

2. **Medium Tests** (1-5 minutes)
   ```bash
   ./test_runner.py unit integration
   python tests/run_agent_tests.py
   ```

3. **Full Test Suite** (5-15 minutes)
   ```bash
   ./test_runner.py        # All tests
   ./test_runner.py -p     # All tests in parallel
   ```

### Testing Specific Features

1. **Test Incremental Coding**
   ```bash
   pytest tests/unit/incremental/
   python tests/test_incremental_workflow.py
   ```

2. **Test TDD Workflow**
   ```bash
   ./test_runner.py tdd
   python tests/test_workflows.py --workflow tdd
   python tests/tdd/test_tdd_integration.py
   ```

3. **Test Individual Agents**
   ```bash
   python tests/run_agent_tests.py planner
   python tests/run_agent_tests.py coder
   ```

### Debugging Failed Tests

1. **Enable Verbose Output**
   ```bash
   ./test_runner.py -v
   pytest -vv tests/unit/
   ```

2. **Run Specific Test**
   ```bash
   pytest tests/unit/incremental/test_error_analyzer.py::test_specific_method
   ```

3. **Check Logs**
   - Look in `tests/outputs/` for detailed logs
   - Check `test_results_[TIMESTAMP].json` for structured results

## 🐛 Common Issues & Solutions

### Issue: "Orchestrator server not running"
**Solution**: Start the orchestrator server first:
```bash
python orchestrator/orchestrator_agent.py
```

### Issue: "Module not found" errors
**Solution**: Ensure virtual environment is activated:
```bash
source .venv/bin/activate
```

### Issue: Docker tests failing
**Solution**: Check Docker is running:
```bash
docker ps  # Should not error
```

### Issue: API tests failing with connection errors
**Solution**: Start the API server:
```bash
python api/orchestrator_api.py
```

## 🔍 Test Coverage

To check test coverage:

```bash
# Install coverage tools
pip install pytest-cov

# Run with coverage
pytest --cov=agents --cov=workflows --cov=orchestrator

# Generate HTML coverage report
pytest --cov=agents --cov-report=html
# Open htmlcov/index.html in browser
```

## 🚦 CI/CD Integration

For CI/CD pipelines, use:

```bash
# CI mode (no emojis, verbose output)
./test_runner.py --ci

# Or run specific test types
pytest tests/unit/ --tb=short
python tests/test_workflows.py --workflow all --complexity minimal
```

## 📈 Performance Testing

For performance testing:

```bash
# Run stress tests
python tests/test_workflows.py --complexity stress

# Time individual tests
pytest tests/unit/ --durations=10  # Show 10 slowest tests
```

## 🤝 Contributing Tests

When adding new tests:

1. **Unit Tests**: Add to `tests/unit/` with pytest
2. **Integration Tests**: Add to `tests/integration/`
3. **Agent Tests**: Add debug script to agent directory
4. **Update TEST_CATEGORIES** in `test_runner.py` if adding new category

Follow existing patterns for consistency!