#!/bin/bash

#######################################################################
# Agent Blackwell Phase 3 Integration Test Runner & Verification Suite
#
# This script provides a comprehensive wrapper for running and verifying
# the Phase 3 agent-specific integration tests, including:
# - SpecAgent
# - DesignAgent
# - CodingAgent
# - ReviewAgent
# - TestAgent
#
# It verifies mock and real LLM integration, persistence, retrieval,
# and transitions between agent outputs.
#######################################################################

# Strict error handling
set -e

# Configuration
MAIN_TEST_SCRIPT="./run-tests.sh"
TEST_LOG_DIR="./test_logs"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
MAIN_LOG_FILE="${TEST_LOG_DIR}/phase3_test_run_${TIMESTAMP}.log"
TEST_RESULTS_FILE="${TEST_LOG_DIR}/phase3_results_${TIMESTAMP}.json"

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

    echo -e "${GREEN}All prerequisites checked!${NC}"
}

# Function to set up the test environment
setup_test_environment() {
    print_section_header "Setting Up Test Environment"

    echo -e "${CYAN}Resetting and starting fresh test environment...${NC}"
    $MAIN_TEST_SCRIPT reset | tee -a "$MAIN_LOG_FILE"

    echo -e "\n${CYAN}Waiting for services to stabilize...${NC}"
    sleep 5

    echo -e "\n${CYAN}Verifying test environment status...${NC}"
    $MAIN_TEST_SCRIPT status | tee -a "$MAIN_LOG_FILE"

    echo -e "\n${GREEN}Test environment is ready!${NC}"
}

# Function to ensure agent worker is running
ensure_agent_worker_running() {
    print_subsection_header "Ensuring Agent Worker is Running"

    echo -e "${CYAN}Checking agent worker container status...${NC}"
    if ! docker ps | grep agent-blackwell-agent-worker > /dev/null; then
        echo -e "${YELLOW}Agent worker container not running. Starting it...${NC}"
        docker compose -f docker-compose-test.yml up -d agent-worker
        echo -e "${CYAN}Waiting for agent worker to initialize...${NC}"
        sleep 10  # Give it time to start up and initialize
    else
        echo -e "${GREEN}Agent worker container is already running.${NC}"
    fi

    # Verify it's running
    if ! docker ps | grep agent-blackwell-agent-worker > /dev/null; then
        echo -e "${RED}Failed to start agent worker container!${NC}"
        echo -e "${RED}This will cause agent integration tests to fail.${NC}"
        return 1
    else
        echo -e "${GREEN}Agent worker container is running!${NC}"
        # Show logs to verify it's initialized properly
        echo -e "${CYAN}Recent agent worker logs:${NC}"
        docker logs agent-blackwell-agent-worker --tail 10
        return 0
    fi
}

# Function to run a specific agent test
run_agent_test() {
    local agent_name=$1
    local agent_command=$2

    print_subsection_header "Running ${agent_name} Tests"

    echo -e "${CYAN}Executing ${agent_name} integration tests...${NC}"
    # Convert agent_name to lowercase for filename
    local agent_name_lower=$(echo "$agent_name" | tr '[:upper:]' '[:lower:]')
    # Use -vvs flag for maximum verbosity and capturing stderr
    $MAIN_TEST_SCRIPT $agent_command -vvs 2>&1 | tee -a "${TEST_LOG_DIR}/${agent_name_lower}_test_${TIMESTAMP}.log"

    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        echo -e "${GREEN}${agent_name} tests completed successfully!${NC}"
        # Add success to results file
        echo "{\"agent\":\"${agent_name}\",\"status\":\"success\",\"timestamp\":\"$(date -Iseconds)\"}" >> "$TEST_RESULTS_FILE"
        return 0
    else
        echo -e "${RED}${agent_name} tests failed!${NC}"
        # Add failure to results file
        echo "{\"agent\":\"${agent_name}\",\"status\":\"failed\",\"timestamp\":\"$(date -Iseconds)\",\"error\":\"See log for details\"}" >> "$TEST_RESULTS_FILE"
        return 1
    fi
}

# Function to run all agent tests
run_all_agent_tests() {
    print_section_header "Running All Agent Tests"

    # Ensure agent worker is running before running tests
    ensure_agent_worker_running

    echo -e "${CYAN}Starting batch execution of all agent tests...${NC}"
    local all_success=true

    # Run all individual agent tests with verbose output
    run_agent_test "SpecAgent" "spec" || all_success=false
    run_agent_test "DesignAgent" "design" || all_success=false
    run_agent_test "CodingAgent" "coding" || all_success=false
    run_agent_test "ReviewAgent" "review" || all_success=false
    run_agent_test "TestAgent" "test" || all_success=false

    # Check if all tests passed
    if [ "$all_success" = true ]; then
        echo -e "\n${GREEN}All agent tests completed successfully!${NC}"
    else
        echo -e "\n${RED}Some agent tests failed. Check individual logs for details.${NC}"
    fi
}

# Function to verify test results
verify_test_results() {
    print_section_header "Verification Checklist"

    echo -e "${CYAN}The following aspects should be verified in the test results:${NC}\n"

    echo -e "${YELLOW}1. Mock LLM Integration:${NC}"
    echo "   - Each agent correctly processes input requests"
    echo "   - Mock LLM responses are properly handled"
    echo "   - Output contains expected data structure"

    echo -e "\n${YELLOW}2. Real LLM Integration (if available):${NC}"
    echo "   - Actual LLM calls work"
    echo "   - Authentication with LLM services functions properly"
    echo "   - Rate limiting is handled appropriately"

    echo -e "\n${YELLOW}3. Persistence:${NC}"
    echo "   - Agent outputs are correctly stored in Redis"
    echo "   - Data structure is maintained when serializing/deserializing"
    echo "   - Required fields are present in stored data"

    echo -e "\n${YELLOW}4. Agent Transitions:${NC}"
    echo "   - Output from one agent can be used as input to the next agent"
    echo "   - Data format between agents is compatible"
    echo "   - Request IDs are preserved across agent transitions"

    echo -e "\n${YELLOW}5. Error Handling:${NC}"
    echo "   - LLM errors are handled gracefully"
    echo "   - Failed requests are properly reported"
    echo "   - System remains stable under error conditions"

    echo -e "\n${CYAN}To validate these aspects, examine the test logs in:${NC}"
    echo "   $TEST_LOG_DIR"
}

# Function to show test summary
show_test_summary() {
    print_section_header "Test Summary"

    echo -e "${CYAN}Test run completed at:${NC} $(date)"
    echo -e "${CYAN}Main log file:${NC} $MAIN_LOG_FILE"
    echo -e "${CYAN}Test results:${NC} $TEST_RESULTS_FILE"

    if [ -f "$TEST_RESULTS_FILE" ] && command -v jq &> /dev/null; then
        echo -e "\n${CYAN}Test results summary:${NC}"
        jq -r '. | "Agent: \(.agent), Status: \(.status)"' "$TEST_RESULTS_FILE" 2>/dev/null || echo "No test results available"
    fi

    echo -e "\n${CYAN}Environment Status:${NC}"
    $MAIN_TEST_SCRIPT status
}

# Function to clean up resources
cleanup() {
    print_section_header "Cleaning Up Test Environment"

    echo -e "${CYAN}Stopping and removing test containers...${NC}"
    $MAIN_TEST_SCRIPT clean | tee -a "$MAIN_LOG_FILE"

    echo -e "\n${GREEN}Cleanup completed!${NC}"
}

# Print welcome banner
print_section_header "Agent Blackwell Phase 3 Integration Test Suite"
echo "Starting comprehensive test run at: $(date)"
echo "This script will run and verify the Phase 3 agent-specific integration tests"
echo "Test logs will be saved to: $TEST_LOG_DIR"

# Main execution flow
check_prerequisites
setup_test_environment
run_all_agent_tests
verify_test_results
show_test_summary

# Ask if user wants to clean up
echo -e "\n${YELLOW}Do you want to clean up the test environment? (y/n)${NC}"
read -r cleanup_response
if [[ "$cleanup_response" =~ ^[Yy]$ ]]; then
    cleanup
else
    echo -e "${CYAN}Test environment left running for further inspection.${NC}"
    echo -e "${CYAN}Run '$MAIN_TEST_SCRIPT clean' when you're done.${NC}"
fi

echo -e "\n${GREEN}Agent Blackwell Phase 3 Integration Test Suite execution completed!${NC}"
echo "Check the logs for detailed results."
