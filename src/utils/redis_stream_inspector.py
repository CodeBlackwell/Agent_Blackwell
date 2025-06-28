"""Redis Stream Inspector Utility.

This module provides helper functions and a minimal CLI for inspecting Redis
streams used by the Agent Blackwell workflow. It is **read-only** – it never
publishes or mutates data – making it safe for debugging live systems.

Usage (from shell):
    python -m src.utils.redis_stream_inspector --host localhost --port 6379 \
        list-streams

    python -m src.utils.redis_stream_inspector read-stream agent:coding:output \
        --count 5 --start 0-0

All output is JSON-serialised so it can be piped to `jq` or saved for later
analysis.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
from typing import Any, Dict, List, Tuple

import redis.asyncio as redis

logger = logging.getLogger(__name__)

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 6379


async def list_streams(client: redis.Redis) -> List[str]:
    """Return a sorted list of all streams currently present in Redis."""
    # Redis doesn't provide a direct *streams only* command; we list keys with
    # the XINFO command in a pipeline for efficiency.
    keys = await client.keys("*agent*:*")  # narrow down to likely agent streams

    streams: List[str] = []
    for key in keys:
        try:
            info = await client.xinfo_stream(key)
            if info:  # Will raise if key is not a stream
                streams.append(key)
        except redis.ResponseError:
            continue  # Not a stream, ignore
    return sorted(streams)


async def read_stream(
    client: redis.Redis,
    stream_name: str,
    count: int = 10,
    start: str = "0-0",
) -> List[Tuple[str, Dict[str, Any]]]:
    """Read entries from a stream starting at *start*.

    Returns a list of (id, data_dict) tuples (max *count* items).
    """
    entries = await client.xread({stream_name: start}, count=count, block=1_000)
    if not entries:
        return []

    # xread returns list[(stream, [(id, data_dict), ...])]
    _, messages = entries[0]
    parsed: List[Tuple[str, Dict[str, Any]]] = []
    for mid, raw in messages:
        parsed.append((mid, _deserialize_message(raw)))
    return parsed


def _deserialize_message(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Attempt JSON deserialisation of each field, fallback to string."""
    result: Dict[str, Any] = {}
    for k, v in raw.items():
        if isinstance(k, bytes):
            k = k.decode()
        if isinstance(v, bytes):
            v = v.decode()
        try:
            result[k] = json.loads(v)
        except (json.JSONDecodeError, TypeError):
            result[k] = v
    return result


async def _async_main(argv: List[str] | None = None) -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(description="Redis stream inspector")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Redis host")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Redis port")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # list-streams
    subparsers.add_parser("list-streams", help="List all stream keys")

    # read-stream
    read_parser = subparsers.add_parser("read-stream", help="Read entries from a stream")
    read_parser.add_argument("stream", help="Stream name to read")
    read_parser.add_argument("--count", type=int, default=10, help="Number of entries")
    read_parser.add_argument("--start", default="0-0", help="Start ID (default 0-0)")

    args = parser.parse_args(argv)

    client = redis.Redis(host=args.host, port=args.port, decode_responses=False)

    if args.command == "list-streams":
        streams = await list_streams(client)
        print(json.dumps(streams, indent=2))
    elif args.command == "read-stream":
        entries = await read_stream(client, args.stream, args.count, args.start)
        print(json.dumps(entries, indent=2, default=str))

    await client.close()


def main() -> None:  # pragma: no cover
    """Entry point for poetry/console-script style execution."""
    asyncio.run(_async_main())


if __name__ == "__main__":  # pragma: no cover
    main()
