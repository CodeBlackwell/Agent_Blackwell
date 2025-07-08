# Contributing Guide

Thank you for your interest in contributing to the Multi-Agent Orchestrator System!

## 🚧 Under Construction

This guide is currently being developed. For now, please refer to:
- [Developer Guide](README.md) for development setup
- [Architecture Overview](architecture/README.md) for system design
- [Testing Guide](testing-guide.md) for test requirements

## Quick Start for Contributors

### 1. Fork and Clone
```bash
git fork <repository-url>
git clone <your-fork-url>
cd rebuild
```

### 2. Set Up Development Environment
```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

### 3. Create a Branch
```bash
git checkout -b feature/your-feature-name
```

### 4. Make Changes
- Follow existing code patterns
- Add tests for new features
- Update documentation

### 5. Run Tests
```bash
python run.py test all
```

### 6. Submit Pull Request
- Push your branch
- Open a PR with description
- Wait for review

## Code Style

- Follow PEP 8
- Use type hints
- Add docstrings
- Keep functions focused

## Testing Requirements

- Add unit tests for new features
- Ensure all tests pass
- Maintain test coverage

## Documentation

- Update relevant documentation
- Add docstrings to new functions
- Include examples where helpful

---

[← Back to Developer Guide](README.md) | [← Back to Docs](../README.md)