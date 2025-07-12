"""Base configuration class with common settings."""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from pathlib import Path
import os


@dataclass
class BaseConfig:
    """Base configuration class with common settings."""
    
    # Application settings
    app_name: str = "Multi-Agent Orchestrator"
    version: str = "0.1.0"
    debug: bool = field(default_factory=lambda: os.getenv('DEBUG', 'False').lower() == 'true')
    
    # Paths
    project_root: Path = field(default_factory=lambda: Path(__file__).parent.parent)
    logs_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent / "logs")
    reports_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent / "reports")
    temp_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent / "temp")
    
    # API settings
    api_host: str = field(default_factory=lambda: os.getenv('API_HOST', '127.0.0.1'))
    api_port: int = field(default_factory=lambda: int(os.getenv('API_PORT', '8000')))
    api_debug: bool = field(default_factory=lambda: os.getenv('API_DEBUG', 'False').lower() == 'true')
    
    # Agent settings
    agent_timeout: int = field(default_factory=lambda: int(os.getenv('AGENT_TIMEOUT', '300')))
    max_retries: int = field(default_factory=lambda: int(os.getenv('MAX_RETRIES', '3')))
    retry_delay: int = field(default_factory=lambda: int(os.getenv('RETRY_DELAY', '5')))
    
    # LLM settings
    llm_model: str = field(default_factory=lambda: os.getenv('LLM_MODEL', 'gpt-4'))
    llm_temperature: float = field(default_factory=lambda: float(os.getenv('LLM_TEMPERATURE', '0.7')))
    llm_max_tokens: int = field(default_factory=lambda: int(os.getenv('LLM_MAX_TOKENS', '4000')))
    
    # Logging settings
    log_level: str = field(default_factory=lambda: os.getenv('LOG_LEVEL', 'INFO'))
    log_format: str = field(default_factory=lambda: os.getenv(
        'LOG_FORMAT', 
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    log_rotation: str = field(default_factory=lambda: os.getenv('LOG_ROTATION', '10MB'))
    log_retention: int = field(default_factory=lambda: int(os.getenv('LOG_RETENTION', '30')))
    
    # Performance settings
    enable_caching: bool = field(default_factory=lambda: os.getenv('ENABLE_CACHING', 'True').lower() == 'true')
    cache_ttl: int = field(default_factory=lambda: int(os.getenv('CACHE_TTL', '3600')))
    max_concurrent_agents: int = field(default_factory=lambda: int(os.getenv('MAX_CONCURRENT_AGENTS', '5')))
    
    def __post_init__(self):
        """Ensure directories exist."""
        for dir_path in [self.logs_dir, self.reports_dir, self.temp_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            k: str(v) if isinstance(v, Path) else v
            for k, v in self.__dict__.items()
        }
    
    def update_from_dict(self, config_dict: Dict[str, Any]) -> None:
        """Update configuration from dictionary."""
        for key, value in config_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)