# MVP Incremental Workflow Phase Tests

This directory contains validation and integration tests for each phase of the MVP incremental workflow development.

## Test Organization

### Phase Tests
- `test_phase2_summary.py` - Phase 2: Validation integration tests
- `test_phase3_validation.py` - Phase 3: Feature dependency and ordering tests
- `test_phase4_retry_trigger.py` - Phase 4: Retry trigger scenario tests
- `test_phase4_validation.py` - Phase 4: Retry logic validation tests
- `test_phase5_validation.py` - Phase 5: Error analyzer validation tests
- `test_phase6_simple.py` - Phase 6: Simple progress monitoring tests
- `test_phase6_validation.py` - Phase 6: Progress monitoring validation tests
- `test_phase7_simple.py` - Phase 7: Feature reviewer agent simple tests
- `test_phase7_validation.py` - Phase 7: Feature reviewer validation tests

### Integration Tests
- `test_incremental_integration.py` - Full incremental workflow integration tests

## Running Tests

### Run all incremental tests:
```bash
pytest tests/integration/incremental/ -v
```

### Run specific phase tests:
```bash
# Phase 2 tests
python tests/integration/incremental/test_phase2_summary.py

# Phase 3 tests  
python tests/integration/incremental/test_phase3_validation.py

# Phase 4 tests
python tests/integration/incremental/test_phase4_validation.py
python tests/integration/incremental/test_phase4_retry_trigger.py

# Phase 5 tests
python tests/integration/incremental/test_phase5_validation.py

# Phase 6 tests
python tests/integration/incremental/test_phase6_simple.py
python tests/integration/incremental/test_phase6_validation.py

# Phase 7 tests
python tests/integration/incremental/test_phase7_simple.py
python tests/integration/incremental/test_phase7_validation.py
```

### Using the test runner:
```bash
# Run all integration tests (includes incremental)
./test_runner.py integration

# Run specific test category
./test_runner.py unit integration
```

## Test Requirements

Most phase tests require:
1. The orchestrator server to be running (`python orchestrator/orchestrator_agent.py`)
2. Virtual environment activated with all dependencies
3. Docker running (for validation tests)

## Phase Overview

- **Phase 1**: Basic feature breakdown (initial implementation)
- **Phase 2**: Validation after each feature
- **Phase 3**: Feature dependency ordering
- **Phase 4**: Retry logic for failed features
- **Phase 5**: Error analysis and recovery
- **Phase 6**: Progress monitoring
- **Phase 7**: Feature reviewer agent
- **Phase 8**: Review integration (upcoming)