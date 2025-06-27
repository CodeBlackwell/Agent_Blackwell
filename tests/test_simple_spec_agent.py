"""
Simplified version of test_spec_agent.py to isolate the import issue
"""
# Start with absolutely minimal imports and build up
print("Starting import test...")

import pytest

print("✓ pytest imported")

import asyncio

print("✓ asyncio imported")

import json

print("✓ json imported")

from typing import Any, Dict, List

print("✓ typing imported")

from unittest.mock import AsyncMock, MagicMock, patch

print("✓ unittest.mock imported")

# This is the failing import
import redis.asyncio as redis

print("✓ redis.asyncio imported")

from src.config.settings import get_settings

print("✓ src.config.settings imported")

from tests.integration.agents.base import BaseAgentIntegrationTest

print("✓ BaseAgentIntegrationTest imported")

print("All imports successful!")


def test_simple():
    """Simple test"""
    assert True
