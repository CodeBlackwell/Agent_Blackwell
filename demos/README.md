# Demos and Examples Directory

Welcome to the unified demos directory for the Multi-Agent Coding System! This directory contains all demo scripts, examples, and helper utilities organized for easy discovery and use.

## Quick Start

The main entry point for all demos is the `run.py` script in the root directory:

```bash
# Interactive mode (recommended for beginners)
python run.py

# Run a specific example
python run.py example calculator

# Run a workflow with custom requirements
python run.py workflow tdd --task "Create a REST API"

# Run tests
python run.py test unit

# Get help
python run.py --help
```

## Directory Structure

```
demos/
├── README.md              # This file
├── examples/              # Pre-configured example projects
│   ├── calculator.yaml    # Simple calculator example
│   ├── todo_api.yaml      # TODO REST API example
│   └── auth_system.yaml   # Authentication system example
├── legacy/                # Old demo scripts (deprecated)
│   ├── hello_agents.py
│   ├── quickstart.py
│   └── simple_example.py
├── advanced/              # Advanced demonstrations
│   ├── mvp_incremental_demo.py
│   └── api_demo.py
└── lib/                   # Helper modules for demos
    ├── config_loader.py
    ├── interactive_menu.py
    ├── workflow_runner.py
    ├── preflight_checker.py
    └── output_formatter.py
```

## Examples

### Pre-configured Examples

The `examples/` directory contains YAML configuration files for common use cases:

1. **calculator.yaml** - A simple Python calculator with basic operations
   - Difficulty: Beginner
   - Time: 2-3 minutes
   - Features: Basic math operations, error handling, tests

2. **todo_api.yaml** - A REST API for TODO management
   - Difficulty: Intermediate
   - Time: 5-7 minutes
   - Features: CRUD operations, FastAPI, validation, tests

3. **auth_system.yaml** - A complete authentication system
   - Difficulty: Advanced
   - Time: 10-15 minutes
   - Features: JWT tokens, password hashing, role-based access

### Running Examples

```bash
# Run the calculator example
python run.py example calculator

# Run TODO API with all testing phases enabled
python run.py example todo-api --all-phases

# Run auth system with custom configuration
python run.py example auth-system --tests --no-integration
```

## Legacy Scripts

The `legacy/` directory contains the original demo scripts. These are deprecated but kept for backward compatibility:

- **hello_agents.py** - The simplest "Hello World" example
- **quickstart.py** - Interactive quickstart with auto-orchestrator startup
- **simple_example.py** - Basic example with command-line arguments

⚠️ **Note**: These scripts will show deprecation warnings. Please use `run.py` instead.

## Advanced Demos

The `advanced/` directory contains specialized demonstrations:

- **mvp_incremental_demo.py** - Comprehensive MVP incremental workflow demonstration
- **api_demo.py** - REST API integration examples

These demos showcase advanced features and are useful for understanding the full capabilities of the system.

## Helper Libraries

The `lib/` directory contains reusable modules used by the demo system:

- **config_loader.py** - Loads and validates YAML configuration files
- **interactive_menu.py** - Provides interactive UI components
- **workflow_runner.py** - Common workflow execution logic
- **preflight_checker.py** - System validation and dependency checking
- **output_formatter.py** - Consistent output formatting across demos

## Creating Your Own Examples

To create a new example:

1. Create a YAML file in `examples/` directory
2. Define the configuration following this structure:

```yaml
name: "My Example"
description: "Brief description"
difficulty: "Beginner|Intermediate|Advanced"
time_estimate: "X-Y minutes"
requirements: |
  Detailed requirements for your project...
config:
  workflow_type: "tdd"  # or "full", "mvp_incremental"
  run_tests: true
  run_integration_verification: false
expected_files:
  - main.py
  - test_main.py
```

3. Run your example: `python run.py example my-example`

## Tips for New Users

1. **Start with Interactive Mode**: Just run `python run.py` for a guided experience
2. **Try the Calculator Example**: It's the simplest and quickest to understand
3. **Enable Verbose Mode**: Use `-v` flag for detailed output
4. **Check System Requirements**: The preflight checker will validate your setup
5. **Read the Logs**: Detailed logs are saved in `demo_outputs/logs/`

## Troubleshooting

If you encounter issues:

1. Ensure the orchestrator is running: `python orchestrator/orchestrator_agent.py`
2. Check you're in a virtual environment
3. Verify all dependencies are installed: `uv pip install -r requirements.txt`
4. Run with verbose mode for more details: `python run.py -v`
5. Check the logs in `demo_outputs/logs/`

## Migration from Old Scripts

If you were using the old demo scripts, here's how to migrate:

| Old Command | New Command |
|-------------|-------------|
| `python hello_agents.py` | `python run.py example hello-world` |
| `python quickstart.py --tdd` | `python run.py workflow tdd` |
| `python simple_example.py --workflow full` | `python run.py workflow full` |
| `python demo_mvp_incremental.py --preset calculator` | `python run.py example calculator` |
| `python test_runner.py unit` | `python run.py test unit` |

## Contributing

When adding new demos:

1. Follow the existing structure and naming conventions
2. Include comprehensive documentation
3. Add appropriate error handling
4. Test thoroughly before committing
5. Update this README if adding new categories

Happy coding with the Multi-Agent System!