# Agent Blackwell Scripts

This directory contains utility scripts for testing and validating the Agent Blackwell system. These scripts provide comprehensive testing capabilities across different phases of the system, from individual agent testing to end-to-end API validation and vector database operations.

## Quick Start Guide

For immediate testing, run these commands in order:

```bash
# 1. Install dependencies
pip install -r ./scripts/requirements-test.txt

# 2. Run Phase 3 agent tests
./scripts/run_phase3_agent_integration_tests_with_verification.sh

# 3. Run Phase 4 vector DB tests
./scripts/run_phase4_vector_db_integration_tests_with_verification.sh

# 4. Run Phase 5 orchestration tests
./scripts/run_phase5_orchestration_api_integration_tests.sh

# 5. Run E2E API validation
python ./scripts/e2e_test_gauntlet.py
```

## Available Scripts

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
python ./scripts/e2e_test_gauntlet.py

# Run with custom API URL
python ./scripts/e2e_test_gauntlet.py --base-url http://your-api:8000

# Debug mode - run only first 3 tests
python ./scripts/e2e_test_gauntlet.py --max-tests 3

# Interactive mode with test customization
python ./scripts/e2e_test_gauntlet.py --interactive

# Custom output directory
python ./scripts/e2e_test_gauntlet.py --output-dir custom_logs
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

**Requirements:**
- Python 3.8+
- requests, aiohttp, python-dotenv packages
- Running Agent Blackwell API server

### 2. `run_phase3_agent_integration_tests_with_verification.sh` - Agent Integration Testing

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

**Usage Examples:**

```bash
# Run all agent integration tests
./scripts/run_phase3_agent_integration_tests_with_verification.sh

# Test specific agent types (use base run-tests.sh script)
./run-tests.sh spec      # SpecAgent only
./run-tests.sh design    # DesignAgent only
./run-tests.sh coding    # CodingAgent only
./run-tests.sh review    # ReviewAgent only
./run-tests.sh test      # TestAgent only

# Check environment status
./run-tests.sh status

# Clean up test environment
./run-tests.sh clean
```

**Verification Areas:**
1. **Mock Integration** - Structured output validation
2. **Real LLM Integration** - Authentication and rate limiting
3. **Persistence** - Redis storage and retrieval
4. **Agent Transitions** - Inter-agent data compatibility
5. **Error Handling** - Graceful failure management

**Requirements:**
- Docker and Docker Compose V2
- jq (recommended for JSON processing)
- Must run from project root directory

### 3. `run_phase4_vector_db_integration_tests_with_verification.sh` - Vector Database Testing

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

**Usage Examples:**

```bash
# Run all vector DB integration tests
./scripts/run_phase4_vector_db_integration_tests_with_verification.sh

# Run with detailed logging
./scripts/run_phase4_vector_db_integration_tests_with_verification.sh --verbose

# Test specific categories
./scripts/run_phase4_vector_db_integration_tests_with_verification.sh --category embedding
./scripts/run_phase4_vector_db_integration_tests_with_verification.sh --category search
```

**Test Categories:**
1. **Embedding Operations** - Store, retrieve, update, delete vectors
2. **Semantic Search** - Similarity search with filtering and ranking
3. **Index Management** - Maintenance, optimization, scaling
4. **Knowledge Persistence** - Long-term storage and retrieval
5. **Performance Testing** - Load testing and throughput validation

**Requirements:**
- Docker and Docker Compose V2
- Pinecone API key (for real DB testing)
- Python 3.8+ with vector processing libraries

### 4. `run_phase5_orchestration_api_integration_tests.sh` - System Integration Testing

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

**Usage Examples:**

```bash
# Run all Phase 5 integration tests
./scripts/run_phase5_orchestration_api_integration_tests.sh

# Run specific test categories
./scripts/run_phase5_orchestration_api_integration_tests.sh orchestration
./scripts/run_phase5_orchestration_api_integration_tests.sh api
./scripts/run_phase5_orchestration_api_integration_tests.sh monitoring
./scripts/run_phase5_orchestration_api_integration_tests.sh system

# List available test categories
./scripts/run_phase5_orchestration_api_integration_tests.sh --list

# Show help and usage information
./scripts/run_phase5_orchestration_api_integration_tests.sh --help
```

**Test Categories:**
1. **Orchestration** - Task routing, lifecycle, agent coordination
2. **API** - REST endpoints, ChatOps, error handling
3. **Monitoring** - Metrics, observability, health checks
4. **System** - End-to-end workflows, performance, resilience

**Requirements:**
- Docker and Docker Compose V2
- All system services running (Redis, API, monitoring)
- Python 3.8+ with async testing capabilities

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
pip install -r ./scripts/requirements-test.txt

# Install in virtual environment (recommended)
python -m venv test_env
source test_env/bin/activate  # On Windows: test_env\Scripts\activate
pip install -r ./scripts/requirements-test.txt
```

## Complete Testing Workflow

### Prerequisites Setup

1. **Environment Preparation:**
   ```bash
   # Create and activate virtual environment
   python -m venv agent_test_env
   source agent_test_env/bin/activate  # Windows: agent_test_env\Scripts\activate

   # Install dependencies
   pip install -r ./scripts/requirements-test.txt
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
   ./scripts/run_phase3_agent_integration_tests_with_verification.sh
   ```

2. **Phase 4 - Vector Database:**
   ```bash
   ./scripts/run_phase4_vector_db_integration_tests_with_verification.sh
   ```

3. **Phase 5 - System Integration:**
   ```bash
   ./scripts/run_phase5_orchestration_api_integration_tests.sh
   ```

4. **End-to-End API Validation:**
   ```bash
   python ./scripts/e2e_test_gauntlet.py --interactive
   ```

### Log Files and Results

All scripts generate detailed logs in these locations:
- **Test Logs:** `./test_logs/` or `./logs/`
- **Naming Pattern:** `phase[X]_test_run_[TIMESTAMP].log`
- **Results Files:** JSON format with test outcomes and metrics
- **Docker Logs:** Available via `docker-compose logs [service]`

## Troubleshooting

### Common Issues

1. **Permission Denied:**
   ```bash
   chmod +x ./scripts/*.sh
   ```

2. **Docker Issues:**
   ```bash
   docker-compose -f docker-compose-test.yml down
   docker system prune -f
   ./run-tests.sh clean
   ```

3. **Python Dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r ./scripts/requirements-test.txt --force-reinstall
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
python ./scripts/e2e_test_gauntlet.py --max-tests 1

# Shell scripts with detailed output
bash -x ./scripts/run_phase3_agent_integration_tests_with_verification.sh
```

## Adding New Scripts

When adding new scripts to this directory:

1. **Include comprehensive documentation** in script headers
2. **Use consistent error handling** with proper exit codes
3. **Add command-line arguments** with help text
4. **Follow naming conventions:** `run_phase[X]_[description].sh` or `[purpose]_[type].py`
5. **Update this README.md** with complete usage documentation
6. **Test thoroughly** in both success and failure scenarios
7. **Add logging and result tracking** for debugging and monitoring

## Support

For issues with specific scripts:
- Check the generated log files for detailed error information
- Verify all prerequisites are installed and accessible
- Ensure Docker services are running and healthy
- Review the script headers for additional troubleshooting information
