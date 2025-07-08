# Configuration Reference

Complete reference for all configuration options in the Multi-Agent Orchestrator System.

## 🚧 Under Construction

This documentation is currently being developed. For configuration help, please refer to:
- [Installation Guide](../user-guide/installation.md#configure-environment) for basic setup
- `.env.example` for environment variables

## Environment Variables

### Required Variables

#### ANTHROPIC_API_KEY
- **Type**: String
- **Description**: API key for Claude AI
- **Example**: `sk-ant-api03-...`

#### OPENAI_API_KEY (Alternative)
- **Type**: String
- **Description**: API key for OpenAI (if not using Claude)
- **Example**: `sk-...`

### Optional Variables

#### LOG_LEVEL
- **Type**: String
- **Default**: `INFO`
- **Options**: `DEBUG`, `INFO`, `WARNING`, `ERROR`

#### DOCKER_TIMEOUT
- **Type**: Integer
- **Default**: `60`
- **Description**: Timeout for Docker operations in seconds

## Configuration Files

### orchestrator_configs.py
Controls orchestrator behavior and output display.

```python
OUTPUT_DISPLAY_CONFIG = {
    "mode": "detailed",  # or "summary"
    "max_input_chars": 1000,
    "max_output_chars": 2000,
    "export_interactions": True
}
```

### workflow_config.py
Controls workflow execution parameters.

```python
# Retry settings
MAX_REVIEW_RETRIES = 3
MAX_TOTAL_RETRIES = 10

# Timeouts
EXECUTION_TIMEOUT = 60
VALIDATION_TIMEOUT = 30

# Paths
GENERATED_CODE_PATH = "./generated/"
```

## YAML Configuration

### Example Configurations
Located in `/examples/configs/`:
- `hello_world.yaml`
- `calculator.yaml`
- `todo_api.yaml`

### Format
```yaml
name: "Example Name"
description: "Description"
requirements: "Detailed requirements"
workflow_type: "full"
options:
  run_tests: true
  phases:
    phase_9: true
    phase_10: false
```

## Docker Configuration

### docker-compose.yml
```yaml
services:
  orchestrator:
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
```

### docker.env.example
Template for Docker environment variables.

---

[← Back to Reference](README.md) | [← Back to Docs](../README.md)