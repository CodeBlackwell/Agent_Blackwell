# Demos Directory

This directory contains example configurations and supporting libraries for the Multi-Agent Coding System.

## Structure

```
demos/
├── examples/          # YAML configuration files for example projects
│   ├── hello_world.yaml
│   └── string_utils.yaml
└── lib/              # Supporting libraries for the run.py script
    ├── config_loader.py     # Loads example configurations
    ├── interactive_menu.py  # Interactive menu system
    ├── workflow_runner.py   # Executes workflows
    ├── preflight_checker.py # System requirements checker
    └── output_formatter.py  # Formats workflow output
```

## Adding New Examples

To add a new example, create a YAML file in the `examples/` directory with the following structure:

```yaml
name: Example Name
description: Brief description of what this example creates
difficulty: beginner|intermediate|advanced
time_estimate: Estimated time to complete
requirements: |
  Detailed requirements for the project...
  
config:
  workflow_type: tdd|full|mvp_incremental
  run_tests: true|false
  test_coverage_threshold: 80-100
  # ... other workflow-specific configs
```

## Usage

List available examples:
```bash
python run.py example --list
```

Run an example:
```bash
python run.py example hello_world
```

## Default Behavior

The system no longer defaults to generating a calculator application. If you run a workflow without specific requirements, it will use the generic session name "project" instead of "calculator".