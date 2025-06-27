#!/bin/bash

set -euo pipefail

# Phase 5 Integration Tests: Orchestration & API Testing
# This script runs comprehensive Phase 5 integration tests for Agent Blackwell
# focusing on orchestration task routing, API endpoints, monitoring, and system integration.

# Log all script output to file
# We output everything to a temporary file first, then copy to timestamped log at the end
TEMP_LOG_FILE="/tmp/phase5_test_output.log"
exec > >(tee "$TEMP_LOG_FILE") 2>&1

# ANSI color codes for output formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TEST_DIR="$PROJECT_ROOT/tests/integration"
COMPOSE_FILE="$PROJECT_ROOT/docker-compose-test.yml"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$PROJECT_ROOT/logs/phase5_integration_tests_$TIMESTAMP.log"

# Test categories
TEST_CATEGORIES=("orchestration" "api" "monitoring" "system")
TEST_DESCRIPTIONS=(
    "Task routing, lifecycle, agent coordination"
    "REST endpoints, ChatOps, error handling"
    "Metrics, observability, health checks"
    "End-to-end workflows, performance, resilience"
)

get_test_description() {
    local category=$1
    case $category in
        orchestration) echo "Task routing, lifecycle, agent coordination" ;;
        api) echo "REST endpoints, ChatOps, error handling" ;;
        monitoring) echo "Metrics, observability, health checks" ;;
        system) echo "End-to-end workflows, performance, resilience" ;;
        *) echo "Unknown category" ;;
    esac
}

# Default test options
RUN_ALL=true
VERBOSE=false
QUICK_MODE=false
CLEANUP_AFTER=true
SHOW_COVERAGE=false
PARALLEL=false

print_header() {
    echo -e "${WHITE}================================================${NC}"
    echo -e "${WHITE}  Agent Blackwell - Phase 5 Integration Tests${NC}"
    echo -e "${WHITE}  Orchestration & API Integration Testing${NC}"
    echo -e "${WHITE}================================================${NC}"
    echo -e "${CYAN}Timestamp: $(date)${NC}"
    echo -e "${CYAN}Project Root: $PROJECT_ROOT${NC}"
    echo -e "${CYAN}Log File: $LOG_FILE${NC}"
    echo ""
}

print_usage() {
    echo -e "${WHITE}Usage: $0 [OPTIONS] [TEST_CATEGORY]${NC}"
    echo ""
    echo -e "${YELLOW}Test Categories:${NC}"
    for category in "${TEST_CATEGORIES[@]}"; do
        description=$(get_test_description "$category")
        echo -e "  ${GREEN}$category${NC} - $description"
    done
    echo ""
    echo -e "${YELLOW}Options:${NC}"
    echo -e "  ${GREEN}-h, --help${NC}          Show this help message"
    echo -e "  ${GREEN}-v, --verbose${NC}       Enable verbose output"
    echo -e "  ${GREEN}-q, --quick${NC}         Quick mode (skip slow tests)"
    echo -e "  ${GREEN}--no-cleanup${NC}        Don't cleanup containers after tests"
    echo -e "  ${GREEN}--coverage${NC}          Show test coverage report"
    echo -e "  ${GREEN}--parallel${NC}          Run tests in parallel"
    echo -e "  ${GREEN}--list-tests${NC}        List all available tests without running"
    echo ""
    echo -e "${YELLOW}Examples:${NC}"
    echo -e "  ${CYAN}$0${NC}                    # Run all Phase 5 tests"
    echo -e "  ${CYAN}$0 orchestration${NC}     # Run only orchestration tests"
    echo -e "  ${CYAN}$0 api --verbose${NC}     # Run API tests with verbose output"
    echo -e "  ${CYAN}$0 --quick --parallel${NC} # Quick parallel test run"
}

check_prerequisites() {
    echo -e "${BLUE}Checking prerequisites...${NC}"
    
    # Check if Docker is available
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Error: Docker is not installed or not in PATH${NC}"
        exit 1
    fi
    
    # Check if Docker Compose is available
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}Error: Docker Compose is not installed or not in PATH${NC}"
        exit 1
    fi
    
    # Check if test compose file exists
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        echo -e "${RED}Error: Test compose file not found: $COMPOSE_FILE${NC}"
        exit 1
    fi
    
    # Check if test directories exist
    for category in "${TEST_CATEGORIES[@]}"; do
        test_path="$TEST_DIR/$category"
        if [[ ! -d "$test_path" ]]; then
            echo -e "${YELLOW}Warning: Test directory not found: $test_path${NC}"
        fi
    done
    
    # Create logs directory
    mkdir -p "$(dirname "$LOG_FILE")"
    
    echo -e "${GREEN}✓ Prerequisites check completed${NC}"
}

start_test_environment() {
    echo -e "${BLUE}Starting test environment...${NC}"
    
    # Stop any existing containers
    docker-compose -f "$COMPOSE_FILE" down --remove-orphans 2>/dev/null || true
    
    # Start test environment
    if [[ "$VERBOSE" == "true" ]]; then
        docker-compose -f "$COMPOSE_FILE" up -d
    else
        docker-compose -f "$COMPOSE_FILE" up -d > /dev/null 2>&1
    fi
    
    # Wait for services to be ready with retry logic
    echo -e "${YELLOW}Waiting for services to be ready...${NC}"
    
    local max_attempts=30
    local attempt=1
    local wait_time=2
    
    # Check Redis connectivity with retries
    echo -n "Checking Redis connectivity"
    while [ $attempt -le $max_attempts ]; do
        if docker-compose -f "$COMPOSE_FILE" exec -T redis-test redis-cli ping > /dev/null 2>&1; then
            echo -e "\n${GREEN}✓ Redis is ready${NC}"
            break
        else
            echo -n "."
            sleep $wait_time
            ((attempt++))
            if [ $attempt -eq 10 ]; then
                wait_time=3
            elif [ $attempt -eq 20 ]; then
                wait_time=5
            fi
        fi
    done
    
    if [ $attempt -gt $max_attempts ]; then
        echo -e "\n${RED}✗ Redis failed to respond after $max_attempts attempts${NC}"
        echo -e "${YELLOW}Checking Redis logs:${NC}"
        docker-compose -f "$COMPOSE_FILE" logs redis-test | tail -20
        cleanup_test_environment
        exit 1
    fi
    
    # Check if app container is healthy with retries
    attempt=1
    wait_time=2
    echo -n "Checking Application container"
    while [ $attempt -le $max_attempts ]; do
        if docker-compose -f "$COMPOSE_FILE" ps app-test | grep -q "Up"; then
            echo -e "\n${GREEN}✓ Application container is running${NC}"
            # Additional check for API readiness
            if curl -f -s http://localhost:8001/health > /dev/null 2>&1; then
                echo -e "${GREEN}✓ Application API is responding${NC}"
                break
            else
                echo -n "."
                sleep $wait_time
                ((attempt++))
            fi
        else
            echo -n "."
            sleep $wait_time
            ((attempt++))
            if [ $attempt -eq 10 ]; then
                wait_time=3
            elif [ $attempt -eq 20 ]; then
                wait_time=5
            fi
        fi
    done
    
    if [ $attempt -gt $max_attempts ]; then
        echo -e "\n${RED}✗ Application container failed to start properly${NC}"
        echo -e "${YELLOW}Checking application logs:${NC}"
        docker-compose -f "$COMPOSE_FILE" logs app-test | tail -20
        cleanup_test_environment
        exit 1
    fi
    
    # Brief additional wait to ensure all services are fully initialized
    echo -e "${YELLOW}Waiting for final service initialization...${NC}"
    sleep 5
    
    echo -e "${GREEN}✓ Test environment is ready${NC}"
}

cleanup_test_environment() {
    if [[ "$CLEANUP_AFTER" == "true" ]]; then
        echo -e "${BLUE}Cleaning up test environment...${NC}"
        docker-compose -f "$COMPOSE_FILE" down --remove-orphans --volumes
        echo -e "${GREEN}✓ Test environment cleaned up${NC}"
    else
        echo -e "${YELLOW}Skipping cleanup (--no-cleanup specified)${NC}"
    fi
}

list_available_tests() {
    echo -e "${WHITE}Available Phase 5 Integration Tests:${NC}"
    echo ""
    
    for category in "${TEST_CATEGORIES[@]}"; do
        description=$(get_test_description "$category")
        echo -e "${GREEN}Category: $category${NC} - $description"
        test_path="$TEST_DIR/$category"
        
        if [[ -d "$test_path" ]]; then
            find "$test_path" -name "test_*.py" -type f | while read -r test_file; do
                echo -e "  ${CYAN}$(basename "$test_file")${NC}"
                
                # Extract test function names
                if command -v grep &> /dev/null; then
                    grep -E "^\s*def test_" "$test_file" | sed 's/def /    /' | sed 's/(.*/:/' | head -5
                fi
            done
            echo ""
        else
            echo -e "  ${RED}Directory not found: $test_path${NC}"
            echo ""
        fi
    done
}

run_test_category() {
    local category=$1
    local test_path="$TEST_DIR/$category"
    
    echo -e "${PURPLE}Running $category tests...${NC}"
    echo -e "${CYAN}Test path: $test_path${NC}"
    
    if [[ ! -d "$test_path" ]]; then
        echo -e "${RED}✗ Test directory not found: $test_path${NC}"
        return 1
    fi
    
    # Convert host path to container path
    # Inside the container, everything is mounted at /app
    local container_test_path="/app/tests/integration/$category"
    
    # Build pytest command
    local pytest_cmd="python -m pytest"
    
    # Add verbosity
    if [[ "$VERBOSE" == "true" ]]; then
        pytest_cmd="$pytest_cmd -v -s"
    else
        pytest_cmd="$pytest_cmd -q"
    fi
    
    # Add parallel execution
    if [[ "$PARALLEL" == "true" ]]; then
        pytest_cmd="$pytest_cmd -n auto"
    fi
    
    # Add quick mode markers
    if [[ "$QUICK_MODE" == "true" ]]; then
        pytest_cmd="$pytest_cmd -m 'not slow'"
    fi
    
    # Add coverage if requested
    if [[ "$SHOW_COVERAGE" == "true" ]]; then
        pytest_cmd="$pytest_cmd --cov=src --cov-report=term-missing"
    fi
    
    # Run tests in Docker container
    local docker_cmd="docker-compose -f $COMPOSE_FILE exec -T test-runner $pytest_cmd $container_test_path"
    
    echo -e "${CYAN}Executing: $docker_cmd${NC}"
    
    if eval "$docker_cmd" | tee -a "$LOG_FILE"; then
        echo -e "${GREEN}✓ $category tests completed successfully${NC}"
        return 0
    else
        echo -e "${RED}✗ $category tests failed${NC}"
        return 1
    fi
}

run_all_tests() {
    local failed_categories=()
    local total_start_time=$(date +%s)
    
    echo -e "${WHITE}Running all Phase 5 integration tests...${NC}"
    
    for category in "${TEST_CATEGORIES[@]}"; do
        local start_time=$(date +%s)
        
        if run_test_category "$category"; then
            local end_time=$(date +%s)
            local duration=$((end_time - start_time))
            echo -e "${GREEN}✓ $category tests completed in ${duration}s${NC}"
        else
            failed_categories+=("$category")
            local end_time=$(date +%s)
            local duration=$((end_time - start_time))
            echo -e "${RED}✗ $category tests failed after ${duration}s${NC}"
        fi
        echo ""
    done
    
    local total_end_time=$(date +%s)
    local total_duration=$((total_end_time - total_start_time))
    
    # Print summary
    echo -e "${WHITE}================================================${NC}"
    echo -e "${WHITE}Phase 5 Integration Tests Summary${NC}"
    echo -e "${WHITE}================================================${NC}"
    echo -e "${CYAN}Total execution time: ${total_duration}s${NC}"
    echo -e "${CYAN}Log file: $LOG_FILE${NC}"
    
    if [[ ${#failed_categories[@]} -eq 0 ]]; then
        echo -e "${GREEN}✓ All test categories passed!${NC}"
        return 0
    else
        echo -e "${RED}✗ Failed categories: ${failed_categories[*]}${NC}"
        return 1
    fi
}

run_specific_test_category() {
    local category=$1
    
    local found=false
    for test_cat in "${TEST_CATEGORIES[@]}"; do
        if [[ "$test_cat" == "$category" ]]; then
            found=true
            break
        fi
    done
    
    if [[ "$found" == "false" ]]; then
        echo -e "${RED}Error: Unknown test category '$category'${NC}"
        echo -e "${YELLOW}Available categories: ${TEST_CATEGORIES[*]}${NC}"
        exit 1
    fi
    
    echo -e "${WHITE}Running $category tests only...${NC}"
    
    if run_test_category "$category"; then
        echo -e "${GREEN}✓ $category tests completed successfully${NC}"
        return 0
    else
        echo -e "${RED}✗ $category tests failed${NC}"
        return 1
    fi
}

generate_test_report() {
    local report_file="$PROJECT_ROOT/reports/phase5_integration_test_report_$TIMESTAMP.html"
    
    echo -e "${BLUE}Generating test report...${NC}"
    
    # Create reports directory
    mkdir -p "$(dirname "$report_file")"
    
    # Generate HTML report if pytest-html is available
    local pytest_cmd="python -m pytest --html=$report_file --self-contained-html"
    
    if [[ "$PARALLEL" == "true" ]]; then
        pytest_cmd="$pytest_cmd -n auto"
    fi
    
    # Run report generation in container
    docker-compose -f "$COMPOSE_FILE" exec -T test-runner $pytest_cmd "$TEST_DIR" || true
    
    if [[ -f "$report_file" ]]; then
        echo -e "${GREEN}✓ Test report generated: $report_file${NC}"
    else
        echo -e "${YELLOW}Warning: Could not generate HTML report${NC}"
    fi
}

main() {
    local test_category=""
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                print_usage
                exit 0
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -q|--quick)
                QUICK_MODE=true
                shift
                ;;
            --no-cleanup)
                CLEANUP_AFTER=false
                shift
                ;;
            --coverage)
                SHOW_COVERAGE=true
                shift
                ;;
            --parallel)
                PARALLEL=true
                shift
                ;;
            --list-tests)
                list_available_tests
                exit 0
                ;;
            --report)
                generate_test_report
                exit 0
                ;;
            -*)
                echo -e "${RED}Error: Unknown option $1${NC}"
                print_usage
                exit 1
                ;;
            *)
                if [[ -z "$test_category" ]]; then
                    test_category="$1"
                else
                    echo -e "${RED}Error: Multiple test categories specified${NC}"
                    print_usage
                    exit 1
                fi
                shift
                ;;
        esac
    done
    
    # Start execution
    print_header
    
    # Check prerequisites
    check_prerequisites
    
    # Start test environment
    start_test_environment
    
    # Set up cleanup trap
    trap cleanup_test_environment EXIT
    
    # Run tests
    local exit_code=0
    
    if [[ -n "$test_category" ]]; then
        run_specific_test_category "$test_category" || exit_code=1
    else
        run_all_tests || exit_code=1
    fi
    
    # Generate report if coverage was requested
    if [[ "$SHOW_COVERAGE" == "true" ]]; then
        generate_test_report
    fi
    
    # Final output
    echo ""
    if [[ $exit_code -eq 0 ]]; then
        echo -e "${GREEN}🎉 Phase 5 integration tests completed successfully!${NC}"
    else
        echo -e "${RED}❌ Phase 5 integration tests failed!${NC}"
        echo -e "${YELLOW}Check log file for details: $LOG_FILE${NC}"
    fi
    
    # Copy complete log file to timestamped location
    echo -e "${CYAN}Saving detailed logs to: $LOG_FILE${NC}"
    cp "$TEMP_LOG_FILE" "$LOG_FILE"
    echo "Detailed test logs saved to: $LOG_FILE" >> "$LOG_FILE"

    exit $exit_code
}

# Run main function with all arguments
main "$@"
