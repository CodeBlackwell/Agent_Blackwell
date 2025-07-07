# Migration Guide: Moving to the Unified Runner

This guide helps users migrate from the old demo scripts to the new unified `run.py` script.

## Overview

We've consolidated all demo scripts, examples, and test runners into a single, powerful `run.py` script. This provides:

- 🎯 **Single entry point** for all functionality
- 🚀 **Interactive mode** for beginners
- 💪 **Powerful CLI** for advanced users
- 🧩 **Consistent interface** across all operations

## Quick Migration Reference

### Running Examples

| Old Command | New Command |
|-------------|-------------|
| `python hello_agents.py` | `python run.py example hello_world` |
| `python quickstart.py` | `python run.py` (interactive mode) |
| `python quickstart.py --tdd` | `python run.py workflow tdd` |
| `python quickstart.py --full` | `python run.py workflow full` |
| `python simple_example.py` | `python run.py example calculator` |
| `python simple_example.py --workflow tdd --task "..."` | `python run.py workflow tdd --task "..."` |

### Running Demos

| Old Command | New Command |
|-------------|-------------|
| `python demo_mvp_incremental.py` | `python demos/advanced/mvp_incremental_demo.py` |
| `python demo_mvp_incremental.py --preset calculator` | `python run.py example calculator` |
| `python demo_mvp_incremental_enhancement.py` | `python demos/advanced/mvp_enhancement_demo.py` |

### Running Tests

| Old Command | New Command |
|-------------|-------------|
| `python test_runner.py` | `python run.py test all` |
| `python test_runner.py unit` | `python run.py test unit` |
| `python test_runner.py -p` | `python run.py test all -p` |
| `python test_runner.py --quick` | `python run.py test unit` |

## Detailed Migration Instructions

### 1. Interactive Mode (Recommended)

The easiest way to get started with the new system:

```bash
python run.py
```

This launches an interactive menu that guides you through:
- Running examples
- Executing workflows
- Running tests
- API demos
- Advanced options

### 2. Command Line Interface

The new CLI provides more features and better organization:

#### Examples
```bash
# List available examples
python run.py list examples

# Run a specific example
python run.py example calculator

# Run with options
python run.py --dry-run example todo_api
python run.py example auth_system --all-phases
```

#### Workflows
```bash
# List available workflows
python run.py list workflows

# Run a workflow
python run.py workflow tdd --task "Create a calculator"
python run.py workflow mvp_incremental --requirements-file spec.txt

# With options
python run.py workflow full --task "Build a REST API" --all-phases
```

#### Tests
```bash
# List test categories
python run.py list tests

# Run tests
python run.py test unit
python run.py test unit integration
python run.py test all --parallel

# CI mode
python run.py test all --ci
```

### 3. Configuration Files

Examples are now defined in YAML files in `demos/examples/`:

```yaml
# demos/examples/my_example.yaml
name: "My Example"
description: "Brief description"
difficulty: "Beginner"
time_estimate: "5 minutes"
requirements: |
  Detailed requirements here...
config:
  workflow_type: "tdd"
  run_tests: true
expected_files:
  - main.py
  - test_main.py
```

### 4. Output Modes

Control output verbosity:

```bash
# Normal output (default)
python run.py example calculator

# Short mode (minimal output)
python run.py -s example calculator

# Verbose mode (detailed output)
python run.py -v example calculator
```

### 5. Dry Run

Preview what will happen without executing:

```bash
python run.py --dry-run example calculator
python run.py --dry-run workflow tdd --task "Test task"
```

## New Features

The unified runner includes several new features:

1. **Preflight Checks**: Automatic system validation before running
2. **Progress Tracking**: Real-time progress indicators
3. **Better Error Messages**: Helpful suggestions when things go wrong
4. **Consistent Output**: Formatted output across all operations
5. **JSON Reports**: Automatic generation of execution reports

## Backward Compatibility

The old scripts still exist but show deprecation warnings:

```bash
$ python hello_agents.py
⚠️  hello_agents.py is deprecated!
   Please use: python run.py example hello_world
   This wrapper will be removed in a future version.

🔄 Redirecting to: python run.py example hello_world
```

These wrapper scripts will be removed in a future version.

## Troubleshooting

### Common Issues

1. **"Command not found"**
   - Make sure you're in the project root directory
   - Ensure `run.py` has execute permissions: `chmod +x run.py`

2. **"Example not found"**
   - List available examples: `python run.py list examples`
   - Check spelling and case sensitivity

3. **"Missing dependencies"**
   - The preflight checker will identify missing packages
   - Install with: `uv pip install -r requirements.txt`

### Getting Help

```bash
# General help
python run.py --help

# Command-specific help
python run.py example --help
python run.py workflow --help
python run.py test --help
```

## Benefits of Migration

1. **Simplified Interface**: One command for everything
2. **Better Discovery**: Interactive mode helps find features
3. **Consistent Experience**: Same patterns across all operations
4. **Future-Proof**: New features will be added to `run.py`
5. **Better Documentation**: Built-in help and examples

## Next Steps

1. Try the interactive mode: `python run.py`
2. Explore available examples: `python run.py list examples`
3. Read the demos README: `demos/README.md`
4. Check out advanced demos in `demos/advanced/`

## Questions?

If you have questions or issues:
- Check the help: `python run.py --help`
- Read the documentation in `demos/README.md`
- Submit an issue on GitHub

Happy coding with the new unified runner! 🚀

---

[← Back to Developer Guide](../developer-guide/) | [← Back to Docs](../)