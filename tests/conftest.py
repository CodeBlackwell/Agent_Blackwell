"""Global pytest fixtures for Agent Blackwell test suite.

This file focuses on test-infrastructure concerns that must apply to *all*
test categories (unit, integration, phase suites, etc.).

Currently it ensures **Redis stream isolation** by deleting all known agent
streams before and after every test function.  This guarantees that residual
messages from a previous test cannot influence subsequent ones – a common
source of flaky behaviour in our Redis-backed workflow.

The fixture is *async* and depends on ``pytest-asyncio`` which is already part
of the test stack.  It is scoped at **function** level and set to
``autouse=True`` so individual tests do **not** need to import or reference it
explicitly.
"""
from __future__ import annotations

import asyncio
from typing import List

import pytest
import redis.asyncio as redis

from src.config.settings import get_settings

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_AGENT_TYPES: List[str] = [
    "spec",
    "design",
    "coding",
    "review",
    "test",
]
_STREAM_TYPES: List[str] = ["input", "output"]
_GENERIC_STREAMS: List[str] = [
    "agent_tasks",
    "agent_results",
    "test_agent_tasks",
    "test_agent_results",
]


# ---------------------------------------------------------------------------
# Helper util – this is *not* a fixture by itself so it can be reused in other
# helper modules if necessary.
# ---------------------------------------------------------------------------

async def _purge_all_agent_streams(client: redis.Redis) -> None:  # pragma: no cover
    """Delete all agent-related Redis streams.

    The function attempts deletes but intentionally ignores *any* errors so it
    is safe to call even if some streams have never been created.
    """
    # Canonical / legacy / test-prefixed per-agent streams
    for agent in _AGENT_TYPES:
        for stype in _STREAM_TYPES:
            streams = [
                f"agent:{agent}:{stype}",
                f"agent:{agent}_agent:{stype}",
                f"test_agent:{agent}:{stype}",
            ]
            for stream in streams:
                try:
                    await client.delete(stream)
                except Exception:  # noqa: BLE001
                    # Ignore if the stream does not exist or Redis is unhappy –
                    # we are best-effort here.
                    pass

    # Shared / generic task & result streams
    for stream in _GENERIC_STREAMS:
        try:
            await client.delete(stream)
        except Exception:  # noqa: BLE001
            pass


# ---------------------------------------------------------------------------
# Autouse fixture – executes before *and* after each test function.
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function", autouse=True)
async def clear_redis_streams_between_tests() -> None:  # noqa: D401 – imperative style OK
    """Clear all Redis streams to guarantee test isolation."""
    settings = get_settings("test")
    client: redis.Redis = redis.Redis(
        host=settings.redis.host,
        port=settings.redis.port,
        decode_responses=True,
    )

    try:
        # Purge before the test starts
        await _purge_all_agent_streams(client)
        yield
    finally:
        # Purge again after the test to leave a pristine state
        await _purge_all_agent_streams(client)
        await client.close()
