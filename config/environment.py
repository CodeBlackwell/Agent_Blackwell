"""Environment configuration management."""

import os
from enum import Enum
from typing import Optional


class Environment(Enum):
    """Available environments for the application."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"
    
    @classmethod
    def from_string(cls, env_str: str) -> 'Environment':
        """Create Environment from string value."""
        env_str = env_str.lower()
        for env in cls:
            if env.value == env_str:
                return env
        return cls.DEVELOPMENT
    
    @classmethod
    def current(cls) -> 'Environment':
        """Get current environment from environment variable."""
        env_str = os.getenv('ORCHESTRATOR_ENV', 'development')
        return cls.from_string(env_str)