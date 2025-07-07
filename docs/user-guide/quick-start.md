# Quick Start Guide

Get up and running with the Multi-Agent Orchestrator System in just a few minutes!

## 🚀 5-Minute Quick Start

### 1. Prerequisites

Ensure you have:
- Python 3.8 or higher
- Git (for cloning the repository)
- UV package manager: `pip install uv`

### 2. Setup

```bash
# Clone the repository
git clone <repository-url>
cd rebuild

# Create and activate virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env to add your API keys
```

### 3. Start the Servers

You need two terminals:

**Terminal 1 - Orchestrator Server:**
```bash
python orchestrator/orchestrator_agent.py
```

**Terminal 2 - Run Examples:**
```bash
# Run your first example
python run.py example hello_world
```

## 🎯 First Examples

### Hello World (Simplest)
```bash
python run.py example hello_world
```
This creates a simple "Hello, World!" program to verify everything is working.

### Calculator (Beginner)
```bash
python run.py example calculator
```
This creates a basic calculator with add, subtract, multiply, and divide functions.

### Interactive Mode
```bash
python run.py
```
This launches an interactive menu where you can:
- Choose from various examples
- Configure workflows
- Run custom tasks

## 💡 What's Next?

### Try Different Workflows

1. **TDD Workflow** - Test-driven development
   ```bash
   python run.py workflow tdd --task "Create a function to validate email addresses"
   ```

2. **MVP Incremental** - Build feature by feature
   ```bash
   python run.py example todo_api
   ```

3. **Full Workflow** - Complete development cycle
   ```bash
   python run.py workflow full --task "Create a password strength checker"
   ```

### Explore the Output

Generated code is saved in:
```
generated/
└── app_generated_[timestamp]/
    ├── main.py          # Your generated code
    ├── test_*.py        # Generated tests
    └── README.md        # Documentation
```

## 🛠️ Common Commands

```bash
# List all examples
python run.py list examples

# Run tests
python run.py test unit

# Get help
python run.py --help

# Run with verbose output
python run.py example calculator --verbose
```

## ❓ Troubleshooting

### "Orchestrator server not running"
Make sure you have the orchestrator running in a separate terminal:
```bash
python orchestrator/orchestrator_agent.py
```

### "Missing dependencies"
Ensure your virtual environment is activated and dependencies installed:
```bash
source .venv/bin/activate
uv pip install -r requirements.txt
```

### "API key errors"
Check your `.env` file has the required API keys set.

## 📚 Learn More

- [Examples Guide](examples.md) - More example projects
- [User Guide](README.md) - Comprehensive usage documentation
- [Workflows Guide](../workflows/README.md) - Understanding different workflows
- [Troubleshooting](troubleshooting.md) - Detailed troubleshooting guide

---

[← Back to User Guide](README.md) | [← Back to Docs](../README.md)