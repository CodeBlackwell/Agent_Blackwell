"""
MCP Configuration

Central configuration for all MCP (Model Context Protocol) servers and clients
used in the multi-agent system.
"""

import os
from pathlib import Path

# Base configuration directory
CONFIG_DIR = Path(__file__).parent
PROJECT_ROOT = CONFIG_DIR.parent

# MCP File System Server Configuration
MCP_FILESYSTEM_CONFIG = {
    # Sandbox root directory - all file operations are restricted to this path
    "sandbox_root": os.getenv("MCP_FILESYSTEM_SANDBOX", str(PROJECT_ROOT / "generated")),
    
    # Audit log location
    "audit_log_path": os.getenv("MCP_FILESYSTEM_AUDIT_LOG", str(PROJECT_ROOT / "logs" / "mcp_filesystem_audit.log")),
    
    # Permission configuration
    "permissions": {
        # Agent-specific permissions
        "agents": {
            "coder_agent": ["read", "write", "create", "delete"],
            "executor_agent": ["read", "write", "create"],
            "validator_agent": ["read"],
            "test_writer_agent": ["read", "write", "create"],
            "reviewer_agent": ["read"],
            "planner_agent": ["read"],
            "designer_agent": ["read"],
            "feature_coder_agent": ["read", "write", "create", "delete"],
            "feature_reviewer_agent": ["read"]
        },
        
        # Path-specific restrictions
        "path_restrictions": {
            # Paths that should be read-only for all agents
            "read_only_paths": [
                "configs/",
                "templates/"
            ],
            
            # Paths that should never be accessible
            "forbidden_paths": [
                ".git/",
                ".env",
                "secrets/",
                "*.key",
                "*.pem"
            ]
        },
        
        # File type restrictions
        "allowed_extensions": [
            ".py", ".js", ".ts", ".jsx", ".tsx",
            ".json", ".yaml", ".yml", ".toml",
            ".md", ".txt", ".rst",
            ".html", ".css", ".scss", ".sass",
            ".sh", ".bash", ".zsh",
            ".dockerfile", ".dockerignore",
            ".gitignore", ".editorconfig",
            ".xml", ".csv"
        ]
    },
    
    # Operation limits
    "limits": {
        # Maximum file size for read/write operations (in bytes)
        "max_file_size": 10 * 1024 * 1024,  # 10MB
        
        # Maximum number of files in a single directory listing
        "max_list_items": 1000,
        
        # Maximum directory depth for recursive operations
        "max_recursion_depth": 10
    },
    
    # Performance settings
    "performance": {
        # Enable caching for read operations
        "enable_read_cache": True,
        
        # Cache TTL in seconds
        "cache_ttl": 300,  # 5 minutes
        
        # Maximum cache size in MB
        "max_cache_size": 100
    },
    
    # Server settings
    "server": {
        # Server host and port
        "host": os.getenv("MCP_FILESYSTEM_HOST", "localhost"),
        "port": int(os.getenv("MCP_FILESYSTEM_PORT", "8090")),
        
        # Connection timeout in seconds
        "timeout": 30,
        
        # Maximum concurrent connections
        "max_connections": 50
    }
}

# MCP Git Tools Server Configuration
MCP_GIT_CONFIG = {
    # GitHub configuration
    "github": {
        "token": os.getenv("GITHUB_TOKEN"),
        "default_branch": "main",
        "pr_template": "templates/pull_request_template.md"
    },
    
    # Repository settings
    "repository": {
        "default_remote": "origin",
        "auto_push": False,
        "sign_commits": False
    },
    
    # Server settings
    "server": {
        "host": os.getenv("MCP_GIT_HOST", "localhost"),
        "port": int(os.getenv("MCP_GIT_PORT", "8091")),
        "timeout": 60
    }
}

# MCP Client Configuration (shared by all agents)
MCP_CLIENT_CONFIG = {
    # Connection settings
    "connection": {
        # Retry configuration
        "max_retries": 3,
        "retry_delay": 1.0,  # seconds
        "retry_backoff": 2.0,  # exponential backoff multiplier
        
        # Connection pooling
        "pool_size": 10,
        "pool_timeout": 30
    },
    
    # Error handling
    "error_handling": {
        # Whether to raise exceptions or return error objects
        "raise_on_error": True,
        
        # Error logging
        "log_errors": True,
        "error_log_path": str(PROJECT_ROOT / "logs" / "mcp_client_errors.log")
    },
    
    # Performance monitoring
    "monitoring": {
        # Enable operation metrics
        "enable_metrics": True,
        
        # Metrics export interval (seconds)
        "metrics_interval": 60,
        
        # Slow operation threshold (seconds)
        "slow_operation_threshold": 5.0
    }
}

# Export a function to get agent-specific configuration
def get_agent_config(agent_name: str) -> dict:
    """Get MCP configuration for a specific agent."""
    config = {
        "filesystem": MCP_FILESYSTEM_CONFIG.copy(),
        "git": MCP_GIT_CONFIG.copy(),
        "client": MCP_CLIENT_CONFIG.copy()
    }
    
    # Add agent-specific permissions
    agent_permissions = MCP_FILESYSTEM_CONFIG["permissions"]["agents"].get(agent_name, ["read"])
    config["filesystem"]["agent_permissions"] = agent_permissions
    
    return config