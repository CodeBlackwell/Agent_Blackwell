# TDD Workflow Quick Reference

## 🚀 Quick Start

```bash
# Run TDD workflow
python run.py workflow tdd --task "Your requirement here"

# Run with API
curl -X POST http://localhost:8000/execute-workflow \
  -H "Content-Type: application/json" \
  -d '{"requirements": "Your requirement", "workflow_type": "tdd"}'
```

## 🔴🟡🟢 Phase System

### 🔴 RED Phase - Write Failing Tests
- **Purpose**: Define expected behavior
- **Duration**: 2-5 minutes typically
- **Key Actions**:
  - Write tests before implementation
  - Ensure tests fail initially
  - Define clear specifications
- **Transition**: Automatic to YELLOW after tests written

### 🟡 YELLOW Phase - Implementation
- **Purpose**: Make tests pass
- **Duration**: 5-10 minutes typically
- **Key Actions**:
  - Write minimal code to pass tests
  - Use test failure hints
  - Retry with improvements
- **Transition**: To GREEN when all tests pass

### 🟢 GREEN Phase - Success & Review
- **Purpose**: Validate and celebrate
- **Duration**: 1-2 minutes typically
- **Key Actions**:
  - Final test validation
  - Code review
  - Coverage check (85%+ required)
  - Generate completion report
- **Transition**: Feature complete!

## ⚙️ Key Configuration

```python
# Enable/Disable features
TDD_CONFIG = {
    "enforce_red_phase": True,      # Can't skip test writing
    "enable_test_caching": True,    # 85%+ hit rate
    "parallel_test_execution": True, # 2.8x speedup
    "retry_with_hints": True,       # Smart retry prompts
    "test_coverage_threshold": 85   # Minimum coverage
}
```

## 📊 Performance Tips

1. **Enable Caching**: `enable_test_caching: true`
2. **Use Parallel Execution**: `parallel_test_execution: true`
3. **Monitor Cache Hit Rate**: Should be 85%+
4. **Check Memory Usage**: Spillover at 100MB

## 🔧 Common Commands

```bash
# View real-time progress
python run.py workflow tdd --task "..." --verbose

# Run specific complexity
python run.py workflow tdd --task "..." --complexity simple

# Dry run (preview only)
python run.py workflow tdd --task "..." --dry-run

# Save artifacts
python run.py workflow tdd --task "..." --save-output
```

## 🚨 Troubleshooting

### Stuck in RED Phase?
- Verify test logic is correct
- Check implementation doesn't already exist
- Ensure `expect_failure=True` is set

### YELLOW Phase Loops?
- Review test failure hints
- Enable verbose logging
- Check retry count (max 3)

### Can't Reach GREEN?
- Verify test coverage ≥ 85%
- Address all review feedback
- Check for flaky tests

## 📈 Metrics to Monitor

- **Phase Duration**: RED (2-5m), YELLOW (5-10m), GREEN (1-2m)
- **Cache Hit Rate**: Target 85%+
- **Test Coverage**: Minimum 85%
- **Retry Success**: Should improve each attempt
- **Memory Usage**: Should stay under 600MB

## 🎯 Best Practices

1. **Write Clear Test Names**: `test_user_login_with_valid_credentials`
2. **One Behavior Per Test**: Keep tests focused
3. **Use Test Hints**: They guide better implementations
4. **Trust the Process**: Let RED→YELLOW→GREEN guide you

## 🔗 Related Resources

- [Full TDD Workflow Guide](tdd-workflow.md)
- [Operation Red Yellow Details](../operations/operation-red-yellow.md)
- [Performance Optimization](../operations/performance-optimizations.md)
- [Testing Guide](../developer-guide/testing-guide.md)

---

**Remember**: You cannot bypass the TDD phases. Embrace the RED→YELLOW→GREEN cycle for better code quality!