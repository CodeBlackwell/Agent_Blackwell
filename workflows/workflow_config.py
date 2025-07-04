"""
Configuration settings for workflow functionality.
Centralizes all configurable parameters for workflows.
"""

# Review retry settings
MAX_REVIEW_RETRIES = 3  # Maximum number of review attempts before auto-approval

# TDD workflow retry settings
TDD_MAX_TOTAL_RETRIES = 10  # Maximum total retries for test-driven development
TDD_MAX_RETRIES_WITHOUT_PROGRESS = 3  # Maximum retries without progress before giving up

# Incremental execution settings
EXECUTION_CONFIG = {
    "max_retries": 3,
    "timeout": 60,
    "validation_threshold": 0.8
}
