# Run Script Guide

The `run.py` script is the unified entry point for all operations in the Multi-Agent Orchestrator System.

## 🆕 New Features

**[TDD Features Guide](run-script-tdd.md)** - Comprehensive guide to using Test-Driven Development features with Operation Red Yellow's RED-YELLOW-GREEN phases.

## Overview

The `run.py` script provides a single, consistent interface for:
- Running examples
- Executing workflows (including TDD with RED-YELLOW-GREEN phases)
- Running tests
- Interactive mode with TDD-specific menus
- Configuration management
- Performance monitoring and optimization

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