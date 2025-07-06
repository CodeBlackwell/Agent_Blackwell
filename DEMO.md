# 🎬 DEMO - Multi-Agent Coding System in Action

This document provides a comprehensive guide to demonstrating the Multi-Agent Coding System's capabilities through various examples, tests, and API interactions.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start Demos](#quick-start-demos)
3. [API Demonstrations](#api-demonstrations)
4. [Workflow Demonstrations](#workflow-demonstrations)
5. [Test Suite Demonstrations](#test-suite-demonstrations)
6. [Advanced Features](#advanced-features)
7. [Visualization Tools](#visualization-tools)
8. [Web Frontend Interface](#web-frontend-interface)
9. [Real-World Examples](#real-world-examples)

---

## 🔧 Prerequisites

Before running any demos, ensure you have:

1. **Environment Setup**
   ```bash
   # Create virtual environment
   uv venv
   source .venv/bin/activate
   
   # Install dependencies
   uv pip install -r requirements.txt
   ```

2. **Start the Orchestrator** (for most demos)
   ```bash
   python orchestrator/orchestrator_agent.py
   ```

3. **Start the API Server** (for API demos)
   ```bash
   python api/orchestrator_api.py
   ```

---

## 🚀 Quick Start Demos

### 1. Hello World - Simplest Demo
```bash
# The absolute simplest way to see the system work
python hello_agents.py
```
**What it does**: Creates a "Hello World" function with tests using 6 AI agents.

### 2. Interactive Demo with Examples
```bash
# Run interactively - prompts for workflow and task
python simple_example.py

# Or specify parameters
python simple_example.py --workflow tdd --task "Create a password validator"
python simple_example.py --workflow full --task "Build a URL shortener"
python simple_example.py --workflow plan --task "Design a chat application"
```

### 3. Advanced Interactive Demo
```bash
# Full-featured demo with auto-orchestrator startup
python quickstart.py

# Command line options
python quickstart.py --tdd --task "Create a REST API for a blog"
python quickstart.py --full --task "Build a command-line todo app"
```

---

## 🌐 API Demonstrations

### 1. Basic API Demo Script
```bash
# Run the included API demo
python api/demo_api_usage.py
```
**Shows**: Complete workflow execution via REST API with progress monitoring.

### 2. Manual API Testing with curl

#### Submit a TDD Workflow
```bash
curl -X POST http://localhost:8000/execute-workflow \
  -H "Content-Type: application/json" \
  -d '{
    "requirements": "Create a temperature converter between Celsius and Fahrenheit",
    "workflow_type": "tdd"
  }'
```

#### Check Workflow Status
```bash
# Replace {session_id} with the ID from the previous response
curl http://localhost:8000/workflow-status/{session_id}
```

#### List Available Workflows
```bash
curl http://localhost:8000/workflow-types
```

### 3. API Client Test Script
```bash
# Test API endpoints programmatically
python api/test_api_simple.py
```

### 4. Proof of Execution via API
```bash
# Demonstrates proof tracking in API responses
python api/test_proof_in_api.py
```

---

## 🔄 Workflow Demonstrations

### 1. Test-Driven Development (TDD) Workflow
```bash
# Using test runner
python test_workflows.py --workflow tdd --complexity minimal

# Using simple example
python simple_example.py --workflow tdd --task "Create a bank account class"
```
**Flow**: Planning → Design → Test Writing → Implementation → Execution → Review

### 2. Full Development Workflow
```bash
# Using test runner
python test_workflows.py --workflow full --complexity standard

# Using simple example
python simple_example.py --workflow full --task "Build a file encryption tool"
```
**Flow**: Planning → Design → Implementation → Execution → Review

### 3. Individual Step Workflows
```bash
# Just planning
python simple_example.py --workflow plan --task "Design a microservices architecture"

# Just design
python simple_example.py --workflow design --task "Create database schema for e-commerce"

# Just implementation
python simple_example.py --workflow implement --task "Write a binary search function"
```

### 4. Incremental Workflow
```bash
# Test incremental feature development
python tests/test_incremental_workflow.py

# Basic incremental test
python tests/integration/test_incremental_workflow_basic.py
```

---

## 🧪 Test Suite Demonstrations

### 1. Run All Tests with Unified Runner
```bash
# Run everything
./test_runner.py

# Run in parallel (faster)
./test_runner.py -p

# Verbose output
./test_runner.py -v
```

### 2. Unit Tests Only
```bash
# Quick unit tests
./test_runner.py unit

# Or directly with pytest
pytest tests/unit/ -v
```
**Tests**: Error analyzer, feature parser, retry strategies, progress monitoring

### 3. Integration Tests
```bash
# Integration tests only
./test_runner.py integration

# Specific integration test
pytest tests/integration/test_realtime_output.py -v
```

### 4. Workflow Tests
```bash
# All workflow tests
./test_runner.py workflow

# Specific workflow test with options
python test_workflows.py --workflow tdd --complexity complex --verbose
```

### 5. Agent Tests
```bash
# Test all agents
python tests/run_agent_tests.py

# Test specific agent
python agents/planner/test_planner_debug.py
```

### 6. Executor Tests
```bash
# Test Docker execution
python tests/test_executor_docker.py

# Test direct execution
python tests/test_executor_direct.py

# Run all executor tests
python tests/run_executor_tests.py
```

---

## 🌟 Advanced Features

### 1. Real-Time Output Display
```bash
# See real-time agent interactions
python tests/integration/test_realtime_output.py
```
**Shows**: Step-by-step visibility of agent inputs/outputs as they execute.

### 2. Proof of Execution Tracking
```bash
# Test proof integration
python test_proof_integration.py

# Read proof documents
python tests/test_proof_reading_integration.py
```
**Demonstrates**: Complete execution audit trail with Docker container details.

### 3. Dynamic App Naming
```bash
# Test dynamic naming convention
python test_dynamic_naming.py

# See it in action with workflows
python test_naming_integration.py
```
**Shows**: How app directories are named based on requirements (e.g., `20250105_143022_calculator_api_abc123/`).

### 4. Incremental Feature Development
```bash
# Advanced incremental coding
python tests/integration/incremental/test_incremental_integration.py

# API-based incremental test
python tests/integration/test_api_incremental_basic.py
```

---

## 📊 Visualization Tools

### 1. Generate Workflow Diagrams
```bash
# Generate all visualizations
python workflows/workflow_visualizer.py

# System overview only
python workflows/workflow_visualizer.py --system-only

# Specific workflow
python workflows/workflow_visualizer.py --workflow tdd

# Custom output directory
python workflows/workflow_visualizer.py --output-dir custom_viz
```
**Output**: SVG diagrams in `docs/workflow_visualizations/`

### 2. View Generated Diagrams
```bash
# Open in browser (macOS)
open docs/workflow_visualizations/system_overview.svg
open docs/workflow_visualizations/tdd_workflow_flow.svg

# Linux
xdg-open docs/workflow_visualizations/system_overview.svg
```

---

## 🖥️ Web Frontend Interface

### 1. Quick Start with Frontend
```bash
# Step 1: Start the orchestrator
python orchestrator/orchestrator_agent.py

# Step 2: Start the API server
python api/orchestrator_api.py

# Step 3: Open the frontend (choose one method):

# Option A: Direct file access
open frontend/index.html  # macOS
# or
xdg-open frontend/index.html  # Linux

# Option B: Using the included server (recommended)
python frontend/serve.py
# Then open http://localhost:3000 in your browser

# Option C: Using Python's built-in server
cd frontend && python -m http.server 3000
```

### 2. Using the Web Interface

1. **Select Workflow Type**:
   - Full Workflow: Complete development cycle
   - TDD Workflow: Test-driven development
   - Individual Step: Single phase execution

2. **Enter Requirements**:
   - Type your project description in natural language
   - Example: "Create a REST API for managing a book library"

3. **Monitor Progress**:
   - Real-time agent activity display
   - Status updates as workflow progresses
   - View agent outputs in the activity panel

### 3. Frontend Features Demo

#### Basic Code Generation
1. Select "Full Workflow"
2. Enter: "Create a Python class for managing user accounts"
3. Click Send
4. Watch agents collaborate in real-time

#### TDD Development
1. Select "TDD Workflow"
2. Enter: "Build a calculator with unit tests"
3. Observe test-first development approach

#### Individual Steps
1. Select "Individual Step"
2. Choose "Planning"
3. Enter: "Design architecture for a chat application"
4. Get just the planning output

### 4. Testing Frontend Integration
```bash
# Run the frontend test script
python frontend/test_frontend.py

# Test CORS configuration
open frontend/test_cors.html
```

---

## 💼 Real-World Examples

### 1. Build a REST API
```bash
python simple_example.py --workflow tdd --task "Create a REST API for a book library with CRUD operations, pagination, and search"
```

### 2. Create a CLI Tool
```bash
python simple_example.py --workflow full --task "Build a command-line tool for file organization that sorts files by type and date"
```

### 3. Design a System Architecture
```bash
python simple_example.py --workflow plan --task "Design a scalable architecture for a real-time collaboration platform like Google Docs"
```

### 4. Implement an Algorithm
```bash
python simple_example.py --workflow implement --task "Implement a caching mechanism with LRU eviction policy"
```

---

## 📁 Output Locations

After running demos, find generated artifacts in:

- **Generated Code**: `./generated/{timestamp}_{project_name}_{hash}/`
- **Test Outputs**: `./tests/outputs/session_{timestamp}/`
- **Logs**: `./logs/`
- **API Logs**: `./api.log`, `./orchestrator.log`
- **Visualizations**: `./docs/workflow_visualizations/`

---

## 🔍 Monitoring & Debugging

### 1. Watch Orchestrator Logs
```bash
# In a separate terminal
tail -f orchestrator.log
```

### 2. Watch API Logs
```bash
tail -f api.log
```

### 3. Check Test Results
```bash
# View latest test results
cat test_results_*.json | jq .

# Check specific session
ls -la tests/outputs/session_*/
```

### 4. Debug Mode
```bash
# Run with debug output
python test_workflows.py --verbose --debug
```

---

## 🎯 Demo Scenarios by Audience

### For Developers
1. Run `hello_agents.py` for quick overview
2. Try `simple_example.py` with custom tasks
3. Explore unit tests with `./test_runner.py unit`

### For API Users
1. Start with `api/demo_api_usage.py`
2. Try curl commands for manual testing
3. Check `api/test_proof_in_api.py` for advanced features

### For System Architects
1. Generate visualizations with `workflow_visualizer.py`
2. Run workflow tests to see system design
3. Explore incremental workflow capabilities

### For QA/Testing
1. Run full test suite with `./test_runner.py`
2. Check proof of execution features
3. Examine test outputs in `tests/outputs/`

---

## 🚨 Troubleshooting Common Demo Issues

**"Connection refused" errors**
- Ensure orchestrator is running: `python orchestrator/orchestrator_agent.py`
- For API demos, also run: `python api/orchestrator_api.py`

**"Module not found" errors**
- Activate virtual environment: `source .venv/bin/activate`
- Install dependencies: `uv pip install -r requirements.txt`

**Docker-related errors**
- Ensure Docker is running: `docker ps`
- Check Docker permissions

**Slow performance**
- Use parallel test execution: `./test_runner.py -p`
- Run specific tests instead of full suite

---

## 📚 Additional Resources

- **README.md** - Project overview and setup
- **CLAUDE.md** - Detailed system documentation
- **TEST_GUIDE.md** - Comprehensive testing documentation
- **EXAMPLES.md** - Quick start example guide
- **API README** - `api/README.md` for API details