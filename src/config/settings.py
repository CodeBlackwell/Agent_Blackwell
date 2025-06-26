"""
Configuration settings factory for Agent Blackwell.

This module provides a configuration factory that allows switching between
different environments (test, staging, production) and toggling between
real and mock services.
"""
import os
from enum import Enum
from functools import lru_cache
from typing import Dict, Optional, Union

from pydantic import BaseModel, Field


class Environment(str, Enum):
    """Supported environments."""

    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"


class RedisConfig(BaseModel):
    """Redis configuration settings."""

    host: str = Field(default="localhost")
    port: int = Field(default=6379)
    use_mock: bool = Field(default=False)


class VectorDBConfig(BaseModel):
    """Vector database (Pinecone or alternative) configuration."""

    api_key: str = Field(default="")
    environment: str = Field(default="us-west1-gcp")
    index_name: str = Field(default="agent-blackwell")
    use_mock: bool = Field(default=False)
    mock_url: Optional[str] = Field(default=None)


class LLMConfig(BaseModel):
    """LLM (OpenAI or alternative) configuration."""

    api_key: str = Field(default="")
    model: str = Field(default="gpt-4")
    use_mock: bool = Field(default=False)
    mock_url: Optional[str] = Field(default=None)


class SlackConfig(BaseModel):
    """Slack API configuration."""

    api_token: Optional[str] = Field(default=None)
    signing_secret: Optional[str] = Field(default=None)
    client_id: Optional[str] = Field(default=None)
    client_secret: Optional[str] = Field(default=None)
    app_id: Optional[str] = Field(default=None)
    use_mock: bool = Field(default=False)


class Settings(BaseModel):
    """Application settings."""

    environment: Environment = Field(default=Environment.PRODUCTION)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    vector_db: VectorDBConfig = Field(default_factory=VectorDBConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    slack: SlackConfig = Field(default_factory=SlackConfig)
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")


class SettingsFactory:
    """Factory for creating and managing application settings."""

    _instances: Dict[Environment, Settings] = {}

    @classmethod
    def create_test_settings(cls) -> Settings:
        """Create settings for test environment."""
        return Settings(
            environment=Environment.TEST,
            redis=RedisConfig(
                host=os.getenv("REDIS_HOST", "redis-test"),
                port=int(os.getenv("REDIS_PORT", "6379")),
                use_mock=False,  # Redis is lightweight enough to use real instance
            ),
            vector_db=VectorDBConfig(
                api_key="test-api-key",
                index_name="test-index",
                use_mock=True,
                mock_url=os.getenv("VECTOR_DB_URL", "http://mock-vector-db:5001"),
            ),
            llm=LLMConfig(
                api_key=os.getenv("OPENAI_API_KEY", "test-api-key"),
                model="gpt-3.5-turbo",  # Use cheaper model for tests
                use_mock=True,
                mock_url=os.getenv("MOCK_API_URL", "http://mockapi:8080"),
            ),
            slack=SlackConfig(use_mock=True),
            debug=True,
            log_level="DEBUG",
        )

    @classmethod
    def create_staging_settings(cls) -> Settings:
        """Create settings for staging environment."""
        return Settings(
            environment=Environment.STAGING,
            redis=RedisConfig(
                host=os.getenv("REDIS_HOST", "redis"),
                port=int(os.getenv("REDIS_PORT", "6379")),
            ),
            vector_db=VectorDBConfig(
                api_key=os.getenv("PINECONE_API_KEY", ""), index_name="staging-index"
            ),
            llm=LLMConfig(
                api_key=os.getenv("OPENAI_API_KEY", ""),
                model="gpt-3.5-turbo",  # Use cheaper model for staging
            ),
            slack=SlackConfig(
                api_token=os.getenv("SLACK_API_TOKEN"),
                signing_secret=os.getenv("SLACK_SIGNING_SECRET"),
                client_id=os.getenv("SLACK_CLIENT_ID"),
                client_secret=os.getenv("SLACK_CLIENT_SECRET"),
                app_id=os.getenv("SLACK_APP_ID"),
            ),
            debug=True,
            log_level="INFO",
        )

    @classmethod
    def create_production_settings(cls) -> Settings:
        """Create settings for production environment."""
        return Settings(
            environment=Environment.PRODUCTION,
            redis=RedisConfig(
                host=os.getenv("REDIS_HOST", "redis"),
                port=int(os.getenv("REDIS_PORT", "6379")),
            ),
            vector_db=VectorDBConfig(
                api_key=os.getenv("PINECONE_API_KEY", ""),
                index_name=os.getenv("PINECONE_INDEX", "agent-blackwell"),
            ),
            llm=LLMConfig(
                api_key=os.getenv("OPENAI_API_KEY", ""),
                model=os.getenv("OPENAI_MODEL", "gpt-4"),
            ),
            slack=SlackConfig(
                api_token=os.getenv("SLACK_API_TOKEN"),
                signing_secret=os.getenv("SLACK_SIGNING_SECRET"),
                client_id=os.getenv("SLACK_CLIENT_ID"),
                client_secret=os.getenv("SLACK_CLIENT_SECRET"),
                app_id=os.getenv("SLACK_APP_ID"),
            ),
            debug=False,
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )

    @classmethod
    def get_settings(cls, env: Optional[Union[Environment, str]] = None) -> Settings:
        """
        Get settings for the specified environment.

        If no environment is specified, it will use the ENVIRONMENT env var,
        defaulting to production if not set.
        """
        if env is None:
            env_str = os.getenv("ENVIRONMENT", "production").lower()
            try:
                env = Environment(env_str)
            except ValueError:
                env = Environment.PRODUCTION
        elif isinstance(env, str):
            try:
                env = Environment(env.lower())
            except ValueError:
                env = Environment.PRODUCTION

        if env not in cls._instances:
            if env == Environment.TEST:
                settings = cls.create_test_settings()
            elif env == Environment.STAGING:
                settings = cls.create_staging_settings()
            else:
                settings = cls.create_production_settings()

            cls._instances[env] = settings

        return cls._instances[env]

    @classmethod
    def reset(cls) -> None:
        """Reset all cached settings instances."""
        cls._instances.clear()


@lru_cache()
def get_settings(env: Optional[Union[Environment, str]] = None) -> Settings:
    """
    Get application settings.

    This is the main function to use throughout the application.
    It's cached to avoid recreating settings objects unnecessarily.
    """
    return SettingsFactory.get_settings(env)
