# Development Setup Guide

## Overview

This guide walks you through setting up a development environment for the Multi-Agent Orchestrator System. Follow these steps to get your local environment ready for development, testing, and contribution.

## Prerequisites

### System Requirements

- **Operating System**: Linux, macOS, or Windows (with WSL2)
- **Python**: 3.10 or higher
- **Memory**: Minimum 8GB RAM (16GB recommended)
- **Storage**: At least 10GB free space
- **Docker**: Latest version (for executor agent)

### Required Software

1. **Python 3.10+**
   ```bash
   # Check Python version
   python --version
   
   # macOS (using Homebrew)
   brew install python@3.10
   
   # Ubuntu/Debian
   sudo apt update
   sudo apt install python3.10 python3.10-venv python3.10-dev
   
   # Windows (using Chocolatey)
   choco install python310
   ```

2. **UV Package Manager** (Recommended)
   ```bash
   # Install UV
   pip install uv
   
   # Or using pipx
   pipx install uv
   ```

3. **Git**
   ```bash
   # macOS
   brew install git
   
   # Ubuntu/Debian
   sudo apt install git
   
   # Windows
   choco install git
   ```

4. **Docker** (Optional, for executor agent)
   - [Docker Desktop](https://www.docker.com/products/docker-desktop)

## Initial Setup

### 1. Clone the Repository

```bash
# Clone via HTTPS
git clone https://github.com/your-org/multi-agent-orchestrator.git

# Or via SSH
git clone git@github.com:your-org/multi-agent-orchestrator.git

cd multi-agent-orchestrator
```

### 2. Set Up Virtual Environment

```bash
# Using UV (recommended)
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Or using standard venv
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Using UV
uv pip install -r requirements.txt
uv pip install -r requirements-dev.txt  # Development dependencies

# Or using pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 4. Environment Configuration

Create a `.env` file in the project root:

```bash
# Copy the example environment file
cp .env.example .env

# Edit with your configuration
nano .env  # or use your preferred editor
```

Required environment variables:

```env
# API Keys (required for AI agents)
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here  # Optional

# Server Configuration
ORCHESTRATOR_HOST=localhost
ORCHESTRATOR_PORT=8080
API_HOST=localhost
API_PORT=8000

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=detailed

# Development Settings
DEBUG=True
RELOAD=True
```

## IDE Setup

### Visual Studio Code

1. **Install Extensions**:
   - Python
   - Pylance
   - Python Test Explorer
   - GitLens
   - Docker (if using Docker)

2. **Configure Settings** (`.vscode/settings.json`):
   ```json
   {
     "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
     "python.linting.enabled": true,
     "python.linting.pylintEnabled": true,
     "python.linting.flake8Enabled": true,
     "python.formatting.provider": "black",
     "python.testing.pytestEnabled": true,
     "python.testing.pytestArgs": ["tests"],
     "editor.formatOnSave": true,
     "editor.codeActionsOnSave": {
       "source.organizeImports": true
     }
   }
   ```

3. **Launch Configuration** (`.vscode/launch.json`):
   ```json
   {
     "version": "0.2.0",
     "configurations": [
       {
         "name": "Orchestrator Server",
         "type": "python",
         "request": "launch",
         "module": "orchestrator.orchestrator_agent",
         "justMyCode": false
       },
       {
         "name": "API Server",
         "type": "python",
         "request": "launch",
         "module": "api.orchestrator_api",
         "justMyCode": false
       },
       {
         "name": "Run Tests",
         "type": "python",
         "request": "launch",
         "module": "pytest",
         "args": ["tests/", "-v"]
       }
     ]
   }
   ```

### PyCharm

1. **Configure Project Interpreter**:
   - File → Settings → Project → Python Interpreter
   - Select the virtual environment: `.venv`

2. **Configure Run Configurations**:
   - Add Configuration → Python
   - Script path: `orchestrator/orchestrator_agent.py`
   - Working directory: Project root

3. **Enable Code Quality Tools**:
   - Settings → Editor → Inspections → Python
   - Enable all relevant inspections

## Development Workflow

### 1. Start Development Servers

```bash
# Terminal 1: Start Orchestrator (ACP Server)
python orchestrator/orchestrator_agent.py

# Terminal 2: Start API Server
python api/orchestrator_api.py

# Terminal 3: Run development tasks
# Your development commands here
```

### 2. Running Tests

```bash
# Run all tests
python run.py test all

# Run specific test categories
python run.py test unit
python run.py test integration
python run.py test workflow

# Run with coverage
pytest --cov=agents --cov=workflows --cov-report=html
```

### 3. Code Quality Checks

```bash
# Format code with Black
black .

# Lint with flake8
flake8 . --config=.flake8

# Type checking with mypy
mypy . --config-file=mypy.ini

# Sort imports
isort . --settings-file=.isort.cfg
```

### 4. Pre-commit Hooks

Set up pre-commit hooks for automatic code quality:

```bash
# Install pre-commit
pip install pre-commit

# Install the git hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

`.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
      - id: black
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.0.0
    hooks:
      - id: mypy
```

## Debugging

### 1. Debug Configuration

Enable detailed logging:

```python
# In your development script
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### 2. Using Debugger

With VS Code:
1. Set breakpoints by clicking left of line numbers
2. Press F5 to start debugging
3. Use debug console for inspection

With PyCharm:
1. Click in the gutter to set breakpoints
2. Right-click → Debug
3. Use debugger panel for variable inspection

### 3. Interactive Debugging

```python
# Add in your code for debugging
import pdb; pdb.set_trace()  # Standard debugger

# Or use IPython debugger
import ipdb; ipdb.set_trace()  # Enhanced debugger
```

## Common Development Tasks

### 1. Adding a New Agent

```bash
# Create agent structure
mkdir -p agents/new_agent
touch agents/new_agent/__init__.py
touch agents/new_agent/new_agent.py
touch agents/new_agent/test_new_agent_debug.py

# Run agent tests
python agents/new_agent/test_new_agent_debug.py
```

### 2. Creating a New Workflow

```bash
# Create workflow structure
mkdir -p workflows/new_workflow
touch workflows/new_workflow/__init__.py
touch workflows/new_workflow/workflow.py
touch workflows/new_workflow/config.py

# Test workflow
python tests/test_workflows.py --workflow new_workflow
```

### 3. Running Examples

```bash
# Run interactive examples
python run.py

# Run specific example
python run.py example calculator

# Run with custom task
python run.py workflow full --task "Create a TODO app"
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Ensure you're in the virtual environment
   which python  # Should show .venv/bin/python
   
   # Reinstall dependencies
   uv pip install -r requirements.txt --force-reinstall
   ```

2. **Port Already in Use**
   ```bash
   # Find process using port
   lsof -i :8080  # macOS/Linux
   netstat -ano | findstr :8080  # Windows
   
   # Kill the process
   kill -9 <PID>  # macOS/Linux
   taskkill /PID <PID> /F  # Windows
   ```

3. **Docker Issues**
   ```bash
   # Ensure Docker is running
   docker ps
   
   # Reset Docker
   docker system prune -a
   ```

4. **API Key Issues**
   ```bash
   # Verify environment variables
   python -c "import os; print(os.getenv('OPENAI_API_KEY'))"
   
   # Re-export if needed
   export OPENAI_API_KEY="your_key_here"
   ```

## Performance Profiling

### 1. CPU Profiling

```python
import cProfile
import pstats

# Profile code
profiler = cProfile.Profile()
profiler.enable()

# Your code here

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)
```

### 2. Memory Profiling

```bash
# Install memory profiler
pip install memory_profiler

# Run with memory profiling
python -m memory_profiler your_script.py
```

### 3. Async Profiling

```python
import asyncio
import aiomonitor

async def main():
    # Start monitor
    with aiomonitor.start_monitor(loop=asyncio.get_event_loop()):
        # Your async code here
        await your_async_function()

asyncio.run(main())
```

## Next Steps

- Read the [Architecture Overview](architecture/README.md)
- Explore [Agent Development](agent-development.md)
- Check out [Workflow Development](workflow-development.md)
- Review [Testing Guide](testing-guide.md)
- Join the development community

## Getting Help

- Check the [FAQ](../user-guide/faq.md)
- Review [Troubleshooting Guide](../user-guide/troubleshooting.md)
- Open an issue on GitHub
- Join our Discord community