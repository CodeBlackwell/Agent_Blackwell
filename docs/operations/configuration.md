# Configuration Guide

## Overview

This guide covers all configuration options for the Multi-Agent Orchestrator System. The system uses a hierarchical configuration approach with environment variables, configuration files, and runtime parameters.

## Configuration Hierarchy

Configuration is loaded in the following order (later sources override earlier ones):

1. Default configuration (built into the code)
2. Configuration files (YAML/JSON)
3. Environment variables
4. Command-line arguments
5. Runtime parameters

## Environment Variables

### Core Configuration

```bash
# API Keys (Required)
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key  # Optional

# Server Configuration
ORCHESTRATOR_HOST=localhost
ORCHESTRATOR_PORT=8080
API_HOST=localhost
API_PORT=8000

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT=detailed  # simple, detailed, json
LOG_FILE=logs/orchestrator.log
LOG_ROTATION=daily  # daily, size, time
LOG_RETENTION_DAYS=30

# Performance
MAX_WORKERS=4
REQUEST_TIMEOUT=300
EXECUTION_TIMEOUT=600
RETRY_ATTEMPTS=3
RETRY_DELAY=5

# Storage
OUTPUT_DIRECTORY=./generated
TEMP_DIRECTORY=/tmp/orchestrator
CACHE_ENABLED=true
CACHE_TTL=3600

# Development
DEBUG=false
RELOAD=false
PROFILE=false
```

### Workflow Configuration

```bash
# TDD Workflow
TDD_MAX_RETRIES=3
TDD_TEST_COVERAGE_THRESHOLD=80
TDD_ENABLE_INTEGRATION_TESTS=true
TDD_AUTO_APPROVE_AFTER_RETRIES=true

# Full Workflow
FULL_WORKFLOW_ENABLE_PARALLEL=true
FULL_WORKFLOW_MAX_REVIEW_ITERATIONS=3
FULL_WORKFLOW_CODE_STYLE=PEP8

# MVP Incremental
MVP_MAX_FEATURES=20
MVP_FEATURE_VALIDATION=strict
MVP_ENABLE_INCREMENTAL_TESTING=true
```

### Agent Configuration

```bash
# Planner Agent
PLANNER_MAX_DEPTH=3
PLANNER_INCLUDE_TIMELINE=true
PLANNER_DETAIL_LEVEL=high

# Coder Agent
CODER_LANGUAGE_PREFERENCE=python
CODER_INCLUDE_COMMENTS=true
CODER_ERROR_HANDLING=comprehensive

# Reviewer Agent
REVIEWER_CHECK_SECURITY=true
REVIEWER_CHECK_PERFORMANCE=true
REVIEWER_SUGGEST_REFACTORING=true

# Executor Agent
EXECUTOR_USE_DOCKER=true
EXECUTOR_TIMEOUT=60
EXECUTOR_MEMORY_LIMIT=512M
```

## Configuration Files

### Main Configuration (config.yaml)

```yaml
# config.yaml
system:
  name: "Multi-Agent Orchestrator"
  version: "2.0.0"
  environment: "production"  # development, staging, production

server:
  orchestrator:
    host: "0.0.0.0"
    port: 8080
    workers: 4
    keepalive: 30
  api:
    host: "0.0.0.0"
    port: 8000
    cors:
      enabled: true
      origins: ["https://yourdomain.com"]
    rate_limit:
      enabled: true
      calls: 100
      period: 60

logging:
  level: "INFO"
  format: "detailed"
  outputs:
    - type: "console"
      format: "colored"
    - type: "file"
      path: "logs/orchestrator.log"
      rotation: "daily"
      retention: 30
    - type: "syslog"
      host: "localhost"
      port: 514

agents:
  defaults:
    timeout: 300
    retries: 3
    retry_delay: 5
  
  planner:
    model: "gpt-4"
    temperature: 0.7
    max_tokens: 2000
    
  coder:
    model: "gpt-4"
    temperature: 0.3
    max_tokens: 4000
    
  reviewer:
    model: "gpt-4"
    temperature: 0.5
    max_tokens: 1500

workflows:
  defaults:
    output_directory: "./generated"
    save_intermediate: true
    enable_caching: true
    
  tdd:
    max_retries: 3
    test_coverage_threshold: 80
    test_frameworks:
      python: "pytest"
      javascript: "jest"
      
  full:
    enable_parallel: true
    max_review_iterations: 3
    code_styles:
      python: "PEP8"
      javascript: "standard"
      
  mvp_incremental:
    max_features: 20
    validation_mode: "strict"
    checkpoint_interval: 5

storage:
  type: "local"  # local, s3, gcs, azure
  local:
    base_path: "./data"
  s3:
    bucket: "orchestrator-storage"
    region: "us-east-1"
    prefix: "orchestrator/"
    
monitoring:
  metrics:
    enabled: true
    provider: "prometheus"
    port: 9090
    
  tracing:
    enabled: true
    provider: "jaeger"
    endpoint: "http://localhost:14268/api/traces"
    
  health_check:
    enabled: true
    interval: 30
    timeout: 5

security:
  authentication:
    enabled: true
    type: "jwt"  # jwt, oauth2, api_key
    secret_key: "${SECRET_KEY}"
    algorithm: "HS256"
    expiration: 3600
    
  encryption:
    enabled: true
    algorithm: "AES-256-GCM"
    key_rotation_days: 90
    
  audit:
    enabled: true
    log_level: "all"  # all, writes, errors
    retention_days: 365

integrations:
  github:
    enabled: true
    token: "${GITHUB_TOKEN}"
    default_branch: "main"
    
  slack:
    enabled: false
    webhook_url: "${SLACK_WEBHOOK_URL}"
    channels:
      notifications: "#orchestrator-notifications"
      errors: "#orchestrator-errors"
      
  database:
    enabled: false
    type: "postgresql"
    connection_string: "${DATABASE_URL}"
    pool_size: 20
    
plugins:
  enabled: true
  directory: "./plugins"
  auto_load: true
  whitelist: []  # Empty means all plugins allowed
  blacklist: []
```

### Workflow-Specific Configuration

```yaml
# workflows/tdd/config.yaml
name: "TDD Workflow"
version: "1.0.0"
description: "Test-Driven Development workflow"

phases:
  planning:
    agent: "planner_agent"
    timeout: 120
    retries: 2
    config:
      depth: 3
      include_tests: true
      
  test_writing:
    agent: "test_writer_agent"
    timeout: 180
    retries: 3
    config:
      framework: "pytest"
      coverage_target: 80
      
  implementation:
    agent: "coder_agent"
    timeout: 300
    retries: 3
    config:
      style: "TDD"
      run_tests: true
      
  review:
    agent: "reviewer_agent"
    timeout: 120
    retries: 1
    config:
      focus: ["tests", "coverage", "implementation"]

error_handling:
  continue_on_error: false
  max_total_retries: 10
  fallback_workflow: "full"

output:
  format: "structured"
  include_test_results: true
  generate_coverage_report: true
```

## Runtime Configuration

### Command-Line Arguments

```bash
# Override configuration via CLI
python orchestrator/orchestrator_agent.py \
  --host 0.0.0.0 \
  --port 8080 \
  --log-level DEBUG \
  --config custom-config.yaml

# API server with custom settings
python api/orchestrator_api.py \
  --workers 8 \
  --timeout 600 \
  --rate-limit 200 \
  --cors-origins "https://app1.com,https://app2.com"
```

### Dynamic Configuration

```python
# Programmatic configuration
from orchestrator.config import Config

# Load configuration
config = Config()
config.load_file("config.yaml")
config.load_env()

# Override specific values
config.set("agents.planner.temperature", 0.8)
config.set("workflows.tdd.max_retries", 5)

# Get configuration values
planner_config = config.get("agents.planner")
api_key = config.get("api_keys.openai", env_var="OPENAI_API_KEY")

# Update configuration at runtime
async def update_config(new_config: dict):
    config.update(new_config)
    await config.reload_agents()
```

## Configuration Best Practices

### 1. Environment-Specific Files

```bash
# Structure
config/
├── config.defaults.yaml     # Default values
├── config.development.yaml  # Development overrides
├── config.staging.yaml      # Staging overrides
├── config.production.yaml   # Production settings
└── config.local.yaml        # Local overrides (git-ignored)

# Load based on environment
ENV=production python orchestrator/orchestrator_agent.py
```

### 2. Secret Management

```yaml
# config.yaml - Use environment variable references
api_keys:
  openai: "${OPENAI_API_KEY}"
  anthropic: "${ANTHROPIC_API_KEY}"
  
database:
  password: "${DB_PASSWORD}"
  
security:
  secret_key: "${SECRET_KEY}"
```

```python
# Use secret management services
from orchestrator.secrets import SecretManager

secrets = SecretManager(provider="aws_secrets_manager")
config.set("api_keys.openai", await secrets.get("openai_api_key"))
```

### 3. Configuration Validation

```python
# config_validator.py
from pydantic import BaseModel, validator
from typing import Optional, List

class ServerConfig(BaseModel):
    host: str = "localhost"
    port: int = 8080
    workers: int = 4
    
    @validator('port')
    def port_range(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError('Port must be between 1 and 65535')
        return v
        
    @validator('workers')
    def workers_range(cls, v):
        if not 1 <= v <= 100:
            raise ValueError('Workers must be between 1 and 100')
        return v

class OrchestratorConfig(BaseModel):
    server: ServerConfig
    agents: dict
    workflows: dict
    
    def validate_config(self):
        """Validate complete configuration"""
        # Check required fields
        if not self.agents:
            raise ValueError("No agents configured")
            
        # Validate agent configurations
        for agent_name, agent_config in self.agents.items():
            self._validate_agent_config(agent_name, agent_config)
            
    def _validate_agent_config(self, name: str, config: dict):
        required_fields = ["timeout", "retries"]
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Agent {name} missing required field: {field}")
```

### 4. Hot Reload Configuration

```python
# config_watcher.py
import asyncio
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ConfigReloader(FileSystemEventHandler):
    def __init__(self, config_manager):
        self.config_manager = config_manager
        
    def on_modified(self, event):
        if event.src_path.endswith('.yaml'):
            asyncio.create_task(self.reload_config())
            
    async def reload_config(self):
        """Reload configuration without restart"""
        try:
            new_config = load_config_file(self.config_path)
            validate_config(new_config)
            
            # Apply non-critical changes
            await self.config_manager.apply_changes(new_config)
            
            logger.info("Configuration reloaded successfully")
        except Exception as e:
            logger.error(f"Failed to reload config: {e}")

# Start watching config file
observer = Observer()
observer.schedule(ConfigReloader(config_manager), path='config/', recursive=False)
observer.start()
```

## Configuration Templates

### Minimal Configuration

```yaml
# config.minimal.yaml
api_keys:
  openai: "${OPENAI_API_KEY}"

server:
  orchestrator:
    port: 8080
  api:
    port: 8000

workflows:
  defaults:
    output_directory: "./generated"
```

### Development Configuration

```yaml
# config.development.yaml
system:
  environment: "development"

server:
  orchestrator:
    host: "localhost"
    port: 8080
  api:
    host: "localhost"
    port: 8000
    cors:
      enabled: true
      origins: ["http://localhost:3000"]

logging:
  level: "DEBUG"
  format: "detailed"

agents:
  defaults:
    timeout: 600  # Longer timeouts for debugging

workflows:
  defaults:
    save_intermediate: true
    enable_caching: false  # Disable caching for development

security:
  authentication:
    enabled: false  # Disable auth for local development
```

### Production Configuration

```yaml
# config.production.yaml
system:
  environment: "production"

server:
  orchestrator:
    host: "0.0.0.0"
    port: 8080
    workers: 8
  api:
    host: "0.0.0.0"
    port: 8000
    cors:
      enabled: true
      origins: ["https://app.yourdomain.com"]
    rate_limit:
      enabled: true
      calls: 100
      period: 60

logging:
  level: "WARNING"
  outputs:
    - type: "syslog"
      host: "log-aggregator.internal"

storage:
  type: "s3"
  s3:
    bucket: "prod-orchestrator-storage"

monitoring:
  metrics:
    enabled: true
  tracing:
    enabled: true

security:
  authentication:
    enabled: true
  encryption:
    enabled: true
  audit:
    enabled: true
```

## Troubleshooting Configuration

### Common Issues

1. **Missing Environment Variables**
   ```bash
   # Check all required env vars
   python scripts/check_config.py
   
   # Set missing variables
   export OPENAI_API_KEY="your-key"
   ```

2. **Configuration File Not Found**
   ```bash
   # Specify config file path
   python orchestrator/orchestrator_agent.py --config /path/to/config.yaml
   
   # Or set via environment
   export ORCHESTRATOR_CONFIG=/path/to/config.yaml
   ```

3. **Invalid Configuration Values**
   ```bash
   # Validate configuration
   python scripts/validate_config.py config.yaml
   
   # Show configuration schema
   python scripts/show_config_schema.py
   ```

4. **Permission Issues**
   ```bash
   # Check file permissions
   ls -la config/
   
   # Fix permissions
   chmod 644 config/*.yaml
   ```

## Related Documentation

- [Environment Variables](../reference/environment-variables.md)
- [Workflow Configuration](../reference/workflow-configuration.md)
- [Security Guide](security.md)
- [Deployment Guide](deployment.md)