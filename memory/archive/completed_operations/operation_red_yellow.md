# Operation Red Yellow: Complete TDD Transformation of MVP Incremental Workflow

## Mission Statement
Fully evolve the MVP Incremental Workflow into a pure Test-Driven Development (TDD) system where RED-YELLOW-GREEN phases are mandatory for every feature. This is not an optional mode - TDD becomes the only way the workflow operates.

## Overview
This operation permanently transforms the workflow into a strict three-phase TDD cycle:
- **RED**: Tests written and confirmed to fail (no implementation exists)
- **YELLOW**: Tests pass but code awaits review
- **GREEN**: Tests pass AND code is reviewed/approved

**Important**: This is a complete evolution, not a feature addition. The workflow will ONLY operate in TDD mode.

---

## Phase 1: Foundation Components

### Phase 1a: TDD Phase Tracker Implementation
**Objective**: Create the core tracking system for RED-YELLOW-GREEN states

**Implementation**:
1. Create `workflows/mvp_incremental/tdd_phase_tracker.py`
   - Define TDDPhase enum (RED, YELLOW, GREEN)
   - Create TDDPhaseTracker class
   - Track phase transitions per feature
   - Implement phase validation rules
   - Add visual indicators for console output

**Dependencies**: None (foundational component)

### Phase 1b: TDD Phase Tracker Testing
**Objective**: Ensure phase tracker works correctly

**Testing**:
1. Create `tests/mvp_incremental/test_tdd_phase_tracker.py`
   - Test phase transitions
   - Test invalid transition prevention
   - Test phase history tracking
   - Test visual output generation

---

## Phase 2: Test Execution Enhancement

### Phase 2a: Enhanced Test Execution Implementation
**Objective**: Modify test execution to support TDD workflow

**Implementation**:
1. Update `workflows/mvp_incremental/test_execution.py`
   - Add `expect_failure` parameter
   - Implement RED phase test execution (must fail)
   - Enhanced test output parsing
   - Test result caching mechanism
   - Detailed failure context extraction

**Dependencies**: Phase 1a (needs phase tracker)

### Phase 2b: Test Execution Testing
**Objective**: Validate enhanced test execution

**Testing**:
1. Create `tests/mvp_incremental/test_enhanced_execution.py`
   - Test expect_failure mode
   - Test output parsing accuracy
   - Test caching functionality
   - Test failure context extraction

---

## Phase 3: Test Writer Integration ✅ COMPLETED

### Phase 3a: Test Writer Integration Implementation ✅
**Objective**: Integrate test writer agent into workflow

**Implementation COMPLETED**:
1. Updated `workflows/mvp_incremental/testable_feature_parser.py`
   - Added TDDPhase import and integration
   - Updated TestableFeature with TDD phase tracking
   - Added phase validation methods (can_start_implementation, etc.)

2. Updated `workflows/mvp_incremental/tdd_feature_implementer.py`
   - Added RED phase enforcement before implementation
   - Integrated phase transitions with test/review workflow
   - Test writer already integrated in workflow

**Dependencies**: Phase 1a ✅, Phase 2a ✅

### Phase 3b: Test Writer Integration Testing ✅
**Objective**: Ensure test generation works correctly

**Testing COMPLETED**:
1. Created `tests/mvp_incremental/test_tdd_phase_integration.py`
   - 11 comprehensive integration tests
   - Tests full TDD workflow integration
   - Validates phase transitions

2. Created `tests/mvp_incremental/test_phase3_components.py`
   - 8 focused component tests
   - Tests specific Phase 3 updates
   - Validates component interactions

**Summary**: Phase 3 successfully integrated TDD phase tracking into all workflow components. The test writer, feature parser, implementer, reviewer, and verifier now all participate in enforcing RED→YELLOW→GREEN progression.

---

## Phase 4: RED Phase Implementation ✅ COMPLETED

### Phase 4a: RED Phase Logic Implementation ✅
**Objective**: Implement the RED phase where tests must fail first

**Implementation COMPLETED**:
1. Created `workflows/mvp_incremental/red_phase.py`
   - RedPhaseOrchestrator class for RED phase orchestration
   - Test execution with failure expectation
   - Comprehensive failure context extraction
   - TestFailureContext dataclass for structured failure data
   - Implementation hints generation based on failure types

2. Updated workflow to enforce RED phase
   - Integrated RedPhaseOrchestrator into TDDFeatureImplementer
   - Enhanced coder context with RED phase failure analysis
   - Proper deduplication of error messages
   - Support for various failure types (import, assertion, attribute, name errors)

**Dependencies**: Phase 2a ✅, Phase 3a ✅

### Phase 4b: RED Phase Testing ✅
**Objective**: Validate RED phase enforcement

**Testing COMPLETED**:
1. Created `tests/mvp_incremental/test_red_phase.py`
   - 14 comprehensive test cases
   - Test failure enforcement
   - Test blocking of unexpected passes
   - Test failure context extraction for all error types
   - Test implementation context preparation
   - All tests passing

**Summary**: Phase 4 successfully implements dedicated RED phase orchestration with robust failure analysis and context extraction. The RED phase is now strictly enforced before any implementation can begin.

---

## Phase 5: YELLOW Phase Implementation

### Phase 5a: YELLOW Phase Logic Implementation
**Objective**: Implement YELLOW phase for passing tests awaiting review

**Implementation**:
1. Create `workflows/mvp_incremental/yellow_phase.py`
   - YELLOW phase detection (tests pass)
   - Pre-review state management
   - Visual indicators for YELLOW state
   - Transition logic to GREEN

**Dependencies**: Phase 4a

### Phase 5b: YELLOW Phase Testing
**Objective**: Validate YELLOW phase behavior

**Testing**:
1. Create `tests/mvp_incremental/test_yellow_phase.py`
   - Test pass detection
   - Test state transitions
   - Test review integration

---

## Phase 6: GREEN Phase Implementation

### Phase 6a: GREEN Phase Logic Implementation
**Objective**: Implement GREEN phase for reviewed and approved code

**Implementation**:
1. Create `workflows/mvp_incremental/green_phase.py`
   - GREEN phase validation
   - Review approval integration
   - Final state confirmation
   - Success metrics tracking

**Dependencies**: Phase 5a

### Phase 6b: GREEN Phase Testing
**Objective**: Validate GREEN phase completion

**Testing**:
1. Create `tests/mvp_incremental/test_green_phase.py`
   - Test review integration
   - Test final state validation
   - Test metrics collection

---

## Phase 7: TDD-Driven Retry Strategy

### Phase 7a: TDD Retry Strategy Implementation
**Objective**: Update retry logic to be test-driven

**Implementation**:
1. Update `workflows/mvp_incremental/retry_strategy.py`
   - Include test failure details in retry prompts
   - Generate test-specific fix hints
   - Track failing vs passing tests
   - Focus retry on making specific tests pass

**Dependencies**: Phase 4a, Phase 5a

### Phase 7b: TDD Retry Strategy Testing
**Objective**: Validate test-driven retry behavior

**Testing**:
1. Update `tests/mvp_incremental/test_retry_strategy.py`
   - Test failure inclusion in prompts
   - Test fix hint generation
   - Test retry effectiveness

---

## Phase 8: Progress Monitor Enhancement

### Phase 8a: TDD Progress Monitor Implementation
**Objective**: Update progress tracking for TDD phases

**Implementation**:
1. Update `workflows/mvp_incremental/progress_monitor.py`
   - Add TDD phase visualization
   - Track test metrics (failures, passes, coverage)
   - Show RED→YELLOW→GREEN progression
   - Add phase timing metrics

**Dependencies**: Phase 1a, Phase 6a

### Phase 8b: Progress Monitor Testing
**Objective**: Validate enhanced progress tracking

**Testing**:
1. Update `tests/mvp_incremental/test_progress_monitor.py`
   - Test TDD visualization
   - Test metrics tracking
   - Test phase progression display

---

## Phase 9: Main Workflow Integration

### Phase 9a: Workflow Orchestration Implementation
**Objective**: Integrate all TDD components into main workflow as the only mode

**Implementation**:
1. Complete overhaul of `workflows/mvp_incremental/mvp_incremental.py`
   - Replace current flow with mandatory TDD phases
   - Remove all non-TDD code paths
   - Enforce RED→YELLOW→GREEN for every feature
   - No configuration options - TDD is the only way

**Dependencies**: All previous phases

### Phase 9b: End-to-End Testing
**Objective**: Validate complete TDD workflow

**Testing**:
1. Create `tests/mvp_incremental/test_tdd_workflow_e2e.py`
   - Test complete TDD cycle
   - Test multi-feature TDD flow
   - Test error scenarios
   - Verify non-TDD paths are removed

---

## Phase 10: MCP Integration (Optional Enhancement)

### Phase 10a: MCP Filesystem Enablement
**Objective**: Enable MCP for reduced token usage

**Implementation**:
1. Update configuration to use MCP
   - Set USE_MCP_FILESYSTEM=true by default
   - Update file operations to use MCP
   - Add MCP server startup instructions
   - Create migration guide

**Dependencies**: Phase 9a

### Phase 10b: MCP Integration Testing
**Objective**: Validate MCP integration

**Testing**:
1. Test with MCP enabled
   - Verify file operations
   - Check performance improvements
   - Validate error handling

---

## Phase 11: Comprehensive Live Testing Infrastructure

### Phase 11a: Live Test Infrastructure Implementation
**Objective**: Create real execution test framework without mocks

**Implementation**:
1. Create `tests/live/test_runner.py`
   - Unified test runner for all live tests
   - Support for parallel execution
   - Real-time progress monitoring
   - Comprehensive result reporting
   - Docker container management for isolated execution

2. Create `tests/live/test_fixtures.py`
   - Live agent interaction fixtures
   - Real workflow execution helpers
   - Test data generators for various complexity levels
   - Container lifecycle management
   - Result validation utilities

3. Create `tests/live/test_categories.py`
   - Define test complexity levels (Simple → Complex)
   - Category-based test organization
   - Progressive difficulty scaling
   - Performance benchmarks per category

**Dependencies**: Phase 9a (complete workflow integration)

### Phase 11b: Progressive Test Suite Implementation
**Objective**: Implement test cases from simple to complex

**Implementation**:

1. **Level 1 - Simple Tests** (`tests/live/level1_simple/`)
   - `test_calculator.py`: Basic arithmetic operations
   - `test_hello_world.py`: Simple string manipulation
   - `test_data_structures.py`: Basic list/dict operations
   - Expected runtime: < 30 seconds per test

2. **Level 2 - Moderate Tests** (`tests/live/level2_moderate/`)
   - `test_rest_api.py`: FastAPI CRUD operations
   - `test_file_processor.py`: CSV/JSON processing
   - `test_algorithm_implementation.py`: Sorting, searching
   - Expected runtime: 1-2 minutes per test

3. **Level 3 - Complex Tests** (`tests/live/level3_complex/`)
   - `test_web_app.py`: Full stack with database
   - `test_microservice.py`: Multi-container setup
   - `test_data_pipeline.py`: ETL workflow
   - Expected runtime: 3-5 minutes per test

4. **Level 4 - Advanced Tests** (`tests/live/level4_advanced/`)
   - `test_concurrent_workflows.py`: Parallel execution
   - `test_performance_limits.py`: Stress testing
   - `test_large_codebase.py`: 1000+ line projects
   - Expected runtime: 5-10 minutes per test

5. **Level 5 - Edge Cases** (`tests/live/level5_edge_cases/`)
   - `test_error_recovery.py`: Failure scenarios
   - `test_timeout_handling.py`: Long-running tasks
   - `test_invalid_inputs.py`: Malformed requests
   - `test_resource_limits.py`: Memory/CPU constraints

**Testing Approach**:
- Each test includes:
  - Input specification (requirements)
  - Expected output validation
  - Performance metrics collection
  - Error scenario handling
  - Resource usage monitoring

**Success Metrics**:
- All tests must execute without mocks
- Real Docker containers for code execution
- Actual file system operations
- Live agent interactions
- Measurable performance baselines

**Dependencies**: Phase 11a

---

## Phase 12: Documentation and Demo

### Phase 12a: Documentation Creation
**Objective**: Create comprehensive documentation

**Implementation**:
1. Create `docs/workflows/mvp-incremental/tdd-guide.md`
2. Update existing MVP incremental documentation
3. Create configuration examples
4. Write migration guide from current workflow
5. Add live testing guide and best practices

### Phase 12b: Demo Script Creation
**Objective**: Create demonstration of TDD workflow

**Implementation**:
1. Create `demos/advanced/mvp_incremental_tdd_demo.py`
   - Visual RED→YELLOW→GREEN progression
   - Clear test-first demonstration
   - Multiple feature example
   - Error recovery demonstration
   - Live test execution examples

---

## Implementation Order Summary

1. **Foundation**: Phase 1a → 1b
2. **Test Execution**: Phase 2a → 2b
3. **Test Generation**: Phase 3a → 3b
4. **TDD Phases**: Phase 4a → 4b → 5a → 5b → 6a → 6b
5. **Enhancements**: Phase 7a → 7b → 8a → 8b
6. **Integration**: Phase 9a → 9b
7. **Optional**: Phase 10a → 10b
8. **Live Testing**: Phase 11a → 11b
9. **Documentation**: Phase 12a → 12b

## Success Criteria

1. Tests are written before any implementation code - MANDATORY
2. Tests must fail initially (RED phase enforced) - NO EXCEPTIONS
3. Implementation guided by test failures - ONLY WAY TO CODE
4. Review required before GREEN phase - ENFORCED
5. Clear visual indication of TDD phases - ALWAYS VISIBLE
6. Comprehensive test coverage for all features - REQUIRED
7. Reduced token usage with MCP integration
8. Complete documentation showing TDD as the only mode

## Risk Mitigation

1. **Migration Path**: Create clear migration guide for existing users
2. **Performance**: Implement test caching to avoid repeated runs
3. **Complexity**: Provide comprehensive documentation and examples
4. **User Adoption**: Create compelling demos showing TDD benefits

## Timeline Estimate

- Phase 1-3: 2 days (Foundation and core components)
- Phase 4-6: 3 days (TDD phase implementation)
- Phase 7-8: 2 days (Enhancements)
- Phase 9: 2 days (Integration)
- Phase 10: 1 day (Optional MCP)
- Phase 11: 3 days (Live Testing Infrastructure)
- Phase 12: 1 day (Documentation)

**Total**: ~13 days for complete implementation

## Notes

- Each implementation phase (a) should be followed immediately by its testing phase (b)
- Dependencies are strictly enforced - later phases require earlier ones
- MCP integration is optional but highly recommended for performance
- Documentation should be updated incrementally during development
- **This is a complete workflow transformation, not an optional feature**
- **The existing non-TDD mode will be completely removed**
- **All future features must follow the RED-YELLOW-GREEN cycle**

## Key Differences from Original Workflow

1. **Test Writer Agent** is now mandatory after design phase
2. **RED phase enforcement** - code cannot be written until tests fail
3. **YELLOW phase** adds a pre-review state for passing tests
4. **No toggle or configuration** - TDD is the only mode
5. **Test execution happens multiple times per feature** (not just at the end)
6. **Retry logic is test-driven** - based on failing test feedback