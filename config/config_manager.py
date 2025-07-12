"""Configuration manager for handling environment-specific configurations."""

import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Type, TypeVar
from dataclasses import dataclass

from .base_config import BaseConfig
from .environment import Environment


T = TypeVar('T', bound=BaseConfig)


class ConfigManager:
    """Manages configuration loading and access."""
    
    def __init__(self, environment: Optional[Environment] = None):
        """Initialize configuration manager."""
        self.environment = environment or Environment.current()
        self.config_dir = Path(__file__).parent
        self._config_cache: Dict[str, Any] = {}
        self._base_config: Optional[BaseConfig] = None
    
    def load_config(self, config_class: Type[T] = BaseConfig) -> T:
        """Load configuration for current environment."""
        if self._base_config and isinstance(self._base_config, config_class):
            return self._base_config
        
        # Start with base configuration
        config = config_class()
        
        # Load environment-specific configurations
        env_config = self._load_env_config()
        if env_config:
            config.update_from_dict(env_config)
        
        # Load local overrides if they exist
        local_config = self._load_local_config()
        if local_config:
            config.update_from_dict(local_config)
        
        self._base_config = config
        return config
    
    def _load_env_config(self) -> Optional[Dict[str, Any]]:
        """Load environment-specific configuration."""
        env_file = self.config_dir / f"{self.environment.value}.yaml"
        if env_file.exists():
            return self._load_yaml_file(env_file)
        
        env_file = self.config_dir / f"{self.environment.value}.json"
        if env_file.exists():
            return self._load_json_file(env_file)
        
        return None
    
    def _load_local_config(self) -> Optional[Dict[str, Any]]:
        """Load local configuration overrides."""
        local_file = self.config_dir / "local.yaml"
        if local_file.exists():
            return self._load_yaml_file(local_file)
        
        local_file = self.config_dir / "local.json"
        if local_file.exists():
            return self._load_json_file(local_file)
        
        return None
    
    def _load_yaml_file(self, file_path: Path) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        with open(file_path, 'r') as f:
            return yaml.safe_load(f) or {}
    
    def _load_json_file(self, file_path: Path) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        with open(file_path, 'r') as f:
            return json.load(f)
    
    def save_config(self, config: BaseConfig, file_name: str = None) -> None:
        """Save configuration to file."""
        file_name = file_name or f"{self.environment.value}.yaml"
        file_path = self.config_dir / file_name
        
        config_dict = config.to_dict()
        
        if file_path.suffix == '.yaml':
            with open(file_path, 'w') as f:
                yaml.dump(config_dict, f, default_flow_style=False)
        else:
            with open(file_path, 'w') as f:
                json.dump(config_dict, f, indent=2)
    
    def get_workflow_config(self, workflow_name: str) -> Dict[str, Any]:
        """Get configuration for specific workflow."""
        workflow_file = self.config_dir / "workflows" / f"{workflow_name}.yaml"
        if workflow_file.exists():
            return self._load_yaml_file(workflow_file)
        
        # Return default workflow configuration
        return {
            "enabled": True,
            "timeout": 300,
            "max_retries": 3,
            "agents": {}
        }
    
    def validate_config(self, config: BaseConfig) -> bool:
        """Validate configuration values."""
        errors = []
        
        # Validate paths exist
        if not config.project_root.exists():
            errors.append(f"Project root does not exist: {config.project_root}")
        
        # Validate numeric values
        if config.agent_timeout <= 0:
            errors.append("Agent timeout must be positive")
        
        if config.max_retries < 0:
            errors.append("Max retries cannot be negative")
        
        if config.api_port < 1 or config.api_port > 65535:
            errors.append("API port must be between 1 and 65535")
        
        if config.llm_temperature < 0 or config.llm_temperature > 2:
            errors.append("LLM temperature must be between 0 and 2")
        
        if errors:
            raise ValueError(f"Configuration validation errors: {'; '.join(errors)}")
        
        return True


# Global configuration manager instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_config(config_class: Type[T] = BaseConfig) -> T:
    """Get configuration instance."""
    return get_config_manager().load_config(config_class)