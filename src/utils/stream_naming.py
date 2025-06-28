"""Utility functions for standardized Redis stream naming.

This module centralizes logic for deriving Redis stream names based on agent type
and environment (test vs production). It is shared by the orchestrator, agent
workers, and any test utilities to guarantee consistency.
"""
from typing import List

__all__ = [
    "normalize_agent_type",
    "get_agent_type_variants",
    "get_stream_name",
    "get_input_streams",
    "get_result_stream_name",
]


def normalize_agent_type(agent_type: str) -> str:
    """Return the canonical agent type w/o the optional ``_agent`` suffix."""
    if agent_type.endswith("_agent"):
        return agent_type[:-6]
    return agent_type


def get_agent_type_variants(agent_type: str) -> List[str]:
    """Return both canonical and ``_agent``-suffixed variants of *agent_type*.

    Examples
    --------
    >>> get_agent_type_variants("spec")
    ["spec", "spec_agent"]
    >>> get_agent_type_variants("spec_agent")
    ["spec", "spec_agent"]
    """
    canonical = normalize_agent_type(agent_type)
    suffixed = f"{canonical}_agent"
    # Preserve order: canonical first, suffixed second. Use list-dedup.
    return [v for i, v in enumerate([canonical, suffixed]) if v not in [canonical, suffixed][:i]]


def get_stream_name(stream_name: str, is_test_mode: bool) -> str:
    """Return *stream_name* with the proper environment prefix.

    Production streams keep their original name. In test mode we ensure a
    ``test_`` prefix is present exactly once.
    """
    if is_test_mode and not stream_name.startswith("test_"):
        return f"test_{stream_name}"
    if not is_test_mode and stream_name.startswith("test_"):
        return stream_name[5:]
    return stream_name


def get_input_streams(agent_type: str, is_test_mode: bool) -> List[str]:
    """Return the list of input streams an agent worker should consume.

    Canonical format is ``agent:{type}:input``.  For backward-compatibility in
    production we also include the legacy ``agent:{type}_agent:input`` form.
    During tests we only use test-prefixed canonical streams plus the shared
    ``test_agent_tasks`` stream.
    """
    canonical_stream = f"agent:{normalize_agent_type(agent_type)}:input"

    if is_test_mode:
        return [f"test_{canonical_stream}", "test_agent_tasks"]

    legacy_stream = f"agent:{normalize_agent_type(agent_type)}_agent:input"
    return [canonical_stream, legacy_stream]


def get_result_stream_name(base_name: str, is_test_mode: bool) -> str:
    """Return the result stream for the current environment."""
    return get_stream_name(base_name, is_test_mode)
