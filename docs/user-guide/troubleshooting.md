# Troubleshooting Guide

This guide helps you resolve common issues when using the Multi-Agent Orchestrator System.

## 🚧 Under Construction

This documentation is currently being developed. In the meantime, please refer to:
- [Quick Start Guide](quick-start.md#troubleshooting) for basic troubleshooting
- [Installation Guide](installation.md#troubleshooting-installation) for setup issues
- [User Guide](README.md) for general help

## Common Issues

### Orchestrator Server Not Running
**Problem**: Error message indicating the orchestrator server is not available.

**Solution**:
1. Start the orchestrator in a separate terminal:
   ```bash
   python orchestrator/orchestrator_agent.py
   ```
2. Verify it's running on port 8080
3. Keep the terminal open while using the system

### Missing Dependencies
**Problem**: Import errors or missing package errors.

**Solution**:
1. Ensure virtual environment is activated:
   ```bash
   source .venv/bin/activate
   ```
2. Reinstall dependencies:
   ```bash
   uv pip install -r requirements.txt
   ```

### API Key Errors
**Problem**: Authentication errors or API key not found.

**Solution**:
1. Check `.env` file exists (copy from `.env.example` if needed)
2. Verify API keys are set correctly
3. Ensure no extra spaces or quotes in the `.env` file

## Getting Help

- Check logs in the `logs/` directory
- Use `--verbose` flag for detailed output
- Review generated `COMPLETION_REPORT.md` files
- Report issues on GitHub

---

[← Back to User Guide](README.md) | [← Back to Docs](../README.md)