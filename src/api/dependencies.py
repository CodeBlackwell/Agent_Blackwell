"""
Shared dependencies for the API.

This module provides centralized dependency injection for shared resources
like the LangGraph Orchestrator instance across the entire application.
"""

import logging
import os
import sys
from typing import Optional

from fastapi import HTTPException, status

from src.orchestrator.langgraph_orchestrator import LangGraphOrchestrator

# Configure logging
logger = logging.getLogger(__name__)

# Global LangGraph Orchestrator instance (initialized in lifespan)
_orchestrator: Optional[LangGraphOrchestrator] = None


def get_orchestrator() -> LangGraphOrchestrator:
    """
    Get the shared LangGraph Orchestrator instance.

    Returns:
        The shared LangGraph Orchestrator instance.

    Raises:
        HTTPException: If the Orchestrator is not initialized.
    """
    if _orchestrator is None:
        logger.error(
            "LangGraph Orchestrator not initialized. Application must be started properly."
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Service not properly initialized",
        )
    return _orchestrator


async def initialize_orchestrator() -> LangGraphOrchestrator:
    """
    Initialize the global LangGraph Orchestrator instance.

    Should be called during application startup.

    Returns:
        The initialized LangGraph Orchestrator instance.
    """
    global _orchestrator

    # Check if we're in a test environment
    is_test = "pytest" in sys.modules or "unittest" in sys.modules

    # Get configuration from environment variables
    openai_api_key = os.getenv("OPENAI_API_KEY", "test-key" if is_test else None)

    if not openai_api_key and not is_test:
        logger.error("OpenAI API key not found")
        raise ValueError("Configuration error: OpenAI API key missing")

    # Create the LangGraph orchestrator instance
    orchestrator = LangGraphOrchestrator(
        openai_api_key=openai_api_key,
        enable_checkpointing=True,
        max_retries=3
    )

    logger.info(f"Created LangGraph orchestrator instance: {id(orchestrator)}")

    # Set the global instance
    _orchestrator = orchestrator
    return orchestrator


async def shutdown_orchestrator() -> None:
    """
    Clean up the LangGraph Orchestrator instance.

    Should be called during application shutdown.
    """
    global _orchestrator

    # Add any cleanup operations here if needed
    # LangGraph orchestrator handles its own cleanup

    logger.info("Shutting down LangGraph orchestrator")
    _orchestrator = None
