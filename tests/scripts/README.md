# Agent Blackwell Testing Infrastructure

This directory contains the unified testing infrastructure for the Agent Blackwell system. The consolidated test scripts provide comprehensive testing capabilities across all system components, from individual agent testing to end-to-end API validation.

## Quick Start Guide

For immediate testing, run these commands in order:

```bash
# 1. Install dependencies
pip install -r ./tests/scripts/requirements-test.txt

# 2. Run the unified test runner with different test suites
./tests/scripts/run-all-tests.sh phase3  # Agent integration tests
./tests/scripts/run-all-tests.sh phase4  # Vector DB tests
./tests/scripts/run-all-tests.sh phase5  # Orchestration & API tests
./tests/scripts/run-all-tests.sh api     # E2E API validation
```

## Unified Test Runner

The `run-all-tests.sh` script is the single entry point for all test suites in the project. It provides a consistent interface, rich logging, and smart environment detection.

### Key Features

- **Smart Environment Management**: Automatic Docker environment setup and health checks
- **Comprehensive Logging**: Timestamped logs with categories and levels
- **Test Category Organization**: Hierarchical command structure for all test types
- **Consolidated Test Execution**: Single interface for all test suites
- **Enhanced Error Handling**: Consistent error reporting and exit codes

### Usage Examples

```bash
# Run specific test phases
./tests/scripts/run-all-tests.sh phase3  # Agent tests
./tests/scripts/run-all-tests.sh phase4  # Vector DB tests
./tests/scripts/run-all-tests.sh phase5  # Orchestration & API tests

# Run specific agent tests
./tests/scripts/run-all-tests.sh agents all
./tests/scripts/run-all-tests.sh agents spec
./tests/scripts/run-all-tests.sh agents design
./tests/scripts/run-all-tests.sh agents coding
./tests/scripts/run-all-tests.sh agents review
./tests/scripts/run-all-tests.sh agents test

# Run specific Redis tests
./tests/scripts/run-all-tests.sh redis all
./tests/scripts/run-all-tests.sh redis basic
./tests/scripts/run-all-tests.sh redis load
./tests/scripts/run-all-tests.sh redis fault

# Infrastructure management
./tests/scripts/run-all-tests.sh infra setup
./tests/scripts/run-all-tests.sh infra clean
./tests/scripts/run-all-tests.sh infra reset
./tests/scripts/run-all-tests.sh infra status

# View Docker logs
./tests/scripts/run-all-tests.sh logs

# Get help
./tests/scripts/run-all-tests.sh help
```

## Test Components

### 1. `e2e_test_gauntlet.py` - End-to-End API Testing

**Purpose:** Comprehensive end-to-end testing suite for validating all Agent Blackwell API endpoints and workflows.

**Key Features:**
- Health check and root endpoint validation
- Feature request creation and workflow testing
- Synchronous and asynchronous workflow execution
- Streaming endpoint testing with real-time monitoring
- Legacy endpoint compatibility validation
- Interactive test selection and customization
- Comprehensive logging and result reporting
- Agent message monitoring during test execution

**Usage Examples:**

```bash
# Basic usage - run all tests
python ./tests/scripts/e2e_test_gauntlet.py

# Run with custom API URL
python ./tests/scripts/e2e_test_gauntlet.py --base-url http://your-api:8000

# Debug mode - run only first 3 tests
python ./tests/scripts/e2e_test_gauntlet.py --max-tests 3

# Interactive mode with test customization
python ./tests/scripts/e2e_test_gauntlet.py --interactive

# Custom output directory
python ./tests/scripts/e2e_test_gauntlet.py --output-dir custom_logs
```

**Command Line Options:**
- `--max-tests, -n`: Limit number of tests (1-6) for debugging
- `--base-url`: Custom API base URL (default: http://localhost:8000)
- `--interactive`: Enable interactive test selection menu
- `--output-dir`: Custom directory for logs and results (default: logs)

**Test Categories:**
1. **Health Check** - Basic API connectivity
2. **Feature Request** - Request creation and validation
3. **Workflow Status** - Status endpoint testing
4. **Legacy Endpoint** - Backward compatibility
5. **Synchronous Workflow** - Full sync execution (60s)
6. **Streaming Workflow** - Real-time streaming (30s)

### 2. Phase 3 - Agent Integration Testing

**Purpose:** Comprehensive testing and verification of all agent types including mock/real LLM integration, persistence, and inter-agent transitions.

**Supported Agents:**
- **SpecAgent** - Requirements specification generation
- **DesignAgent** - System design and architecture
- **CodingAgent** - Code generation and implementation
- **ReviewAgent** - Code review and quality analysis
- **TestAgent** - Test case generation and validation

**Key Features:**
- Mock LLM integration testing with structured outputs
- Real LLM integration validation (when API keys available)
- Redis persistence and data structure verification
- Agent-to-agent transition testing
- Error handling and recovery validation
- Comprehensive logging and result tracking
- Prerequisites checking and environment validation
- Automatic cleanup and resource management

**Usage:**
```bash
# Run all agent integration tests
./tests/scripts/run-all-tests.sh phase3

# Test specific agent types
./tests/scripts/run-all-tests.sh agents spec
./tests/scripts/run-all-tests.sh agents design
./tests/scripts/run-all-tests.sh agents coding
./tests/scripts/run-all-tests.sh agents review
./tests/scripts/run-all-tests.sh agents test
```

### 3. Phase 4 - Vector Database Testing

**Purpose:** Comprehensive testing of Pinecone/Vector DB integration including embedding operations, semantic search, and knowledge persistence.

**Key Features:**
- Embedding storage and retrieval operations
- Semantic search functionality with similarity scoring
- Index maintenance and management operations
- Knowledge persistence and context retrieval
- Vector database performance testing
- Namespace isolation and multi-tenancy
- Batch operations and bulk data handling
- Mock and real vector DB integration

**Usage:**
```bash
# Run all vector DB integration tests
./tests/scripts/run-all-tests.sh phase4
```

**Test Categories:**
1. **Embedding Operations** - Store, retrieve, update, delete vectors
2. **Semantic Search** - Similarity search with filtering and ranking
3. **Index Management** - Maintenance, optimization, scaling
4. **Knowledge Persistence** - Long-term storage and retrieval
5. **Performance Testing** - Load testing and throughput validation

### 4. Phase 5 - System Integration Testing

**Purpose:** End-to-end system integration testing focusing on orchestration, task routing, API endpoints, and monitoring capabilities.

**Key Features:**
- Task routing and lifecycle management
- Workflow orchestration and agent coordination
- REST API endpoint comprehensive testing
- ChatOps command interface validation
- Monitoring, metrics, and observability testing
- Error handling and fault tolerance validation
- Performance testing and load validation
- Health checks and system resilience

**Usage:**
```bash
# Run all Phase 5 integration tests
./tests/scripts/run-all-tests.sh phase5
```

**Test Categories:**
1. **Orchestration** - Task routing, lifecycle, agent coordination
2. **API** - REST endpoints, ChatOps, error handling
3. **System** - End-to-end workflows, performance, resilience

### 5. `requirements-test.txt` - Testing Dependencies

**Purpose:** Python package dependencies required for running all test scripts.

**Included Packages:**
```
requests>=2.31.0      # HTTP client for API testing
aiohttp>=3.8.5        # Async HTTP client for streaming tests
python-dotenv>=1.0.0  # Environment variable management
```

**Usage:**
```bash
# Install all testing dependencies
pip install -r ./tests/scripts/requirements-test.txt

# Install in virtual environment (recommended)
python -m venv test_env
source test_env/bin/activate  # On Windows: test_env\Scripts\activate
pip install -r ./tests/scripts/requirements-test.txt
```

## Complete Testing Workflow

### Prerequisites Setup

1. **Environment Preparation:**
   ```bash
   # Create and activate virtual environment
   python -m venv agent_test_env
   source agent_test_env/bin/activate  # Windows: agent_test_env\Scripts\activate

   # Install dependencies
   pip install -r ./tests/scripts/requirements-test.txt
   ```

2. **Docker Environment:**
   ```bash
   # Ensure Docker is running
   docker --version
   docker-compose --version

   # Verify project structure
   ls -la  # Should show docker-compose-test.yml and other config files
   ```

### Recommended Testing Sequence

1. **Phase 3 - Agent Integration:**
   ```bash
   ./tests/scripts/run-all-tests.sh phase3
   ```

2. **Phase 4 - Vector Database:**
   ```bash
   ./tests/scripts/run-all-tests.sh phase4
   ```

3. **Phase 5 - System Integration:**
   ```bash
   ./tests/scripts/run-all-tests.sh phase5
   ```

4. **End-to-End API Validation:**
   ```bash
   python ./tests/scripts/e2e_test_gauntlet.py --interactive
   ```

### Log Files and Results

All scripts generate detailed logs in these locations:
- **Test Logs:** `./test_logs/` or `./logs/`
- **Naming Pattern:** `unified_tests_[TIMESTAMP].log`
- **Results Files:** JSON format with test outcomes and metrics
- **Docker Logs:** Available via `./tests/scripts/run-all-tests.sh logs`

## Troubleshooting

### Common Issues

1. **Permission Denied:**
   ```bash
   chmod +x ./tests/scripts/*.sh
   ```

2. **Docker Issues:**
   ```bash
   docker-compose -f docker-compose-test.yml down
   docker system prune -f
   ./tests/scripts/run-all-tests.sh infra clean
   ```

3. **Python Dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r ./tests/scripts/requirements-test.txt --force-reinstall
   ```

4. **Port Conflicts:**
   ```bash
   # Check for running services
   lsof -i :8000 -i :6379 -i :8080

   # Stop conflicting services
   docker-compose down
   ```

### Debug Mode

Most scripts support debug and verbose modes:

```bash
# E2E Gauntlet debug mode
python ./tests/scripts/e2e_test_gauntlet.py --max-tests 1

# Shell scripts with detailed output
bash -x ./tests/scripts/run-all-tests.sh phase3
```

## Adding New Tests

When adding new tests to this infrastructure:

1. **Add test files** to the appropriate directory:
   - Unit tests: `./tests/unit/`
   - Integration tests: `./tests/integration/`
   - System tests: `./tests/integration/system/`

2. **Follow naming conventions:**
   - Test files: `test_*.py`
   - Test functions: `test_*`
   - Test classes: `Test*`

3. **Use pytest fixtures** for common setup and teardown
   - Environment fixtures: `./tests/conftest.py`
   - Category-specific fixtures: `./tests/integration/conftest.py`

4. **Update the unified runner** if needed for new test categories

## Support

For issues with the testing infrastructure:
- Check the generated log files for detailed error information
- Verify all prerequisites are installed and accessible
- Ensure Docker services are running and healthy
- Review the script headers for additional troubleshooting information
