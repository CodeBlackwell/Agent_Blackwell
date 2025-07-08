# Plugin System Guide

## Overview

The Multi-Agent Orchestrator Plugin System allows developers to extend the functionality of the orchestrator without modifying core code. Plugins can add new agents, workflows, API endpoints, and integrations while maintaining system stability and modularity.

## Plugin Architecture

### Core Concepts

1. **Plugin Interface**: Standardized contract for plugin integration
2. **Plugin Manager**: Discovers, loads, and manages plugins
3. **Hook System**: Extension points throughout the application
4. **Plugin Registry**: Central repository of available plugins

### Plugin Structure

```
plugins/
└── your_plugin/
    ├── __init__.py
    ├── plugin.yaml          # Plugin metadata
    ├── main.py             # Entry point
    ├── requirements.txt    # Dependencies
    ├── agents/            # Custom agents
    ├── workflows/         # Custom workflows
    ├── api/              # API extensions
    └── tests/            # Plugin tests
```

## Creating a Plugin

### Step 1: Define Plugin Metadata

```yaml
# plugin.yaml
name: your-plugin
version: 1.0.0
description: Description of your plugin
author: Your Name
email: your.email@example.com

# Plugin capabilities
provides:
  agents:
    - name: custom_agent
      class: agents.CustomAgent
  workflows:
    - name: custom_workflow
      class: workflows.CustomWorkflow
  api_endpoints:
    - path: /custom/endpoint
      router: api.custom_router
  hooks:
    - name: pre_workflow_execution
      handler: hooks.pre_workflow_handler

# Dependencies
requires:
  python: ">=3.10"
  packages:
    - fastapi>=0.68.0
    - pydantic>=1.8.0

# Configuration schema
config_schema:
  type: object
  properties:
    api_key:
      type: string
      description: API key for external service
    timeout:
      type: integer
      default: 30
      description: Request timeout in seconds
```

### Step 2: Implement Plugin Interface

```python
# main.py
from typing import Dict, Any, List
from plugins.base import BasePlugin, PluginMetadata

class YourPlugin(BasePlugin):
    """Main plugin class"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        self.config = config
        self.metadata = PluginMetadata(
            name="your-plugin",
            version="1.0.0",
            description="Your plugin description"
        )
        
    async def initialize(self) -> None:
        """Initialize plugin resources"""
        # Set up connections, load resources, etc.
        self.logger.info(f"Initializing {self.metadata.name}")
        await self._setup_resources()
        
    async def shutdown(self) -> None:
        """Clean up plugin resources"""
        self.logger.info(f"Shutting down {self.metadata.name}")
        await self._cleanup_resources()
        
    def get_agents(self) -> Dict[str, Any]:
        """Return custom agents provided by this plugin"""
        from .agents import CustomAgent
        return {
            "custom_agent": CustomAgent
        }
        
    def get_workflows(self) -> Dict[str, Any]:
        """Return custom workflows provided by this plugin"""
        from .workflows import CustomWorkflow
        return {
            "custom_workflow": CustomWorkflow
        }
        
    def get_api_routers(self) -> List[Any]:
        """Return API routers for additional endpoints"""
        from .api import custom_router
        return [custom_router]
        
    def register_hooks(self, hook_manager: Any) -> None:
        """Register plugin hooks"""
        from .hooks import pre_workflow_handler, post_workflow_handler
        
        hook_manager.register("pre_workflow_execution", pre_workflow_handler)
        hook_manager.register("post_workflow_execution", post_workflow_handler)
```

### Step 3: Implement Plugin Components

#### Custom Agent

```python
# agents/custom_agent.py
from typing import AsyncGenerator
from agents.base_agent import BaseAgent

class CustomAgent(BaseAgent):
    """Custom agent implementation"""
    
    def __init__(self):
        super().__init__(
            name="custom_agent",
            role="Specialized custom processing"
        )
        
    async def _execute_task(self, request: dict) -> AsyncGenerator[str, None]:
        """Execute custom agent logic"""
        yield "Starting custom processing...\n"
        
        # Your custom logic here
        result = await self._process_custom_task(request)
        
        yield f"Custom result: {result}\n"
        yield "Processing complete!\n"
        
    async def _process_custom_task(self, request: dict) -> str:
        # Implement your custom processing
        return "Custom task completed"
```

#### Custom Workflow

```python
# workflows/custom_workflow.py
from typing import Dict, Any, AsyncGenerator
from workflows.base_workflow import BaseWorkflow

class CustomWorkflow(BaseWorkflow):
    """Custom workflow implementation"""
    
    def __init__(self):
        super().__init__({
            "name": "custom_workflow",
            "description": "Custom workflow for specific tasks",
            "agents": ["planner_agent", "custom_agent", "reviewer_agent"]
        })
        
    async def execute(
        self, 
        requirements: str, 
        config: Dict[str, Any] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute custom workflow"""
        
        # Planning phase
        yield {"type": "phase_start", "phase": "planning"}
        plan = await self._run_agent("planner_agent", {
            "task": f"Plan: {requirements}",
            "context": {}
        })
        yield {"type": "phase_complete", "phase": "planning", "result": plan}
        
        # Custom processing phase
        yield {"type": "phase_start", "phase": "custom_processing"}
        result = await self._run_agent("custom_agent", {
            "task": requirements,
            "context": {"plan": plan}
        })
        yield {"type": "phase_complete", "phase": "custom_processing", "result": result}
        
        # Review phase
        yield {"type": "phase_start", "phase": "review"}
        review = await self._run_agent("reviewer_agent", {
            "task": "Review the custom processing",
            "context": {"result": result}
        })
        yield {"type": "phase_complete", "phase": "review", "result": review}
        
        # Final result
        yield {
            "type": "final_result",
            "status": "completed",
            "results": {
                "plan": plan,
                "custom_result": result,
                "review": review
            }
        }
```

#### API Extensions

```python
# api/custom_endpoints.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

router = APIRouter(prefix="/custom", tags=["custom-plugin"])

class CustomRequest(BaseModel):
    data: str
    options: Dict[str, Any] = {}

class CustomResponse(BaseModel):
    result: str
    metadata: Dict[str, Any]

@router.post("/process", response_model=CustomResponse)
async def process_custom_data(request: CustomRequest):
    """Process data using custom plugin logic"""
    try:
        # Process using plugin logic
        result = await process_with_plugin(request.data, request.options)
        
        return CustomResponse(
            result=result,
            metadata={"processed_by": "custom-plugin"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_plugin_status():
    """Get custom plugin status"""
    return {
        "plugin": "custom-plugin",
        "status": "active",
        "version": "1.0.0"
    }
```

### Step 4: Implement Hook System

```python
# hooks/workflow_hooks.py
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

async def pre_workflow_handler(context: Dict[str, Any]) -> Dict[str, Any]:
    """Handler called before workflow execution"""
    logger.info(f"Pre-workflow hook: {context.get('workflow_type')}")
    
    # Modify context if needed
    context["plugin_metadata"] = {
        "enhanced_by": "custom-plugin",
        "timestamp": datetime.now().isoformat()
    }
    
    # Validate or enhance requirements
    requirements = context.get("requirements", "")
    if "custom" in requirements.lower():
        context["use_custom_agent"] = True
    
    return context

async def post_workflow_handler(context: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
    """Handler called after workflow execution"""
    logger.info(f"Post-workflow hook: {context.get('workflow_type')}")
    
    # Process or enhance results
    if context.get("use_custom_agent"):
        result["custom_enhancement"] = "Applied custom processing"
    
    # Log metrics
    await log_workflow_metrics(context, result)
    
    return result

async def log_workflow_metrics(context: Dict[str, Any], result: Dict[str, Any]):
    """Log workflow execution metrics"""
    metrics = {
        "workflow_type": context.get("workflow_type"),
        "duration": result.get("duration"),
        "success": result.get("status") == "completed",
        "plugin": "custom-plugin"
    }
    # Send to metrics system
    logger.info(f"Workflow metrics: {metrics}")
```

## Plugin Manager

### Core Plugin Manager

```python
# plugins/manager.py
import importlib
import yaml
from pathlib import Path
from typing import Dict, Any, List
import logging

class PluginManager:
    """Manages plugin lifecycle"""
    
    def __init__(self, plugins_dir: str = "plugins"):
        self.plugins_dir = Path(plugins_dir)
        self.plugins: Dict[str, Any] = {}
        self.logger = logging.getLogger(__name__)
        
    async def discover_plugins(self) -> List[str]:
        """Discover available plugins"""
        discovered = []
        
        for plugin_path in self.plugins_dir.iterdir():
            if plugin_path.is_dir() and (plugin_path / "plugin.yaml").exists():
                discovered.append(plugin_path.name)
                
        self.logger.info(f"Discovered plugins: {discovered}")
        return discovered
        
    async def load_plugin(self, plugin_name: str) -> None:
        """Load a single plugin"""
        plugin_path = self.plugins_dir / plugin_name
        
        # Load metadata
        with open(plugin_path / "plugin.yaml") as f:
            metadata = yaml.safe_load(f)
            
        # Import plugin module
        spec = importlib.util.spec_from_file_location(
            f"plugins.{plugin_name}",
            plugin_path / "main.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Get plugin class
        plugin_class = getattr(module, metadata.get("class", "Plugin"))
        
        # Instantiate plugin
        config = self._load_plugin_config(plugin_name)
        plugin_instance = plugin_class(config)
        
        # Initialize plugin
        await plugin_instance.initialize()
        
        # Store plugin
        self.plugins[plugin_name] = {
            "instance": plugin_instance,
            "metadata": metadata,
            "module": module
        }
        
        self.logger.info(f"Loaded plugin: {plugin_name}")
        
    async def load_all_plugins(self) -> None:
        """Load all discovered plugins"""
        plugins = await self.discover_plugins()
        
        for plugin_name in plugins:
            try:
                await self.load_plugin(plugin_name)
            except Exception as e:
                self.logger.error(f"Failed to load plugin {plugin_name}: {e}")
                
    def get_plugin(self, plugin_name: str) -> Any:
        """Get loaded plugin instance"""
        plugin_data = self.plugins.get(plugin_name)
        return plugin_data["instance"] if plugin_data else None
        
    def get_all_agents(self) -> Dict[str, Any]:
        """Get all agents from all plugins"""
        agents = {}
        
        for plugin_name, plugin_data in self.plugins.items():
            plugin_agents = plugin_data["instance"].get_agents()
            agents.update(plugin_agents)
            
        return agents
        
    def get_all_workflows(self) -> Dict[str, Any]:
        """Get all workflows from all plugins"""
        workflows = {}
        
        for plugin_name, plugin_data in self.plugins.items():
            plugin_workflows = plugin_data["instance"].get_workflows()
            workflows.update(plugin_workflows)
            
        return workflows
        
    async def shutdown_all(self) -> None:
        """Shutdown all plugins"""
        for plugin_name, plugin_data in self.plugins.items():
            try:
                await plugin_data["instance"].shutdown()
                self.logger.info(f"Shutdown plugin: {plugin_name}")
            except Exception as e:
                self.logger.error(f"Error shutting down plugin {plugin_name}: {e}")
```

### Plugin Configuration

```python
# plugins/config.py
from typing import Dict, Any
import os
import json

class PluginConfig:
    """Plugin configuration management"""
    
    def __init__(self, config_dir: str = "config/plugins"):
        self.config_dir = config_dir
        os.makedirs(config_dir, exist_ok=True)
        
    def load_config(self, plugin_name: str) -> Dict[str, Any]:
        """Load plugin configuration"""
        config_file = os.path.join(self.config_dir, f"{plugin_name}.json")
        
        if os.path.exists(config_file):
            with open(config_file) as f:
                return json.load(f)
                
        # Return default config
        return self._get_default_config(plugin_name)
        
    def save_config(self, plugin_name: str, config: Dict[str, Any]) -> None:
        """Save plugin configuration"""
        config_file = os.path.join(self.config_dir, f"{plugin_name}.json")
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
            
    def _get_default_config(self, plugin_name: str) -> Dict[str, Any]:
        """Get default configuration for plugin"""
        defaults = {
            "enabled": True,
            "log_level": "INFO",
            "timeout": 30
        }
        return defaults
```

## Plugin Development Best Practices

### 1. Error Handling

```python
class RobustPlugin(BasePlugin):
    async def initialize(self) -> None:
        """Initialize with proper error handling"""
        try:
            await self._connect_to_service()
            self.logger.info("Plugin initialized successfully")
        except ConnectionError as e:
            self.logger.error(f"Failed to connect: {e}")
            # Graceful degradation
            self.degraded_mode = True
        except Exception as e:
            self.logger.error(f"Initialization failed: {e}")
            raise PluginInitializationError(f"Cannot initialize plugin: {e}")
```

### 2. Resource Management

```python
class ResourceAwarePlugin(BasePlugin):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.resources = []
        self.cleanup_tasks = []
        
    async def initialize(self) -> None:
        """Initialize resources"""
        # Create connection pool
        self.db_pool = await create_pool(
            max_connections=self.config.get("max_connections", 10)
        )
        self.resources.append(self.db_pool)
        
        # Start background tasks
        task = asyncio.create_task(self._background_sync())
        self.cleanup_tasks.append(task)
        
    async def shutdown(self) -> None:
        """Clean up all resources"""
        # Cancel background tasks
        for task in self.cleanup_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
                
        # Close resources
        for resource in self.resources:
            if hasattr(resource, 'close'):
                await resource.close()
```

### 3. Plugin Testing

```python
# tests/test_plugin.py
import pytest
from plugins.your_plugin.main import YourPlugin

@pytest.fixture
async def plugin():
    """Create plugin instance for testing"""
    config = {
        "api_key": "test_key",
        "timeout": 10
    }
    plugin = YourPlugin(config)
    await plugin.initialize()
    yield plugin
    await plugin.shutdown()

@pytest.mark.asyncio
async def test_plugin_initialization(plugin):
    """Test plugin initializes correctly"""
    assert plugin.metadata.name == "your-plugin"
    assert plugin.config["api_key"] == "test_key"

@pytest.mark.asyncio
async def test_custom_agent(plugin):
    """Test custom agent functionality"""
    agents = plugin.get_agents()
    assert "custom_agent" in agents
    
    # Test agent execution
    agent = agents["custom_agent"]()
    request = {"task": "test task", "context": {}}
    
    responses = []
    async for response in agent.process_request(request):
        responses.append(response)
        
    assert len(responses) > 0
    assert "complete" in responses[-1].lower()
```

### 4. Plugin Documentation

```markdown
# Your Plugin Documentation

## Overview
Brief description of what your plugin does.

## Installation
```bash
# Copy plugin to plugins directory
cp -r your-plugin /path/to/orchestrator/plugins/

# Install dependencies
pip install -r plugins/your-plugin/requirements.txt
```

## Configuration
```json
{
  "api_key": "your-api-key",
  "timeout": 30,
  "retry_attempts": 3
}
```

## Usage

### Using Custom Agent
```python
result = await orchestrator.run_agent("custom_agent", {
    "task": "Process this data",
    "options": {"format": "json"}
})
```

### Using Custom Workflow
```python
result = await orchestrator.execute_workflow(
    requirements="Build a custom solution",
    workflow_type="custom_workflow"
)
```

## API Endpoints
- `POST /custom/process` - Process custom data
- `GET /custom/status` - Get plugin status

## Troubleshooting
Common issues and solutions.
```

## Plugin Distribution

### 1. Package Structure

```
your-plugin-package/
├── setup.py
├── README.md
├── LICENSE
├── requirements.txt
└── your_plugin/
    ├── __init__.py
    ├── plugin.yaml
    ├── main.py
    └── ...
```

### 2. Setup Script

```python
# setup.py
from setuptools import setup, find_packages

setup(
    name="orchestrator-your-plugin",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Your plugin for Multi-Agent Orchestrator",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/your-plugin",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "fastapi>=0.68.0",
        "pydantic>=1.8.0",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.10",
    entry_points={
        "orchestrator.plugins": [
            "your_plugin = your_plugin.main:YourPlugin",
        ],
    },
)
```

### 3. Plugin Registry

Register your plugin in the community registry:

```yaml
# plugin-registry.yaml
plugins:
  - name: your-plugin
    description: Brief description
    author: Your Name
    repository: https://github.com/yourusername/your-plugin
    version: 1.0.0
    compatibility:
      orchestrator: ">=2.0.0"
    tags:
      - custom-processing
      - api-integration
```

## Security Considerations

### 1. Plugin Sandboxing

```python
# plugins/sandbox.py
import resource
import signal
from contextlib import contextmanager

@contextmanager
def sandbox_plugin(memory_limit_mb: int = 512, cpu_time_limit: int = 30):
    """Sandbox plugin execution"""
    # Set memory limit
    resource.setrlimit(
        resource.RLIMIT_AS,
        (memory_limit_mb * 1024 * 1024, memory_limit_mb * 1024 * 1024)
    )
    
    # Set CPU time limit
    def timeout_handler(signum, frame):
        raise TimeoutError("Plugin execution timeout")
        
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(cpu_time_limit)
    
    try:
        yield
    finally:
        signal.alarm(0)
```

### 2. Permission System

```python
# plugins/permissions.py
from enum import Enum
from typing import Set

class PluginPermission(Enum):
    READ_WORKFLOW = "read_workflow"
    WRITE_WORKFLOW = "write_workflow"
    EXECUTE_AGENT = "execute_agent"
    ACCESS_API = "access_api"
    MODIFY_CONFIG = "modify_config"

class PluginPermissionManager:
    def __init__(self):
        self.permissions: Dict[str, Set[PluginPermission]] = {}
        
    def grant_permission(self, plugin_name: str, permission: PluginPermission):
        if plugin_name not in self.permissions:
            self.permissions[plugin_name] = set()
        self.permissions[plugin_name].add(permission)
        
    def check_permission(self, plugin_name: str, permission: PluginPermission) -> bool:
        return permission in self.permissions.get(plugin_name, set())
        
    def require_permission(self, permission: PluginPermission):
        """Decorator to check permissions"""
        def decorator(func):
            async def wrapper(plugin_instance, *args, **kwargs):
                if not self.check_permission(plugin_instance.metadata.name, permission):
                    raise PermissionError(f"Plugin lacks permission: {permission.value}")
                return await func(plugin_instance, *args, **kwargs)
            return wrapper
        return decorator
```

## Related Documentation

- [Architecture Overview](architecture/README.md)
- [Agent Development](agent-development.md)
- [Workflow Development](workflow-development.md)
- [API Development](api-development.md)
- [Plugin API Reference](../reference/plugin-api.md)