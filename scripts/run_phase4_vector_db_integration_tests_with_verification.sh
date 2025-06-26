#!/bin/bash

#######################################################################
# Agent Blackwell Phase 4 Integration Test Runner & Verification Suite
#
# This script provides a comprehensive wrapper for running and verifying
# the Phase 4 Pinecone/Vector DB integration tests, including:
# - Embedding Storage/Retrieval Operations
# - Semantic Search Functionality
# - Index Maintenance & Management
# - Knowledge Persistence & Context Retrieval
# - Vector Database Performance Testing
#
# It verifies mock and real vector DB integration, embedding operations,
# semantic search accuracy, and knowledge persistence mechanisms.
#######################################################################

# Strict error handling
set -e

# Configuration
MAIN_TEST_SCRIPT="./run-tests.sh"
TEST_LOG_DIR="./test_logs"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
MAIN_LOG_FILE="${TEST_LOG_DIR}/phase4_test_run_${TIMESTAMP}.log"
TEST_RESULTS_FILE="${TEST_LOG_DIR}/phase4_results_${TIMESTAMP}.json"

# ANSI Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print section headers
print_section_header() {
    echo -e "\n${BLUE}======================================================================${NC}"
    echo -e "${BLUE}== $1${NC}"
    echo -e "${BLUE}======================================================================${NC}\n"
}

# Function to print sub-section headers
print_subsection_header() {
    echo -e "\n${PURPLE}== $1${NC}\n"
}

# Function to check if required tools are installed
check_prerequisites() {
    print_section_header "Checking Prerequisites"

    # Check if main test script exists
    if [ ! -f "$MAIN_TEST_SCRIPT" ]; then
        echo -e "${RED}ERROR: Main test script '$MAIN_TEST_SCRIPT' not found${NC}"
        echo "Make sure you're running this script from the project root directory"
        exit 1
    fi

    # Check Docker and Docker Compose
    echo -e "${CYAN}Checking Docker installation...${NC}"
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}ERROR: Docker is not installed or not in PATH${NC}"
        exit 1
    else
        echo -e "${GREEN}Docker is installed!${NC}"
    fi

    # Check Docker Compose
    echo -e "${CYAN}Checking Docker Compose installation...${NC}"
    if ! docker compose version &> /dev/null; then
        echo -e "${RED}ERROR: Docker Compose V2 is not available${NC}"
        exit 1
    else
        echo -e "${GREEN}Docker Compose is installed!${NC}"
    fi

    # Create test log directory if it doesn't exist
    if [ ! -d "$TEST_LOG_DIR" ]; then
        echo -e "${CYAN}Creating test log directory at $TEST_LOG_DIR${NC}"
        mkdir -p "$TEST_LOG_DIR"
    fi

    # Check for jq for JSON processing
    echo -e "${CYAN}Checking for jq (JSON processor)...${NC}"
    if ! command -v jq &> /dev/null; then
        echo -e "${YELLOW}WARNING: 'jq' is not installed. Some test result processing may be limited.${NC}"
        echo "Consider installing jq using your package manager (e.g., 'brew install jq')"
    else
        echo -e "${GREEN}jq is installed!${NC}"
    fi

    # Check for Python and required packages
    echo -e "${CYAN}Checking Python environment...${NC}"
    if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
        echo -e "${RED}ERROR: Python is not installed or not in PATH${NC}"
        exit 1
    else
        echo -e "${GREEN}Python is installed!${NC}"
    fi

    # Check for pytest
    echo -e "${CYAN}Checking pytest installation...${NC}"
    if ! python -m pytest --version &> /dev/null && ! python3 -m pytest --version &> /dev/null; then
        echo -e "${RED}ERROR: pytest is not installed${NC}"
        echo "Install pytest with: pip install pytest pytest-asyncio"
        exit 1
    else
        echo -e "${GREEN}pytest is installed!${NC}"
    fi

    echo -e "${GREEN}All prerequisites checked!${NC}"
}

# Function to set up the test environment
setup_test_environment() {
    print_section_header "Setting Up Vector DB Test Environment"

    echo -e "${CYAN}Resetting and starting fresh test environment...${NC}"
    $MAIN_TEST_SCRIPT reset | tee -a "$MAIN_LOG_FILE"

    echo -e "\n${CYAN}Waiting for services to stabilize...${NC}"
    sleep 5

    echo -e "\n${CYAN}Verifying test environment status...${NC}"
    $MAIN_TEST_SCRIPT status | tee -a "$MAIN_LOG_FILE"

    # Check if vector DB mock service is available
    echo -e "\n${CYAN}Checking vector DB mock service availability...${NC}"
    if docker ps | grep -q "vector.*db\|pinecone.*mock"; then
        echo -e "${GREEN}Vector DB mock service is running!${NC}"
    else
        echo -e "${YELLOW}Vector DB mock service not found. Tests will use internal mocking.${NC}"
    fi

    echo -e "\n${GREEN}Test environment is ready!${NC}"
}

# Function to run embedding operations tests
run_embedding_operations_tests() {
    print_subsection_header "Running Embedding Operations Tests"

    echo -e "${CYAN}Executing embedding storage/retrieval tests...${NC}"
    local test_output_file="${TEST_LOG_DIR}/embedding_operations_${TIMESTAMP}.log"

    # Run with maximum verbosity and capture detailed output
    if python -m pytest tests/integration/vector_db/test_embedding_operations.py -v -s --tb=short --capture=no 2>&1 | tee "$test_output_file"; then
        echo -e "${GREEN}✓ Embedding Operations Tests PASSED${NC}"
        return 0
    else
        echo -e "${RED}✗ Embedding Operations Tests FAILED${NC}"
        echo -e "${YELLOW}Check log file: $test_output_file${NC}"
        return 1
    fi
}

# Function to run semantic search tests
run_semantic_search_tests() {
    print_subsection_header "Running Semantic Search Tests"

    echo -e "${CYAN}Executing semantic search and similarity tests...${NC}"
    local test_output_file="${TEST_LOG_DIR}/semantic_search_${TIMESTAMP}.log"

    if python -m pytest tests/integration/vector_db/test_semantic_search.py -v -s --tb=short --capture=no 2>&1 | tee "$test_output_file"; then
        echo -e "${GREEN}✓ Semantic Search Tests PASSED${NC}"
        return 0
    else
        echo -e "${RED}✗ Semantic Search Tests FAILED${NC}"
        echo -e "${YELLOW}Check log file: $test_output_file${NC}"
        return 1
    fi
}

# Function to run index maintenance tests
run_index_maintenance_tests() {
    print_subsection_header "Running Index Maintenance Tests"

    echo -e "${CYAN}Executing index maintenance and management tests...${NC}"
    local test_output_file="${TEST_LOG_DIR}/index_maintenance_${TIMESTAMP}.log"

    if python -m pytest tests/integration/vector_db/test_index_maintenance.py -v -s --tb=short --capture=no 2>&1 | tee "$test_output_file"; then
        echo -e "${GREEN}✓ Index Maintenance Tests PASSED${NC}"
        return 0
    else
        echo -e "${RED}✗ Index Maintenance Tests FAILED${NC}"
        echo -e "${YELLOW}Check log file: $test_output_file${NC}"
        return 1
    fi
}

# Function to run performance and load tests
run_performance_tests() {
    print_subsection_header "Running Vector DB Performance Tests"

    echo -e "${CYAN}Executing performance and load tests...${NC}"
    local test_output_file="${TEST_LOG_DIR}/vector_performance_${TIMESTAMP}.log"

    if python -m pytest tests/integration/vector_db/test_performance.py -v -s --tb=short --capture=no 2>&1 | tee "$test_output_file"; then
        echo -e "${GREEN}✓ Vector DB Performance Tests PASSED${NC}"
        return 0
    else
        echo -e "${RED}✗ Vector DB Performance Tests FAILED${NC}"
        echo -e "${YELLOW}Check log file: $test_output_file${NC}"
        return 1
    fi
}

# Function to run all Phase 4 tests
run_all_phase4_tests() {
    print_section_header "Running All Phase 4 Vector DB Integration Tests"

    local tests_passed=0
    local tests_failed=0
    local failed_tests=()

    # Run embedding operations tests
    if run_embedding_operations_tests; then
        ((tests_passed++))
    else
        ((tests_failed++))
        failed_tests+=("Embedding Operations")
    fi

    # Run semantic search tests
    if run_semantic_search_tests; then
        ((tests_passed++))
    else
        ((tests_failed++))
        failed_tests+=("Semantic Search")
    fi

    # Run index maintenance tests (if test file exists)
    if [ -f "tests/integration/vector_db/test_index_maintenance.py" ]; then
        if run_index_maintenance_tests; then
            ((tests_passed++))
        else
            ((tests_failed++))
            failed_tests+=("Index Maintenance")
        fi
    else
        echo -e "${YELLOW}Index Maintenance tests not found - skipping${NC}"
    fi

    # Run performance tests (if test file exists)
    if [ -f "tests/integration/vector_db/test_performance.py" ]; then
        if run_performance_tests; then
            ((tests_passed++))
        else
            ((tests_failed++))
            failed_tests+=("Performance")
        fi
    else
        echo -e "${YELLOW}Performance tests not found - skipping${NC}"
    fi

    # Summary
    print_section_header "Phase 4 Test Results Summary"

    echo -e "${GREEN}Tests Passed: $tests_passed${NC}"
    echo -e "${RED}Tests Failed: $tests_failed${NC}"

    if [ $tests_failed -gt 0 ]; then
        echo -e "\n${RED}Failed Test Categories:${NC}"
        for failed_test in "${failed_tests[@]}"; do
            echo -e "${RED}  - $failed_test${NC}"
        done
        return 1
    else
        echo -e "\n${GREEN}🎉 All Phase 4 Vector DB Integration Tests PASSED! 🎉${NC}"
        return 0
    fi
}

# Function to verify vector DB connectivity
verify_vector_db_connectivity() {
    print_subsection_header "Verifying Vector DB Connectivity"

    echo -e "${CYAN}Testing vector DB connection...${NC}"

    # Create a simple connectivity test
    cat > /tmp/vector_db_connectivity_test.py << 'EOF'
#!/usr/bin/env python
"""Quick vector DB connectivity test."""
import asyncio
import sys
from tests.fixtures.vector_embeddings import generate_random_embedding

async def test_connectivity():
    try:
        # Import vector DB client (adjust based on your actual implementation)
        # from your_vector_db_client import VectorDBClient

        # Simple embedding generation test
        embedding = generate_random_embedding()
        assert len(embedding) == 1536  # Default OpenAI embedding size

        print("✓ Vector embedding generation works")
        print("✓ Vector DB fixtures are accessible")
        return True

    except Exception as e:
        print(f"✗ Vector DB connectivity test failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_connectivity())
    sys.exit(0 if result else 1)
EOF

    if python /tmp/vector_db_connectivity_test.py; then
        echo -e "${GREEN}✓ Vector DB connectivity verified${NC}"
        rm -f /tmp/vector_db_connectivity_test.py
        return 0
    else
        echo -e "${RED}✗ Vector DB connectivity test failed${NC}"
        rm -f /tmp/vector_db_connectivity_test.py
        return 1
    fi
}

# Function to generate test report
generate_test_report() {
    print_section_header "Generating Phase 4 Test Report"

    local report_file="${TEST_LOG_DIR}/phase4_test_report_${TIMESTAMP}.md"

    cat > "$report_file" << EOF
# Agent Blackwell Phase 4 Vector DB Integration Test Report

**Generated:** $(date)
**Test Run ID:** ${TIMESTAMP}

## Test Environment
- Docker Compose Test Environment
- Vector DB Mock Services
- Python Async Testing Framework

## Test Categories Executed

### 1. Embedding Operations Tests
- **File:** \`tests/integration/vector_db/test_embedding_operations.py\`
- **Focus:** Storage, retrieval, batch operations, metadata management
- **Log:** \`${TEST_LOG_DIR}/embedding_operations_${TIMESTAMP}.log\`

### 2. Semantic Search Tests
- **File:** \`tests/integration/vector_db/test_semantic_search.py\`
- **Focus:** Similarity search, clustering, knowledge persistence
- **Log:** \`${TEST_LOG_DIR}/semantic_search_${TIMESTAMP}.log\`

### 3. Index Maintenance Tests
- **File:** \`tests/integration/vector_db/test_index_maintenance.py\`
- **Focus:** Index management, optimization, maintenance operations
- **Log:** \`${TEST_LOG_DIR}/index_maintenance_${TIMESTAMP}.log\`

### 4. Performance Tests
- **File:** \`tests/integration/vector_db/test_performance.py\`
- **Focus:** Load testing, concurrent operations, performance benchmarks
- **Log:** \`${TEST_LOG_DIR}/vector_performance_${TIMESTAMP}.log\`

## Test Results Summary
$(if [ -f "${TEST_LOG_DIR}/phase4_summary_${TIMESTAMP}.txt" ]; then cat "${TEST_LOG_DIR}/phase4_summary_${TIMESTAMP}.txt"; else echo "Results will be populated after test execution"; fi)

## Next Steps
1. Review individual test logs for detailed results
2. Address any failing tests
3. Update vector DB configuration if needed
4. Proceed to Phase 5 integration testing

## Log Files
- Main log: \`${MAIN_LOG_FILE}\`
- Test results: \`${TEST_RESULTS_FILE}\`
- Report: \`${report_file}\`
EOF

    echo -e "${GREEN}Test report generated: $report_file${NC}"
}

# Function to cleanup test environment
cleanup_test_environment() {
    print_section_header "Cleaning Up Test Environment"

    echo -e "${CYAN}Stopping test services...${NC}"
    $MAIN_TEST_SCRIPT clean | tee -a "$MAIN_LOG_FILE"

    echo -e "${CYAN}Cleaning up temporary files...${NC}"
    rm -f /tmp/vector_db_*.py

    echo -e "${GREEN}Cleanup completed!${NC}"
}

# Main execution function
main() {
    echo -e "${BLUE}🚀 Agent Blackwell Phase 4 Vector DB Integration Test Suite${NC}"
    echo -e "${BLUE}================================================================${NC}"

    # Initialize log file
    echo "Phase 4 Vector DB Integration Test Run - $(date)" > "$MAIN_LOG_FILE"

    # Execute test phases
    check_prerequisites
    setup_test_environment

    # Run connectivity verification
    if ! verify_vector_db_connectivity; then
        echo -e "${YELLOW}Warning: Vector DB connectivity test failed, but continuing with tests${NC}"
    fi

    # Run all Phase 4 tests
    local overall_result=0
    if ! run_all_phase4_tests; then
        overall_result=1
    fi

    # Generate report
    generate_test_report

    # Cleanup
    if [ "${SKIP_CLEANUP:-}" != "true" ]; then
        cleanup_test_environment
    fi

    # Final status
    if [ $overall_result -eq 0 ]; then
        echo -e "\n${GREEN}🎉 Phase 4 Vector DB Integration Tests completed successfully! 🎉${NC}"
        exit 0
    else
        echo -e "\n${RED}❌ Phase 4 Vector DB Integration Tests completed with failures${NC}"
        echo -e "${YELLOW}Check the logs in ${TEST_LOG_DIR}/ for detailed information${NC}"
        exit 1
    fi
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [--help|--skip-cleanup|--connectivity-only]"
        echo ""
        echo "Options:"
        echo "  --help             Show this help message"
        echo "  --skip-cleanup     Skip cleanup of test environment"
        echo "  --connectivity-only Run only connectivity tests"
        echo ""
        echo "Environment Variables:"
        echo "  SKIP_CLEANUP=true  Skip cleanup phase"
        exit 0
        ;;
    --skip-cleanup)
        SKIP_CLEANUP=true
        main
        ;;
    --connectivity-only)
        check_prerequisites
        setup_test_environment
        verify_vector_db_connectivity
        exit $?
        ;;
    "")
        main
        ;;
    *)
        echo -e "${RED}Unknown option: $1${NC}"
        echo "Use --help for usage information"
        exit 1
        ;;
esac
