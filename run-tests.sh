#!/bin/bash

# Agent Blackwell Integration Test Runner
# Simple wrapper script for running integration tests

set -e

COMPOSE_FILE="docker-compose-test.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_usage() {
    echo -e "${BLUE}Agent Blackwell Integration Test Runner${NC}"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  setup     Start the test environment (Redis, mock APIs)"
    echo "  redis     Run Redis integration tests"
    echo "  basic     Run basic Redis tests only"
    echo "  load      Run load/concurrency tests only"
    echo "  fault     Run fault tolerance tests only"
    echo "  agents    Run all agent integration tests (Phase 3)"
    echo "  spec      Run SpecAgent tests only"
    echo "  design    Run DesignAgent tests only"
    echo "  coding    Run CodingAgent tests only"
    echo "  review    Run ReviewAgent tests only"
    echo "  test      Run TestAgent tests only"
    echo "  all       Run all integration tests"
    echo "  status    Show test environment status"
    echo "  logs      Show test environment logs"
    echo "  clean     Stop and remove test environment"
    echo "  reset     Clean and setup fresh environment"
    echo "  help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 setup && $0 redis    # Start environment and run Redis tests"
    echo "  $0 reset && $0 all      # Fresh environment and run all tests"
}

setup_environment() {
    echo -e "${YELLOW}Starting test environment...${NC}"
    docker compose -f $COMPOSE_FILE up -d

    echo -e "${YELLOW}Waiting for services to be ready...${NC}"
    sleep 5

    echo -e "${GREEN}Test environment is ready!${NC}"
    docker compose -f $COMPOSE_FILE ps
}

run_redis_tests() {
    echo -e "${YELLOW}Running Redis integration tests...${NC}"
    docker compose -f $COMPOSE_FILE run --rm test-runner pytest tests/integration/redis_tests/ -v
}

run_basic_tests() {
    echo -e "${YELLOW}Running basic Redis tests...${NC}"
    docker compose -f $COMPOSE_FILE run --rm test-runner pytest tests/integration/redis_tests/test_basic_redis.py -v
}

run_load_tests() {
    echo -e "${YELLOW}Running load and concurrency tests...${NC}"
    docker compose -f $COMPOSE_FILE run --rm test-runner pytest tests/integration/redis_tests/test_concurrency_load.py -v
}

run_fault_tests() {
    echo -e "${YELLOW}Running fault tolerance tests...${NC}"
    docker compose -f $COMPOSE_FILE run --rm test-runner pytest tests/integration/redis_tests/test_fault_tolerance.py -v
}

run_all_tests() {
    echo -e "${YELLOW}Running all integration tests...${NC}"
    docker compose -f $COMPOSE_FILE run --rm test-runner pytest tests/integration/ -v
}

run_agents_tests() {
    echo -e "${YELLOW}Running all agent integration tests...${NC}"
    docker compose -f $COMPOSE_FILE run --rm test-runner pytest tests/integration/agents/ -v
}

run_spec_tests() {
    echo -e "${YELLOW}Running SpecAgent tests...${NC}"
    docker compose -f $COMPOSE_FILE run --rm test-runner pytest tests/integration/agents/test_spec_agent.py -v
}

run_design_tests() {
    echo -e "${YELLOW}Running DesignAgent tests...${NC}"
    docker compose -f $COMPOSE_FILE run --rm test-runner pytest tests/integration/agents/test_design_agent.py -v
}

run_coding_tests() {
    echo -e "${YELLOW}Running CodingAgent tests...${NC}"
    docker compose -f $COMPOSE_FILE run --rm test-runner pytest tests/integration/agents/test_coding_agent.py -v
}

run_review_tests() {
    echo -e "${YELLOW}Running ReviewAgent tests...${NC}"
    docker compose -f $COMPOSE_FILE run --rm test-runner pytest tests/integration/agents/test_review_agent.py -v
}

run_test_tests() {
    echo -e "${YELLOW}Running TestAgent tests...${NC}"
    docker compose -f $COMPOSE_FILE run --rm test-runner pytest tests/integration/agents/test_test_agent.py -v
}

show_status() {
    echo -e "${BLUE}Test environment status:${NC}"
    docker compose -f $COMPOSE_FILE ps
}

show_logs() {
    echo -e "${BLUE}Test environment logs:${NC}"
    docker compose -f $COMPOSE_FILE logs --tail=50 -f
}

clean_environment() {
    echo -e "${YELLOW}Stopping and removing test environment...${NC}"
    docker compose -f $COMPOSE_FILE down -v
    echo -e "${GREEN}Test environment cleaned!${NC}"
}

reset_environment() {
    echo -e "${YELLOW}Resetting test environment...${NC}"
    clean_environment
    echo "Waiting for cleanup..."
    sleep 2
    setup_environment
}

check_prerequisites() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Error: Docker is not installed or not in PATH${NC}"
        exit 1
    fi

    if ! docker compose version &> /dev/null; then
        echo -e "${RED}Error: Docker Compose is not available${NC}"
        echo "Make sure you have Docker Compose V2 installed"
        exit 1
    fi

    if [ ! -f $COMPOSE_FILE ]; then
        echo -e "${RED}Error: $COMPOSE_FILE not found${NC}"
        echo "Make sure you're running this script from the project root"
        exit 1
    fi
}

# Main script logic
case "$1" in
    "setup")
        check_prerequisites
        setup_environment
        ;;
    "redis")
        check_prerequisites
        echo "🔗 Running Redis integration tests..."
        docker compose -f $COMPOSE_FILE up -d
        sleep 2
        docker compose -f $COMPOSE_FILE run --rm test-runner pytest -xvs tests/integration/redis_tests/ 
        docker compose -f $COMPOSE_FILE down
        ;;
    "basic")
        check_prerequisites
        run_basic_tests
        ;;
    "load")
        check_prerequisites
        run_load_tests
        ;;
    "fault")
        check_prerequisites
        run_fault_tests
        ;;
    "agents")
        check_prerequisites
        run_agents_tests
        ;;
    "spec")
        check_prerequisites
        run_spec_tests
        ;;
    "design")
        check_prerequisites
        run_design_tests
        ;;
    "coding")
        check_prerequisites
        run_coding_tests
        ;;
    "review")
        check_prerequisites
        run_review_tests
        ;;
    "test")
        check_prerequisites
        run_test_tests
        ;;
    "all")
        check_prerequisites
        run_all_tests
        ;;
    "status")
        check_prerequisites
        show_status
        ;;
    "logs")
        check_prerequisites
        show_logs
        ;;
    "clean")
        check_prerequisites
        clean_environment
        ;;
    "reset")
        check_prerequisites
        reset_environment
        ;;
    "help"|"--help"|"-h")
        print_usage
        ;;
    "")
        print_usage
        ;;
    *)
        echo -e "${RED}Error: Unknown command '$1'${NC}"
        echo ""
        print_usage
        exit 1
        ;;
esac
