"""
Shared dependencies for the API.

This module provides centralized dependency injection for shared resources
like the Orchestrator instance across the entire application.
"""

import logging
import os
import sys
from typing import Optional

from fastapi import HTTPException, status

from src.orchestrator.main import Orchestrator

# Configure logging
logger = logging.getLogger(__name__)

# Global Orchestrator instance (initialized in lifespan)
_orchestrator: Optional[Orchestrator] = None


def get_orchestrator() -> Orchestrator:
    """
    Get the shared Orchestrator instance.

    Returns:
        The shared Orchestrator instance.

    Raises:
        HTTPException: If the Orchestrator is not initialized.
    """
    if _orchestrator is None:
        logger.error(
            "Orchestrator not initialized. Application must be started properly."
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Service not properly initialized",
        )
    return _orchestrator


async def initialize_orchestrator() -> Orchestrator:
    """
    Initialize the global Orchestrator instance.

    Should be called during application startup.

    Returns:
        The initialized Orchestrator instance.
    """
    global _orchestrator

    # Check if we're in a test environment
    is_test = "pytest" in sys.modules or "unittest" in sys.modules

    # Get configuration from environment variables
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    openai_api_key = os.getenv("OPENAI_API_KEY", "test-key" if is_test else None)

    # Only use Pinecone in non-test environments
    pinecone_api_key = None if is_test else os.getenv("PINECONE_API_KEY")
    skip_pinecone_init = is_test

    if not openai_api_key and not is_test:
        logger.error("OpenAI API key not found")
        raise ValueError("Configuration error: OpenAI API key missing")

    # Create the orchestrator instance
    orchestrator = Orchestrator(
        redis_url=redis_url,
        pinecone_api_key=pinecone_api_key,
        openai_api_key=openai_api_key,
        skip_pinecone_init=skip_pinecone_init,
    )

    logger.info(f"Created orchestrator instance: {id(orchestrator)}")

    # Initialize agents in non-test environments
    if not is_test:
        orchestrator.initialize_agents()
        logger.info("Initialized agents")

    # Set the global instance
    _orchestrator = orchestrator
    return orchestrator


async def shutdown_orchestrator() -> None:
    """
    Clean up the Orchestrator instance.

    Should be called during application shutdown.
    """
    global _orchestrator

    # Add any cleanup operations here
    # For example, close Redis connections

    logger.info("Shutting down orchestrator")
    _orchestrator = None
