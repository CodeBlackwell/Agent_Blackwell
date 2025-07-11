"""Configuration settings for the flagship TDD orchestrator"""

from models.flagship_models import TDDWorkflowConfig


# Default configuration
DEFAULT_CONFIG = TDDWorkflowConfig(
    max_iterations=5,
    timeout_seconds=300,
    auto_refactor=False,
    verbose_output=True,
    test_framework="pytest",
    test_directory="generated/tests",
    code_directory="generated/src",
    coverage_threshold=80.0,
    strict_tdd=True
)

# Quick test configuration
QUICK_TEST_CONFIG = TDDWorkflowConfig(
    max_iterations=2,
    timeout_seconds=60,
    auto_refactor=False,
    verbose_output=True,
    test_framework="pytest",
    test_directory="generated/tests",
    code_directory="generated/src",
    coverage_threshold=70.0,
    strict_tdd=False
)

# Comprehensive configuration
COMPREHENSIVE_CONFIG = TDDWorkflowConfig(
    max_iterations=10,
    timeout_seconds=600,
    auto_refactor=True,
    verbose_output=True,
    test_framework="pytest",
    test_directory="generated/tests",
    code_directory="generated/src",
    coverage_threshold=90.0,
    strict_tdd=True
)

# Demo configuration (for examples)
DEMO_CONFIG = TDDWorkflowConfig(
    max_iterations=3,
    timeout_seconds=120,
    auto_refactor=False,
    verbose_output=True,
    test_framework="pytest",
    test_directory="Flagship/generated/tests",
    code_directory="Flagship/generated/src",
    coverage_threshold=80.0,
    strict_tdd=True
)


def get_config(config_name: str = "default") -> TDDWorkflowConfig:
    """
    Get a predefined configuration by name
    
    Args:
        config_name: Name of the configuration (default, quick, comprehensive, demo)
        
    Returns:
        The requested configuration
    """
    configs = {
        "default": DEFAULT_CONFIG,
        "quick": QUICK_TEST_CONFIG,
        "comprehensive": COMPREHENSIVE_CONFIG,
        "demo": DEMO_CONFIG
    }
    
    return configs.get(config_name.lower(), DEFAULT_CONFIG)


# Phase-specific settings
PHASE_COLORS = {
    "RED": "\033[91m",      # Red
    "YELLOW": "\033[93m",   # Yellow  
    "GREEN": "\033[92m",    # Green
    "REFACTOR": "\033[94m", # Blue
    "RESET": "\033[0m"      # Reset
}

# Agent response templates
AGENT_PROMPTS = {
    "test_writer": {
        "system": "You are a test writer following TDD principles. Write comprehensive tests that will initially fail.",
        "user_template": "Write failing tests for: {requirements}"
    },
    "coder": {
        "system": "You are a coder following TDD principles. Write the minimal code needed to pass the tests.",
        "user_template": "Write minimal code to pass these tests: {test_code}"
    },
    "test_runner": {
        "system": "You are a test runner. Execute tests and report results clearly.",
        "user_template": "Run these tests against this implementation: {test_code}\n\n{implementation_code}"
    }
}

# Output formatting settings
OUTPUT_SETTINGS = {
    "show_timestamps": True,
    "show_phase_colors": True,
    "show_agent_icons": True,
    "max_output_lines": 100,
    "truncate_long_outputs": True
}

# File naming conventions
FILE_NAMING = {
    "test_prefix": "test_",
    "test_suffix": "_test.py",
    "implementation_suffix": ".py",
    "state_file_prefix": "tdd_state_",
    "log_file_prefix": "tdd_log_"
}

# Server configuration
SERVER_CONFIG = {
    "host": "0.0.0.0",
    "port": 8100,
    "api_prefix": "/api/v1",
    "max_workflows": 100,
    "workflow_timeout": 600,  # 10 minutes
    "enable_cors": True,
    "log_level": "INFO"
}

# Client configuration
CLIENT_CONFIG = {
    "base_url": "http://localhost:8100",
    "timeout": 30,
    "retry_attempts": 3,
    "retry_delay": 1.0
}