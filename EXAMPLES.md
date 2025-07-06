# 🚀 Quick Start Examples

This directory contains three example scripts to help you get started with the Multi-Agent Coding System:

## 1. 👋 `hello_agents.py` - Absolute Beginner
The simplest possible example. Creates a "Hello World" program using AI agents.

```bash
# First, start the orchestrator
python orchestrator/orchestrator_agent.py

# Then run the example
python hello_agents.py
```

**What it does:** Creates a simple Python function with tests using 6 AI agents working together.

## 2. 📘 `simple_example.py` - Basic Usage
A more complete example with command-line options and different workflows.

```bash
# Start the orchestrator first
python orchestrator/orchestrator_agent.py

# Run with defaults (TDD workflow)
python simple_example.py

# Specify a workflow
python simple_example.py --workflow full

# Provide your own task
python simple_example.py --task "Create a password generator"

# Combine options
python simple_example.py --workflow tdd --task "Build a calculator class"
```

**Available workflows:**
- `tdd` - Test-Driven Development (tests first, then code)
- `full` - Complete workflow (no test-first approach)
- `plan` - Just planning phase
- `design` - Just design phase
- `implement` - Just coding phase

## 3. 🎯 `quickstart.py` - Advanced Interactive
Full-featured example with interactive mode and automatic orchestrator startup (requires MCP).

```bash
# Interactive mode - prompts for workflow and task
python quickstart.py

# Command line mode
python quickstart.py --tdd --task "Create a REST API"
python quickstart.py --full --task "Build a todo app"
python quickstart.py --plan --task "Design a chat system"
```

## 📋 Common Tasks to Try

Here are some example tasks you can use with any of the scripts:

**Simple Tasks:**
- "Create a function to reverse a string"
- "Build a temperature converter (Celsius to Fahrenheit)"
- "Write a password strength checker"

**Medium Tasks:**
- "Create a Calculator class with basic operations"
- "Build a simple TODO list manager"
- "Implement a basic file encryption tool"

**Complex Tasks:**
- "Create a REST API for a blog system"
- "Build a command-line expense tracker"
- "Design a real-time chat application architecture"

## 🎯 Which Example Should I Use?

- **New to the system?** Start with `hello_agents.py`
- **Want to experiment?** Use `simple_example.py`
- **Need all features?** Use `quickstart.py`

## 📁 Output Location

All generated code will be saved in the `./generated/` directory with descriptive folder names like:
- `generated/20240105_143022_hello_world_abc123/`
- `generated/20240105_143022_calculator_class_def456/`

## 🐛 Troubleshooting

**"Connection refused" error:**
Make sure the orchestrator is running:
```bash
python orchestrator/orchestrator_agent.py
```

**"Module not found" error:**
Install dependencies:
```bash
uv pip install -r requirements.txt
```

**Need more help?**
Check the main documentation:
- `README.md` - Project overview
- `CLAUDE.md` - Detailed system documentation
- `TEST_GUIDE.md` - Testing documentation