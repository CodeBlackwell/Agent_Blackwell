# Installation Guide

This guide provides detailed instructions for installing and setting up the Multi-Agent Orchestrator System.

## 📋 System Requirements

### Minimum Requirements
- **Operating System**: Windows 10+, macOS 10.15+, or Linux (Ubuntu 20.04+)
- **Python**: Version 3.8 or higher
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 1GB free space
- **Network**: Internet connection for API calls

### Optional Requirements
- **Docker**: For containerized execution and testing
- **Graphviz**: For workflow visualization (`brew install graphviz` on macOS)

## 🔧 Installation Steps

### 1. Install Python

Verify Python installation:
```bash
python --version
# Should show Python 3.8 or higher
```

If not installed, download from [python.org](https://python.org).

### 2. Install UV Package Manager

UV is a fast Python package manager:
```bash
pip install uv
```

### 3. Clone the Repository

```bash
git clone <repository-url>
cd rebuild
```

### 4. Set Up Virtual Environment

```bash
# Create virtual environment
uv venv

# Activate virtual environment
# On Linux/macOS:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate
```

### 5. Install Dependencies

```bash
uv pip install -r requirements.txt
```

### 6. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your API keys
# Required: ANTHROPIC_API_KEY or OPENAI_API_KEY
```

## 🐳 Docker Installation (Optional)

### Install Docker

1. Download Docker Desktop from [docker.com](https://docker.com)
2. Install and start Docker Desktop
3. Verify installation:
   ```bash
   docker --version
   docker-compose --version
   ```

### Using Docker Compose

```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 🔐 API Key Configuration

### Anthropic Claude API
1. Sign up at [console.anthropic.com](https://console.anthropic.com)
2. Generate an API key
3. Add to `.env`:
   ```
   ANTHROPIC_API_KEY=your-key-here
   ```

### OpenAI API (Alternative)
1. Sign up at [platform.openai.com](https://platform.openai.com)
2. Generate an API key
3. Add to `.env`:
   ```
   OPENAI_API_KEY=your-key-here
   ```

## ✅ Verify Installation

### 1. Check Dependencies

```bash
# Verify Python packages
python -c "import fastapi; import httpx; print('Dependencies OK')"
```

### 2. Start Orchestrator

```bash
python orchestrator/orchestrator_agent.py
# Should show: "Orchestrator server started on http://localhost:8080"
```

### 3. Run Test Example

In a new terminal:
```bash
python run.py example hello_world
```

## 🚀 Post-Installation

### IDE Setup

#### VS Code
1. Install Python extension
2. Select interpreter: `.venv/bin/python`
3. Enable format on save

#### PyCharm
1. Configure interpreter to use `.venv`
2. Mark `src` as sources root
3. Enable code inspections

### Optional Tools

```bash
# Install development tools
uv pip install pytest black isort mypy

# Install visualization tools (macOS)
brew install graphviz

# Install visualization tools (Ubuntu)
sudo apt-get install graphviz
```

## 🔧 Troubleshooting Installation

### Common Issues

#### "uv: command not found"
```bash
# Reinstall uv
pip install --upgrade uv
```

#### "No module named 'fastapi'"
```bash
# Ensure virtual environment is activated
source .venv/bin/activate
# Reinstall dependencies
uv pip install -r requirements.txt
```

#### Permission Errors
```bash
# Use user installation
pip install --user uv
# Or use sudo (not recommended)
sudo pip install uv
```

### Platform-Specific Issues

#### Windows
- Use PowerShell or Git Bash
- May need to enable script execution:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```

#### macOS
- Install Xcode Command Line Tools if needed:
  ```bash
  xcode-select --install
  ```

#### Linux
- May need python3-venv package:
  ```bash
  sudo apt-get install python3-venv
  ```

## 📚 Next Steps

- [Quick Start Guide](quick-start.md) - Run your first example
- [Docker Setup](docker-setup.md) - Containerized deployment
- [Configuration Reference](../reference/configuration.md) - Advanced configuration

---

[← Back to User Guide](README.md) | [← Back to Docs](../README.md)