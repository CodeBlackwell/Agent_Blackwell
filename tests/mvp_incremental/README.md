# MVP Incremental Workflow Tests

This directory contains all tests specific to the MVP incremental workflow implementation.

## Test Files

### Core Workflow Tests
- `test_mvp_incremental.py` - Main MVP incremental workflow test
- `test_incremental_workflow.py` - Incremental workflow integration test
- `test_incremental_workflow_basic.py` - Basic workflow functionality test
- `test_incremental_simple.py` - Simple incremental test cases

### Phase-Specific Tests
- `test_mvp_incremental_phase2.py` - Phase 2: Validation integration
- `test_mvp_incremental_phase3.py` - Phase 3: Feature dependencies and ordering
- `test_mvp_incremental_phase4.py` - Phase 4: Retry logic
- `test_mvp_incremental_phase5.py` - Phase 5: Error analysis
- `test_mvp_incremental_phase6.py` - Phase 6: Progress monitoring

### Phase 7 & 8 Tests (Review Integration)
- `test_phase8_final.py` - Final validation of Phase 8 implementation
- `test_phase8_simple.py` - Simple Phase 8 integration test
- `test_phase8_trace.py` - Trace test for review integration
- `test_review_component.py` - Review component unit test
- `test_workflow_reviews.py` - Workflow review integration test

### Integration Tests (Phase Validation)
- `test_phase2_summary.py` - Phase 2 validation summary
- `test_phase3_validation.py` - Phase 3 dependency validation
- `test_phase4_validation.py` - Phase 4 retry validation
- `test_phase4_retry_trigger.py` - Retry trigger testing
- `test_phase5_validation.py` - Phase 5 error analysis validation
- `test_phase6_simple.py` - Simple progress monitoring test
- `test_phase6_validation.py` - Phase 6 progress validation
- `test_phase7_simple.py` - Simple reviewer test
- `test_phase7_validation.py` - Phase 7 reviewer validation
- `test_phase8_validation.py` - Phase 8 review integration validation
- `test_phase8_review_integration.py` - Review integration module test

### Unit Tests (Component Level)
- `test_error_analyzer.py` - Error analyzer component
- `test_feature_orchestrator.py` - Feature orchestration logic
- `test_feature_parser.py` - Feature parsing utilities
- `test_incremental_executor.py` - Incremental execution engine
- `test_progress_monitor.py` - Progress monitoring component
- `test_retry_strategies.py` - Retry strategy patterns
- `test_stagnation_detector.py` - Stagnation detection logic
- `test_validation_system.py` - Validation system components

## Running the Tests

### Run All MVP Tests
```bash
# Using the test runner
./test_runner.py mvp

# Or run individual tests
python tests/mvp_incremental/test_mvp_incremental.py
```

### Run Specific Phase Tests
```bash
# Test a specific phase
python tests/mvp_incremental/test_mvp_incremental_phase2.py

# Test review integration
python tests/mvp_incremental/test_review_component.py
```

## Test Organization

Tests in this directory focus on the MVP incremental workflow's unique features:
- Feature-by-feature implementation
- Validation after each feature
- Feature dependency management
- Retry strategies for failed features
- Error analysis and recovery
- Progress monitoring
- Review integration throughout the workflow

This directory now contains ALL tests related to the MVP incremental workflow, including:
- Unit tests for individual components (error analyzer, feature parser, etc.)
- Integration tests for phase validation
- Workflow-level tests
- Review integration tests