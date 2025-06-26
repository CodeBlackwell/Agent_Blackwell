# Agent Blackwell Scripts

This directory contains utility scripts for testing and validating the Agent Blackwell system. These scripts help automate various testing scenarios and provide consistent verification of system components.

## Available Scripts

### 1. `run_phase3_agent_integration_tests_with_verification.sh`

A comprehensive shell script for running and verifying the Phase 3 agent-specific integration tests.

**Features:**
- Automates testing for all agent types (SpecAgent, DesignAgent, CodingAgent, ReviewAgent, TestAgent)
- Verifies mock and real LLM integration
- Validates data persistence and retrieval
- Checks agent transitions and data format compatibility
- Includes detailed logging and reporting
- Provides cleanup functionality

**Usage:**

To run all agent tests:
```bash
cd /path/to/agent_blackwell
./scripts/run_phase3_agent_integration_tests_with_verification.sh
```

To run tests for a specific agent only:
```bash
# Format: ./run-tests.sh [agent-type]

# For SpecAgent tests only
cd /path/to/agent_blackwell
./run-tests.sh spec

# For DesignAgent tests only
./run-tests.sh design

# For CodingAgent tests only
./run-tests.sh coding

# For ReviewAgent tests only
./run-tests.sh review

# For TestAgent tests only
./run-tests.sh test
```

**Requirements:**
- Docker and Docker Compose V2
- jq (recommended for enhanced test result processing)
- Run from project root directory

### 2. `e2e_test_gauntlet.py`

Python script for running comprehensive end-to-end tests against the Agent Blackwell API to validate all major endpoints and workflows.

**Features:**
- Tests all major API endpoints
- Validates complete workflows
- Provides detailed test reports
- Supports both synchronous and asynchronous testing

**Usage:**
```bash
cd /path/to/agent_blackwell
python ./scripts/e2e_test_gauntlet.py
```

**Requirements:**
- Python 3.8+
- Required Python packages (see requirements-test.txt)

### 3. `requirements-test.txt`

Python package dependencies required for running test scripts.

**Includes:**
- requests>=2.31.0
- aiohttp>=3.8.5
- python-dotenv>=1.0.0

**Usage:**
```bash
pip install -r ./scripts/requirements-test.txt
```

## Running Tests

For a complete testing workflow, follow these steps:

1. Install all dependencies:
   ```bash
   pip install -r ./scripts/requirements-test.txt
   ```

2. Run the Phase 3 agent integration tests:
   ```bash
   # Run all agent tests
   ./scripts/run_phase3_agent_integration_tests_with_verification.sh

   # Or run tests for specific agents
   ./run-tests.sh spec   # SpecAgent only
   ./run-tests.sh design # DesignAgent only
   ./run-tests.sh coding # CodingAgent only
   ./run-tests.sh review # ReviewAgent only
   ./run-tests.sh test   # TestAgent only
   ```

3. Run the E2E API tests:
   ```bash
   python ./scripts/e2e_test_gauntlet.py
   ```

4. Review the test results in the generated log files.

## Adding New Scripts

When adding new scripts to this directory, please follow these guidelines:

1. Include comprehensive documentation in the script header
2. Use consistent error handling and logging
3. Add appropriate command-line arguments and help text
4. Update this README.md with details about the new script
