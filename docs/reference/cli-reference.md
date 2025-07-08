# CLI Reference

Complete command-line interface reference for the Multi-Agent Orchestrator System.

## 🚧 Under Construction

This documentation is currently being developed. For CLI usage, run:
```bash
python run.py --help
```

## Overview

The `run.py` script provides a unified command-line interface for all system operations.

## Global Options

- `--help`, `-h`: Show help message
- `--verbose`, `-v`: Enable verbose output
- `--version`: Show version information

## Commands

### run.py (Interactive Mode)
```bash
python run.py
```
Launches interactive menu for guided usage.

### run.py example
```bash
python run.py example <name> [options]
```

**Arguments:**
- `<name>`: Example name (hello_world, calculator, todo_api, etc.)

**Options:**
- `--verbose`: Show detailed output
- `--save-output`: Save results to file

**Examples:**
```bash
python run.py example calculator
python run.py example todo_api --verbose
```

### run.py workflow
```bash
python run.py workflow <type> --task <requirements> [options]
```

**Arguments:**
- `<type>`: Workflow type (tdd, full, mvp_incremental, mvp_incremental_tdd)

**Required Options:**
- `--task`: Task requirements (string)

**Optional:**
- `--verbose`: Detailed output
- `--timeout`: Execution timeout in seconds

**Examples:**
```bash
python run.py workflow tdd --task "Create a calculator"
python run.py workflow mvp_incremental --task "Build a REST API"
```

### run.py test
```bash
python run.py test <categories> [options]
```

**Arguments:**
- `<categories>`: Test categories (all, unit, integration, workflow, agent, etc.)

**Options:**
- `-p`, `--parallel`: Run tests in parallel
- `-v`, `--verbose`: Verbose test output
- `--ci`: CI mode (no colors/emojis)

**Examples:**
```bash
python run.py test all
python run.py test unit integration -p
python run.py test workflow --verbose
```

### run.py list
```bash
python run.py list <type>
```

**Arguments:**
- `<type>`: What to list (examples, workflows, tests)

**Examples:**
```bash
python run.py list examples
python run.py list workflows
python run.py list tests
```

## Advanced Usage

### Custom Configuration
```bash
python run.py workflow full --task "..." --config custom.yaml
```

### Batch Processing
```bash
python run.py batch --file tasks.txt --output results/
```

## Exit Codes

- `0`: Success
- `1`: General error
- `2`: Invalid arguments
- `3`: Missing dependencies
- `4`: Execution error

---

[← Back to Reference](README.md) | [← Back to Docs](../README.md)