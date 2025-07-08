# Run Script Guide

The `run.py` script is the unified entry point for all operations in the Multi-Agent Orchestrator System.

## 🚧 Under Construction

This documentation is currently being developed. For now, please refer to:
- [Quick Start Guide](quick-start.md) for basic usage
- [Examples](examples.md) for common use cases

## Overview

The `run.py` script provides a single, consistent interface for:
- Running examples
- Executing workflows
- Running tests
- Interactive mode
- Configuration management

## Basic Usage

```bash
# Interactive mode
python run.py

# Run an example
python run.py example calculator

# Execute a workflow
python run.py workflow tdd --task "Create a function"

# Run tests
python run.py test all

# Get help
python run.py --help
```

## Commands

### Example Command
```bash
python run.py example <name> [options]
```

### Workflow Command
```bash
python run.py workflow <type> --task <requirements> [options]
```

### Test Command
```bash
python run.py test <categories> [options]
```

## Options

- `--verbose`: Detailed output
- `--help`: Show help message
- `--list`: List available options

For complete documentation, run:
```bash
python run.py --help
```

---

[← Back to User Guide](README.md) | [← Back to Docs](../README.md)