# Run.py TDD Features Guide

This guide explains how to use the Test-Driven Development (TDD) features in the unified `run.py` script, powered by Operation Red Yellow.

## 🔴🟡🟢 Overview

The `run.py` script now includes comprehensive TDD support with RED-YELLOW-GREEN phase enforcement:

- **🔴 RED Phase**: Write failing tests first
- **🟡 YELLOW Phase**: Implement code to pass tests  
- **🟢 GREEN Phase**: Tests pass and code is approved

## Interactive TDD Mode

### Accessing TDD Mode

1. Run `python run.py` to start interactive mode
2. Select option 3: "🔴🟡🟢 TDD Mode (Operation Red Yellow)"
3. Choose from TDD-specific options

### TDD Menu Options

```
TDD Mode Options:
1. 🔴🟡🟢 Standard TDD Workflow
2. 🚀 Performance-Optimized TDD
3. ⚡ Quick TDD Demo
4. 📊 View Performance Statistics
5. 🔧 Configure TDD Settings
6. 📖 TDD Examples Gallery
```

### Workflow Variants

#### Standard TDD (`tdd`)
- Full RED-YELLOW-GREEN enforcement
- 85% test coverage requirement
- Test caching and parallel execution enabled
- Retry with intelligent hints

#### Performance-Optimized TDD (`tdd_optimized`)
- All standard features plus:
- Memory spillover for large projects
- Streaming responses for real-time feedback
- Maximum parallelization
- Aggressive caching strategies

#### Quick TDD Demo (`tdd_quick`)
- Simplified for demonstrations
- 70% test coverage threshold
- Single-threaded execution
- No caching (fresh runs)

## Command Line Usage

### Basic TDD Workflow

```bash
# Run TDD workflow with a task
python run.py workflow tdd --task "Create a calculator module"

# Run with strict TDD enforcement
python run.py workflow tdd --task "Build an API" --tdd-strict

# Run with performance optimizations
python run.py workflow tdd --task "Process large dataset" --performance
```

### TDD-Specific CLI Options

#### Global Flags

- `--tdd-strict`: Enforce all TDD rules strictly
- `--performance`: Enable all performance optimizations
- `--phase [red|yellow|green]`: Start from specific phase
- `--cache-info`: Display cache statistics after execution

#### Workflow Flags

- `--tdd`: Convert any workflow to use TDD
- `--coverage N`: Set test coverage threshold (default: 85)
- `--no-cache`: Disable test caching
- `--no-parallel`: Disable parallel test execution

### Examples

```bash
# Run calculator example with TDD
python run.py example tdd_demo

# Run performance demo
python run.py example performance_demo

# Convert MVP incremental to TDD
python run.py workflow mvp_incremental --task "..." --tdd

# Custom coverage threshold
python run.py workflow tdd --task "..." --coverage 90

# View cache statistics
python run.py workflow tdd --task "..." --cache-info
```

## Performance Monitoring

### Viewing Statistics

In interactive mode:
1. Go to TDD Mode → View Performance Statistics
2. Or Advanced Options → Performance Settings → View Cache Statistics

From command line:
```bash
python run.py workflow tdd --task "..." --cache-info
```

### Metrics Displayed

- **Test Cache Hit Rate**: Should be 85%+ for optimal performance
- **Parallel Execution Status**: Enabled/Disabled
- **Total Tests Run**: Cumulative count
- **Average Test Time**: Per test execution time
- **Memory Usage**: Current memory consumption

## Configuration

### Per-Workflow Settings

Each TDD workflow variant has default configurations:

```python
{
    "enforce_red_phase": True,      # Can't skip test writing
    "enable_test_caching": True,    # 85%+ hit rate
    "parallel_test_execution": True, # 2.8x speedup
    "retry_with_hints": True,       # Smart retry prompts
    "test_coverage_threshold": 85   # Minimum coverage
}
```

### Customizing Settings

1. **Interactive Mode**: Use "Configure TDD Settings" option
2. **CLI**: Use flags like `--coverage`, `--no-cache`, etc.
3. **Examples**: Modify YAML files in `demos/examples/`

## TDD Examples

### Pre-configured Examples

1. **tdd_demo.yaml**: String utilities with full TDD
2. **performance_demo.yaml**: Data processor with optimizations
3. **calculator.yaml**: Simple calculator with TDD

### Running Examples

```bash
# List all examples
python run.py list examples

# Run specific TDD example
python run.py example tdd_demo

# Run with custom settings
python run.py example tdd_demo --coverage 90 --no-cache
```

## Advanced Features

### Phase History

View TDD phase transitions:
1. Go to Advanced Options → View TDD Phase History
2. See timing for each phase
3. Analyze bottlenecks in development

### Performance Tuning

Access performance settings:
1. Advanced Options → Performance Settings
2. Toggle individual optimizations
3. Configure memory limits
4. Reset performance counters

### Export Configuration

Save current workflow configurations:
1. Advanced Options → Export Configuration
2. Creates timestamped JSON file
3. Use for backup or sharing

## Troubleshooting

### Common Issues

**Tests not failing in RED phase?**
- Ensure no implementation exists
- Check test logic is correct
- Verify `expect_failure=True` is set

**Low cache hit rate?**
- Enable caching with `--performance`
- Avoid modifying test files frequently
- Use consistent test naming

**Out of memory?**
- Enable memory spillover
- Reduce parallel execution
- Use `tdd_quick` for smaller projects

### Debug Mode

```bash
# Verbose output
python run.py workflow tdd --task "..." -v

# Dry run to preview
python run.py workflow tdd --task "..." --dry-run
```

## Best Practices

1. **Always start with RED**: Let tests fail first
2. **Small iterations**: Write one test at a time
3. **Use hints**: Pay attention to retry suggestions
4. **Monitor performance**: Check cache rates regularly
5. **Review in GREEN**: Ensure code quality before completion

## Related Documentation

- [Operation Red Yellow Overview](../operations/operation-red-yellow.md)
- [TDD Workflow Guide](../workflows/tdd-workflow.md)
- [Performance Optimization Guide](../operations/performance-optimizations.md)
- [TDD Quick Reference](../workflows/tdd-quick-reference.md)

---

[← Back to User Guide](../user-guide/) | [← Back to Docs](../)