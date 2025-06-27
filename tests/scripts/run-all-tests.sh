#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# Agent Blackwell Unified Test Runner (alpha)
# -----------------------------------------------------------------------------
# This script is the single entry-point for **ALL** test suites in the project.
# It consolidates the behaviour of multiple legacy wrappers (run-tests.sh,
# phase3/4/5 scripts, e2e_test_gauntlet.py, etc.).  During the transition it
# delegates to those scripts where appropriate while providing a modern
# interface, richer logging, and environment-detection helpers.
# -----------------------------------------------------------------------------

set -euo pipefail

# ------------- Global Configuration ---------------------------------------- #
SCRIPT_VERSION="0.1.0-alpha"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
COMPOSE_FILE="docker-compose-test.yml"
LOG_DIR="$PROJECT_ROOT/logs"
DATE_TAG="$(date +%Y%m%d_%H%M%S)"
LOG_FILE="$LOG_DIR/unified_tests_${DATE_TAG}.log"

# Colour codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ------------- Logging Helpers -------------------------------------------- #
setup_comprehensive_logging() {
    mkdir -p "$LOG_DIR"
    touch "$LOG_FILE"
    echo "# Unified Test Runner Log - ${DATE_TAG}" > "$LOG_FILE"
    echo "version: ${SCRIPT_VERSION}" >> "$LOG_FILE"
    echo "project_root: ${PROJECT_ROOT}" >> "$LOG_FILE"
}

log_with_timestamp() {
    # Usage: log_with_timestamp LEVEL MESSAGE
    local level=$1; shift
    local msg="$*"
    local ts="$(date +%Y-%m-%dT%H:%M:%S%z)"
    echo -e "${ts} [${level}] ${msg}" | tee -a "$LOG_FILE"
}

# Convenience wrappers
log_info()    { log_with_timestamp "INFO"    "$*"; }
log_warn()    { log_with_timestamp "WARN"    "$*"; }
log_error()   { log_with_timestamp "ERROR"   "$*"; }
log_success() { log_with_timestamp "SUCCESS" "$*"; }

# ------------- Environment Detection & Setup ------------------------------ #
check_prerequisites() {
    command -v docker      >/dev/null 2>&1 || { log_error "Docker not found in PATH"; exit 1; }
    docker compose version >/dev/null 2>&1 || { log_error "Docker Compose v2 required"; exit 1; }
    if [[ ! -f "$PROJECT_ROOT/$COMPOSE_FILE" ]]; then
        log_error "${COMPOSE_FILE} not found in project root"
        exit 1
    fi
}

detect_environment_state() {
    # Sets global ENVIRONMENT_READY variable (0/1)
    ENVIRONMENT_READY=0
    if docker compose -f "$COMPOSE_FILE" ps >/dev/null 2>&1; then
        local running_count
        running_count=$(docker compose -f "$COMPOSE_FILE" ps --services --filter "status=running" | wc -l | tr -d ' ')
        [[ "$running_count" -gt 0 ]] && ENVIRONMENT_READY=1
    fi
    return 0
}

auto_environment_setup() {
    detect_environment_state
    if [[ "$ENVIRONMENT_READY" -eq 1 ]]; then
        log_info "Docker services already running – skipping setup"
        return 0
    fi
    log_info "Starting Docker test environment via docker compose…"
    docker compose -f "$COMPOSE_FILE" up -d

    # Wait for healthy services with exponential back-off (max ~30s)
    local attempt=1
    local max_attempts=6
    local delay=2
    while (( attempt <= max_attempts )); do
        if ensure_environment_ready; then
            log_success "Environment is ready (attempt $attempt)."
            return 0
        fi
        log_info "Waiting for services (attempt $attempt)…"
        sleep $delay
        delay=$(( delay * 2 ))
        (( attempt++ ))
    done

    log_error "Environment failed to become ready after ${max_attempts} attempts."
    exit 1
}

clean_environment() {
    log_warn "Stopping and removing test environment…"
    docker compose -f "$COMPOSE_FILE" down -v || true
    log_success "Environment cleaned."
}

reset_environment() {
    clean_environment
    auto_environment_setup
}

# Verify all key services are running and healthy
ensure_environment_ready() {
    detect_environment_state
    if [[ "$ENVIRONMENT_READY" -eq 0 ]]; then
        return 1
    fi

    # Quick Redis health check (container name assumed redis-test as per compose)
    if ! docker compose -f "$COMPOSE_FILE" exec -T redis-test redis-cli ping 2>/dev/null | grep -q "PONG"; then
        log_warn "Redis did not respond to PING yet."
        return 1
    fi
    return 0
}

# ------------- Legacy Bridging -------------------------------------------- #
# Until all functionality is ported we will call existing run-tests.sh where
# it already handles the desired behaviour. This ensures we don’t break the
# developer workflow mid-migration.
LEGACY_SCRIPT="$PROJECT_ROOT/run-tests.sh"

call_legacy() {
    local legacy_cmd="$1"; shift || true
    if [[ -x "$LEGACY_SCRIPT" ]]; then
        log_info "Delegating to legacy script ($legacy_cmd)…"
        "$LEGACY_SCRIPT" "$legacy_cmd" "$@"
    else
        log_error "Legacy script not found – cannot dispatch '$legacy_cmd'"
        exit 1
    fi
}

# ------------- Command Routing ------------------------------------------- #
print_usage() {
    cat << EOF
${BLUE}Agent Blackwell Unified Test Runner v${SCRIPT_VERSION}${NC}
Usage: $0 <category> [subcommand]

Top-level categories:
  infra        Manage test infrastructure (setup | clean | reset | status)
  redis        Redis integration test suites (basic | load | fault | full)
  agents       Agent-specific tests (spec | design | coding | review | test | all)
  phase3       Full Phase 3 agent integration suite
  phase4       Vector-DB (Phase 4) integration suite
  phase5       Orchestration/API (Phase 5) integration suite
  api          End-to-end API tests via Poetry env
  unit         Run unit tests via Poetry
  all          Run everything
  logs         Tail recent Docker logs
  help         Show this help

Examples:
  $0 infra setup
  $0 redis basic
  $0 agents spec
  $0 phase5
  $0 all
EOF
}

handle_infra() {
    local sub=${1:-status}
    case "$sub" in
        setup)  check_prerequisites; auto_environment_setup ;;
        clean)  check_prerequisites; clean_environment       ;;
        reset)  check_prerequisites; reset_environment       ;;
        status) check_prerequisites; docker compose -f "$COMPOSE_FILE" ps ;;
        *)      log_error "Unknown infra subcommand '$sub'"; exit 1         ;;
    esac
}

# ------------ Agent Test Helpers ------------------------------------------- #
run_agents_all() {
    auto_environment_setup
    log_info "Running all agent integration tests…"
    docker compose -f "$COMPOSE_FILE" run --rm test-runner pytest tests/integration/agents/ -v
}

run_agent_spec() {
    auto_environment_setup
    log_info "Running SpecAgent tests…"
    docker compose -f "$COMPOSE_FILE" run --rm test-runner pytest tests/integration/agents/test_spec_agent.py -v
}

run_agent_design() {
    auto_environment_setup
    log_info "Running DesignAgent tests…"
    docker compose -f "$COMPOSE_FILE" run --rm test-runner pytest tests/integration/agents/test_design_agent.py -v
}

run_agent_coding() {
    auto_environment_setup
    log_info "Running CodingAgent tests…"
    docker compose -f "$COMPOSE_FILE" run --rm test-runner pytest tests/integration/agents/test_coding_agent.py -v
}

run_agent_review() {
    auto_environment_setup
    log_info "Running ReviewAgent tests…"
    docker compose -f "$COMPOSE_FILE" run --rm test-runner pytest tests/integration/agents/test_review_agent.py -v
}

run_agent_test() {
    auto_environment_setup
    log_info "Running TestAgent tests…"
    docker compose -f "$COMPOSE_FILE" run --rm test-runner pytest tests/integration/agents/test_test_agent.py -v
}

# ------------ Redis Test Helpers ------------------------------------------- #
run_redis_full() {
    auto_environment_setup
    log_info "Running full Redis integration suite…"
    docker compose -f "$COMPOSE_FILE" run --rm test-runner pytest tests/integration/redis_tests/ -v
}

run_redis_basic() {
    auto_environment_setup
    log_info "Running basic Redis tests…"
    docker compose -f "$COMPOSE_FILE" run --rm test-runner pytest tests/integration/redis_tests/test_basic_redis.py -v
}

run_redis_load() {
    auto_environment_setup
    log_info "Running load/concurrency Redis tests…"
    docker compose -f "$COMPOSE_FILE" run --rm test-runner pytest tests/integration/redis_tests/test_concurrency_load.py -v
}

run_redis_fault() {
    auto_environment_setup
    log_info "Running Redis fault-tolerance tests…"
    docker compose -f "$COMPOSE_FILE" run --rm test-runner pytest tests/integration/redis_tests/test_fault_tolerance.py -v
}

handle_redis() {
    local sub=${1:-full}
    case "$sub" in
        basic)  run_redis_basic ;;
        load)   run_redis_load  ;;
        fault)  run_redis_fault ;;
        full|all) run_redis_full ;;
        *)      log_error "Unknown redis subcommand '$sub'"; exit 1 ;;
    esac
}

handle_agents() {
    local sub=${1:-all}
    case "$sub" in
        spec)   run_agent_spec    ;;
        design) run_agent_design  ;;
        coding) run_agent_coding  ;;
        review) run_agent_review  ;;
        test)   run_agent_test    ;;
        all)    run_agents_all    ;;
        *)      log_error "Unknown agents subcommand '$sub'"; exit 1 ;;
    esac
}

# ------------ Unit Tests ------------------------------------------------ #
run_unit_tests() {
    log_info "Running tests from root tests/ directory via Poetry..."
    if ! command -v poetry >/dev/null 2>&1; then
        log_error "Poetry not installed – install it or adjust your PATH."
        exit 1
    fi

    # Ensure virtualenv and deps
    poetry install --no-interaction --with dev >/dev/null

    # Run tests in the root tests/ directory
    log_info "Executing tests in root tests/ directory..."
    if poetry run python -m pytest tests/ -k "not integration and not api"; then
        log_success "Root directory tests completed successfully."
        return 0
    else
        log_error "Root directory tests failed. Check output for details."
        return 1
    fi
}

run_e2e_http_tests() {
    log_info "Running E2E HTTP tests via Poetry…"
    if ! command -v poetry >/dev/null 2>&1; then
        log_error "Poetry not installed – install it or adjust your PATH."
        exit 1
    fi
    # Ensure virtualenv and deps
    poetry install --no-interaction --with dev >/dev/null

    # Start the API server in the background
    log_info "Starting API server for E2E tests..."
    poetry run uvicorn src.api.main:app --host 0.0.0.0 --port 8000 &
    API_PID=$!

    # Give the API server time to start up
    log_info "Waiting for API server to start (5s)..."
    sleep 5

    # Run the E2E tests
    log_info "Running E2E tests..."
    poetry run python tests/scripts/e2e_test_gauntlet.py
    E2E_EXIT_CODE=$?

    # Shutdown the API server
    log_info "Shutting down API server..."
    kill $API_PID
    wait $API_PID 2>/dev/null || true

    # Return the exit code from the E2E tests
    return $E2E_EXIT_CODE
}

# ------------ Phase 3 Integration Suite ---------------------------------- #
ensure_agent_worker_running() {
    # Ensure agent-worker service is running; start if necessary
    if docker compose -f "$COMPOSE_FILE" ps --services --filter "status=running" | grep -q "^agent-worker$"; then
        log_info "agent-worker service already running."
    else
        log_info "Starting agent-worker service…"
        docker compose -f "$COMPOSE_FILE" up -d agent-worker
        # Give the container a few seconds to initialise
        sleep 5
    fi
}

run_phase3_suite() {
    log_info "Starting Phase 3 agent integration test suite…"
    auto_environment_setup
    ensure_agent_worker_running

    if run_agents_all; then
        log_success "Phase 3 agent integration suite completed successfully."
    else
        log_error "Phase 3 agent integration suite failed. Check logs for details."
        exit 1
    fi
}

# ------------ Phase 4 Integration Suite ---------------------------------- #
run_vector_db_all() {
    auto_environment_setup
    log_info "Running vector DB integration tests…"
    docker compose -f "$COMPOSE_FILE" run --rm test-runner pytest tests/integration/vector_db/ -v
}

run_phase4_suite() {
    log_info "Starting Phase 4 vector DB integration test suite…"
    if run_vector_db_all; then
        log_success "Phase 4 vector DB integration suite completed successfully."
    else
        log_error "Phase 4 vector DB integration suite failed. Check logs for details."
        exit 1
    fi
}

# ------------ Phase 5 Integration Suite ---------------------------------- #
run_phase5_suite() {
    log_info "Starting Phase 5 orchestration & API integration test suite…"
    auto_environment_setup

    # Optionally ensure agent-worker is up (already handled for phase3), app-test container will start with compose.

    local TEST_PATHS=(
        tests/integration/system
    )

    if docker compose -f "$COMPOSE_FILE" run --rm test-runner pytest --import-mode=importlib "${TEST_PATHS[@]}" -v; then
        log_success "Phase 5 orchestration & API integration suite completed successfully."
    else
        log_error "Phase 5 orchestration & API integration suite failed. Check logs for details."
        exit 1
    fi
}

# ------------- Main Dispatcher ------------------------------------------- #
main() {
    setup_comprehensive_logging

    local category=${1:-help}; shift || true
    case "$category" in
        infra)   handle_infra "$@"   ;;
        redis)   handle_redis "$@"   ;;
        agents)  handle_agents "$@"  ;;
        phase3)  run_phase3_suite ;;
        phase4)  run_phase4_suite ;;
        phase5)  run_phase5_suite           ;;
        api)     run_e2e_http_tests   ;;
        unit)    run_unit_tests       ;;
        all)
            log_info "Running all test suites..."
            run_unit_tests || true
            run_phase3_suite || true
            run_phase4_suite || true
            run_phase5_suite || true
            run_e2e_http_tests || true
            log_success "All test suites completed!"
            ;;

        logs)    docker compose -f "$COMPOSE_FILE" logs --tail=100 -f ;;
        help|--help|-h) print_usage  ;;
        *)       log_error "Unknown category '$category'"; print_usage; exit 1 ;;
    esac
}

main "$@"
