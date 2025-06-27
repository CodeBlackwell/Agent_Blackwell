"""
Real-time streaming API module.

This module provides WebSocket endpoints for real-time job and task status streaming.
"""

from .router import initialize_streaming_service, router, shutdown_streaming_service

__all__ = ["router", "initialize_streaming_service", "shutdown_streaming_service"]
