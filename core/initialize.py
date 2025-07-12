"""Initialize core infrastructure components."""

import logging
from typing import Optional

from config.config_manager import get_config_manager, get_config
from config.base_config import BaseConfig
from .logging_config import setup_logging, get_logger
from .container import get_container
from .providers import OrchestratorProvider, WorkflowProvider
from .agent_registry import initialize_default_configs
from .exceptions import get_error_handler


logger: Optional[logging.Logger] = None


def initialize_core(config: Optional[BaseConfig] = None) -> None:
    """Initialize all core infrastructure components."""
    global logger
    
    # Load configuration
    if config is None:
        config = get_config()
    
    # Setup logging first
    setup_logging(config)
    logger = get_logger(__name__)
    logger.info("Initializing core infrastructure...")
    
    # Initialize agent configurations
    logger.info("Initializing agent configurations...")
    initialize_default_configs()
    
    # Initialize dependency injection container
    logger.info("Setting up dependency injection container...")
    container = get_container()
    
    # Register providers (they'll be initialized later with actual instances)
    orchestrator_provider = OrchestratorProvider()
    workflow_provider = WorkflowProvider()
    
    # Initialize error handler
    logger.info("Initializing error handler...")
    error_handler = get_error_handler()
    
    logger.info("Core infrastructure initialized successfully")
    
    # Log configuration summary
    logger.debug(f"Configuration: {config.to_dict()}")
    
    return {
        "config": config,
        "container": container,
        "orchestrator_provider": orchestrator_provider,
        "workflow_provider": workflow_provider,
        "error_handler": error_handler
    }


def initialize_orchestrator_integration(orchestrator_agent) -> None:
    """Initialize orchestrator integration with dependency injection."""
    if logger:
        logger.info("Initializing orchestrator integration...")
    
    container = get_container()
    orchestrator_provider = container.resolve(OrchestratorProvider)
    orchestrator_provider.set_orchestrator_agent(orchestrator_agent)
    
    if logger:
        logger.info("Orchestrator integration complete")


def initialize_workflow_integration(workflow_manager) -> None:
    """Initialize workflow manager integration with dependency injection."""
    if logger:
        logger.info("Initializing workflow manager integration...")
    
    container = get_container()
    workflow_provider = container.resolve(WorkflowProvider)
    workflow_provider.set_workflow_manager(workflow_manager)
    
    if logger:
        logger.info("Workflow manager integration complete")


def shutdown_core() -> None:
    """Shutdown core infrastructure components."""
    if logger:
        logger.info("Shutting down core infrastructure...")
    
    # Clear containers and registries
    container = get_container()
    container.clear()
    
    # Clear error history
    error_handler = get_error_handler()
    error_handler.clear_history()
    
    if logger:
        logger.info("Core infrastructure shutdown complete")