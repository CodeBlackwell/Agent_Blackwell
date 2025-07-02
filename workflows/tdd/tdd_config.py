# workflows/tdd/tdd_config.py
"""
Configuration for the enhanced TDD workflow
"""

# Retry logic configuration
RETRY_CONFIG = {
    "max_total_retries": 10,               # Absolute limit on retry attempts
    "max_retries_without_progress": 3,     # Max retries at same test pass level
    "enable_retry_logic": True,            # Toggle retry logic on/off
}

# Test execution configuration  
TEST_CONFIG = {
    "default_test_count": 10,              # Default number of tests if not detected
    "min_pass_threshold": 0.8,             # Minimum pass rate to consider successful (80%)
    "execute_real_tests": False,           # Toggle between simulation and real test execution
}

# Review configuration
REVIEW_CONFIG = {
    "require_reviews": True,               # Toggle reviewer intermediary on/off
    "review_timeout": 300,                 # Timeout for review in seconds
    "allow_review_override": False,        # Allow proceeding without review approval
}

# Workflow configuration
WORKFLOW_CONFIG = {
    "verbose_logging": True,               # Detailed logging of workflow steps
    "save_intermediate_results": True,     # Save results after each phase
    "parallel_reviews": False,             # Run reviews in parallel (experimental)
}