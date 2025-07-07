# 🚀 Quick Start Examples

Examples are now integrated into the unified `run.py` script for a better experience:

## 1. 👋 Hello World Example - Absolute Beginner
The simplest possible example. Creates a "Hello World" program using AI agents.

```bash
# First, start the orchestrator
python orchestrator/orchestrator_agent.py

# Then run the example
python run.py example hello_world
```

**What it does:** Creates a simple Python function with tests using 6 AI agents working together.

## 2. 📘 Calculator Example - Basic Usage
A more complete example with different workflow options.

```bash
# Start the orchestrator first
python orchestrator/orchestrator_agent.py

# Run the calculator example
python run.py example calculator

# Or run a custom workflow with your own task
python run.py workflow tdd --task "Create a password generator"

# Use different workflows
python run.py workflow full --task "Build a calculator class"
```

**Available workflows:**
- `tdd` - Test-Driven Development (tests first, then code)
- `full` - Complete workflow (no test-first approach)
- `plan` - Just planning phase
- `design` - Just design phase
- `implement` - Just coding phase

## 3. 🎯 Interactive Mode - Advanced
Full-featured interactive mode for exploring all capabilities.

```bash
# Interactive mode - menu-driven interface
python run.py

# Or use command line directly
python run.py workflow tdd --task "Create a REST API"
python run.py workflow full --task "Build a todo app"
python run.py workflow planning --task "Design a chat system"
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

- **New to the system?** Start with `python run.py example hello_world`
- **Want to experiment?** Use `python run.py example calculator`
- **Need all features?** Use `python run.py` (interactive mode)

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
- [`README.md`](../../README.md) - Project overview
- [`CLAUDE.md`](../../CLAUDE.md) - Detailed system documentation
- [Testing Guide](../developer-guide/testing-guide.md) - Testing documentation

---

[← Back to User Guide](../user-guide/) | [← Back to Docs](../)