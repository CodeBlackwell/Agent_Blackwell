# TDD Workflow

## Overview

The Test-Driven Development (TDD) workflow implements a rigorous development approach where tests are written before the implementation code. Following the completion of Operation Red Yellow, this workflow now enforces mandatory RED-YELLOW-GREEN phases, ensuring high code quality, comprehensive test coverage, and reliable software delivery through strict phase progression.

## RED-YELLOW-GREEN Phase System

The TDD workflow now enforces a strict phase progression system with visual indicators:

### 🔴 RED Phase - Test First
**Purpose**: Write failing tests that define the expected behavior
- Tests are written before any implementation
- All tests must fail initially
- Clear specifications of expected functionality
- Automatic validation that tests can detect failures

### 🟡 YELLOW Phase - Implementation
**Purpose**: Write code to make tests pass
- Implementation guided by failing tests
- Minimal code to achieve test success
- Pre-review state for quality checks
- Retry opportunities with test-specific hints

### 🟢 GREEN Phase - Success
**Purpose**: All tests pass and code is approved
- Full test suite passes
- Code review approved
- Refactoring completed
- Feature ready for integration

## Workflow Phases

### 1. Planning Phase
- Analyze requirements and break down into testable components
- Define acceptance criteria
- Create high-level architecture design
- Identify test scenarios
- **TDD Integration**: Each component starts in RED phase

### 2. Design Phase
- Create detailed technical design
- Define API contracts and interfaces
- Design data models and schemas
- Plan integration points
- **TDD Integration**: Design guides test specifications

### 3. Test Writing Phase (🔴 RED)
- Write unit tests for each component
- Create integration tests for workflows
- Tests must fail initially (RED phase enforcement)
- Establish test coverage targets
- **Phase Transition**: Automatically moves to YELLOW after implementation

### 4. Implementation Phase (🟡 YELLOW)
- Implement code to pass the tests
- Use test failure hints for guidance
- Write minimal code to make tests pass
- Track retry attempts and improvements
- **Phase Transition**: Moves to GREEN when tests pass and review approves

### 5. Execution Phase
- Run all tests to verify implementation
- Check test coverage metrics (85%+ target)
- Validate against acceptance criteria
- Performance optimized with test caching
- **Real-time Progress**: Visual phase tracking during execution

### 6. Review Phase (🟢 GREEN)
- Code review by the reviewer agent
- Verify adherence to TDD principles
- Check code quality and standards
- Approve for GREEN phase or request revisions
- **Celebration**: Success metrics and completion report

## Configuration

```python
TDD_WORKFLOW_CONFIG = {
    "max_retries": 3,
    "test_coverage_threshold": 85,  # Increased from 80%
    "enable_integration_tests": True,
    "execution_timeout": 60,
    "auto_approve_after_retries": True,
    # New TDD-specific settings
    "enforce_red_phase": True,
    "enable_test_caching": True,
    "parallel_test_execution": True,
    "phase_tracking": True,
    "retry_with_hints": True
}
```

### Phase-Specific Configuration

```python
PHASE_CONFIG = {
    "red": {
        "enforce_failing_tests": True,
        "min_test_count": 1,
        "timeout": 300  # 5 minutes
    },
    "yellow": {
        "max_retry_attempts": 3,
        "enable_hints": True,
        "review_required": True
    },
    "green": {
        "min_coverage": 85,
        "celebration_mode": True,
        "generate_report": True
    }
}
```

## Usage Example

```bash
# Using the run.py script
python run.py workflow tdd --task "Create a REST API for user management"

# Using the API
curl -X POST http://localhost:8000/execute-workflow \
  -H "Content-Type: application/json" \
  -d '{
    "requirements": "Create a REST API for user management with CRUD operations",
    "workflow_type": "tdd"
  }'
```

### Real-Time Phase Tracking

When running TDD workflows, you'll see real-time phase progression:

```
================================================================================
Feature: User Authentication
================================================================================
🔴 RED Phase [14:23:15] - Writing failing tests...
  ✓ Test: test_user_login_with_valid_credentials (FAILING as expected)
  ✓ Test: test_user_login_with_invalid_credentials (FAILING as expected)
  
🟡 YELLOW Phase [14:25:42] - Implementing solution...
  → Attempt 1: 2 tests failing
  → Attempt 2: 1 test failing (progress!)
  → Attempt 3: All tests passing!
  
🟢 GREEN Phase [14:28:19] - Success!
  ✓ All tests passing (100% coverage)
  ✓ Code review approved
  ✓ Feature complete in 5m 4s
================================================================================
```

## Best Practices

### RED Phase Best Practices
1. **Write Failing Tests First**: Never skip the RED phase
2. **Clear Test Names**: Use descriptive names that explain what's being tested
3. **Test One Thing**: Each test should verify a single behavior
4. **Expect Failures**: Tests must fail initially to prove they work

### YELLOW Phase Best Practices
1. **Minimal Implementation**: Write just enough code to pass tests
2. **Use Test Hints**: Leverage retry hints for faster fixes
3. **Track Progress**: Monitor which tests pass with each attempt
4. **Don't Skip Steps**: Resist urge to implement beyond test requirements

### GREEN Phase Best Practices
1. **Refactor with Confidence**: Tests protect against regressions
2. **Celebrate Success**: Review metrics and learn from the process
3. **Document Patterns**: Share successful approaches with team
4. **Maintain Coverage**: Keep test coverage above 85%

### General TDD Best Practices
1. **Fast Feedback**: Keep tests fast for rapid development cycles
2. **Test Independence**: Each test should run independently
3. **Use Test Cache**: Enable caching for faster iterations
4. **Parallel Execution**: Run tests in parallel when possible

## Error Handling

The TDD workflow includes enhanced error handling with phase-specific strategies:

### RED Phase Error Handling
- Validation that tests actually fail
- Clear error messages if tests pass unexpectedly
- Timeout protection for test writing

### YELLOW Phase Error Handling
- Test-specific retry hints based on failure patterns
- Progressive retry strategies that evolve with attempts
- Context preservation between retries
- Automatic rollback to RED if unrecoverable

### GREEN Phase Error Handling
- Final validation of all tests
- Coverage verification
- Review approval requirements
- Comprehensive error reporting

### General Error Handling
- Automatic retry on test failures (up to 3 attempts)
- Detailed error messages with stack traces
- Fallback to manual review after max retries
- Execution timeout protection (configurable per phase)
- Test result caching to avoid re-running passed tests

## Integration with Other Workflows

The TDD workflow can be combined with:
- **MVP Incremental Workflow**: For feature-by-feature TDD development
- **Full Workflow**: As a quality assurance layer
- **Individual Steps**: For targeted TDD on specific components

## Monitoring and Metrics

Track TDD workflow performance with enhanced metrics:

### Phase Metrics
- **RED Phase Duration**: Time to write failing tests
- **YELLOW Phase Duration**: Time to implement solution
- **GREEN Phase Duration**: Time to review and approve
- **Total Feature Time**: End-to-end completion time

### Test Metrics
- **Test Execution Time**: With cache hit rates
- **Test Coverage**: Target 85%+
- **Test Pass Rate**: Per attempt tracking
- **Retry Effectiveness**: Success rate by retry attempt

### Performance Metrics
- **Cache Hit Rate**: Typically 85%+ after warmup
- **Parallel Speedup**: 2.8x average improvement
- **Memory Usage**: 70% reduction from baseline
- **Code-to-Test Ratio**: Ideal 1:1.5

### Quality Metrics
- **Defect Detection Rate**: Bugs caught in testing
- **Review Approval Rate**: First-time vs retry approvals
- **Feature Success Rate**: Completed without manual intervention

## Troubleshooting

Common issues and solutions:

### Phase-Specific Issues

1. **Stuck in RED Phase**
   - **Issue**: Tests won't fail initially
   - **Solution**: Verify test logic is correct and implementation doesn't exist
   - **Check**: Ensure `expect_failure=True` is set for initial test runs

2. **YELLOW Phase Loops**
   - **Issue**: Can't get all tests to pass
   - **Solution**: Review test hints and failure patterns
   - **Check**: Enable verbose logging to see detailed failure reasons

3. **Can't Reach GREEN Phase**
   - **Issue**: Review keeps rejecting code
   - **Solution**: Address all review feedback points
   - **Check**: Verify test coverage meets 85% threshold

### Performance Issues

1. **Slow Test Execution**
   - Enable test caching: `enable_test_caching: true`
   - Use parallel execution: `parallel_test_execution: true`
   - Check for expensive test setup/teardown

2. **High Memory Usage**
   - Enable code storage spillover
   - Limit parallel execution threads
   - Clear test cache periodically

3. **Cache Misses**
   - Verify cache configuration
   - Check test determinism
   - Monitor cache statistics

### General Issues

1. **Tests Timing Out**
   - Increase phase-specific timeouts
   - Check for infinite loops in tests
   - Verify external dependencies

2. **Low Test Coverage**
   - Review untested code paths
   - Add edge case tests
   - Use coverage reports for guidance

3. **Flaky Tests**
   - Eliminate timing dependencies
   - Mock external services
   - Ensure test data consistency
   - Use test isolation

## Related Documentation

- [Operation Red Yellow](../operations/operation-red-yellow.md) - Complete TDD transformation details
- [TDD Architecture Guide](../developer-guide/architecture/tdd-architecture.md) - Technical implementation
- [Workflows Overview](README.md) - All available workflows
- [Testing Guide](../developer-guide/testing-guide.md) - Comprehensive testing documentation
- [MVP Incremental Workflow](mvp-incremental/README.md) - Feature-by-feature development
- [Performance Optimization](../operations/performance-optimizations.md) - Speed improvements
- [Configuration Reference](../reference/configuration.md) - All configuration options