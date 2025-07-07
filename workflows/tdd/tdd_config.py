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
    "execute_real_tests": True,            # Toggle between simulation and real test execution
    "use_tdd_cycle": True,                 # Use proper red-green-refactor cycle
    "test_before_code": True,              # Ensure tests are run before implementation
    "use_generated_directory": True,       # Run tests in generated project directory vs temp
    "preserve_iterations": False,          # Keep intermediate test results and files
    "test_isolation_mode": "project",      # Options: "project", "temp", "docker"
    "max_iterations": 5,                   # Maximum TDD cycle iterations
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

# Session and directory management configuration
SESSION_CONFIG = {
    "use_single_directory": True,          # Create only one directory per workflow run
    "session_name_prefix": "tdd",          # Prefix for session directories
    "include_timestamp": True,             # Include timestamp in directory name
    "save_metadata": True,                 # Save session metadata file
    "organize_by_feature": False,          # Organize files by feature/component
}