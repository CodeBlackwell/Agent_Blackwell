"""Agent configuration registry to avoid circular imports."""

from typing import Dict, Any, Optional
import threading


class AgentRegistry:
    """Registry for agent configurations."""
    
    def __init__(self):
        """Initialize the registry."""
        self._configs: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
    
    def register(self, agent_name: str, config: Dict[str, Any]) -> None:
        """Register an agent configuration."""
        with self._lock:
            self._configs[agent_name] = config
    
    def get_config(self, agent_name: str) -> Dict[str, Any]:
        """Get an agent configuration."""
        with self._lock:
            if agent_name not in self._configs:
                raise KeyError(f"Agent configuration '{agent_name}' not found")
            return self._configs[agent_name].copy()
    
    def has_config(self, agent_name: str) -> bool:
        """Check if an agent configuration exists."""
        with self._lock:
            return agent_name in self._configs
    
    def list_agents(self) -> list[str]:
        """List all registered agents."""
        with self._lock:
            return list(self._configs.keys())
    
    def update_config(self, agent_name: str, updates: Dict[str, Any]) -> None:
        """Update an agent configuration."""
        with self._lock:
            if agent_name not in self._configs:
                raise KeyError(f"Agent configuration '{agent_name}' not found")
            self._configs[agent_name].update(updates)
    
    def clear(self) -> None:
        """Clear all registered configurations."""
        with self._lock:
            self._configs.clear()


# Global registry instance
_registry: Optional[AgentRegistry] = None
_registry_lock = threading.Lock()


def get_agent_registry() -> AgentRegistry:
    """Get the global agent registry instance."""
    global _registry
    with _registry_lock:
        if _registry is None:
            _registry = AgentRegistry()
        return _registry


def register_agent_config(agent_name: str, config: Dict[str, Any]) -> None:
    """Register an agent configuration in the global registry."""
    registry = get_agent_registry()
    registry.register(agent_name, config)


def get_agent_config(agent_name: str) -> Dict[str, Any]:
    """Get an agent configuration from the global registry."""
    registry = get_agent_registry()
    return registry.get_config(agent_name)


# Initialize default agent configurations
def initialize_default_configs():
    """Initialize default agent configurations."""
    default_configs = {
        "feature_reviewer": {
            "model": "gpt-4",
            "temperature": 0.3,
            "max_tokens": 3000
        },
        "planner_agent": {
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 3000
        },
        "designer_agent": {
            "model": "gpt-4",
            "temperature": 0.6,
            "max_tokens": 3500
        },
        "coder_agent": {
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 4000
        },
        "test_writer_agent": {
            "model": "gpt-4",
            "temperature": 0.3,
            "max_tokens": 3000
        },
        "reviewer_agent": {
            "model": "gpt-4",
            "temperature": 0.4,
            "max_tokens": 2500
        },
        "executor_agent": {
            "model": "gpt-4",
            "temperature": 0.2,
            "max_tokens": 2000
        }
    }
    
    registry = get_agent_registry()
    for agent_name, config in default_configs.items():
        registry.register(agent_name, config)