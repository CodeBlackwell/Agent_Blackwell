"""
Job Management API module.

This module provides REST API endpoints for job and task management in the Agent Blackwell system.
"""

from .router import router

__all__ = ["router"]
