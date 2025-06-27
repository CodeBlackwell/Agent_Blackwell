#!/usr/bin/env python3
"""
Redis Stream Inspector for Agent Blackwell

This tool inspects Redis streams to diagnose task routing issues between
test and production environments.
"""

import asyncio
import json
from datetime import datetime

import redis.asyncio as redis


async def inspect_streams():
    """
    Inspect Redis streams for debugging purposes.
    """
    # Use both potential Redis URLs
    urls = [
        "redis://localhost:6379",  # Test URL
        "redis://localhost:6380",  # Docker test environment
    ]

    # Streams to check - add all potential stream names based on naming conventions
    streams = [
        "test_agent_tasks",
        "agent:tasks",
        "agent_tasks",
        "agent:spec:input",
        "agent:spec_agent:input",
        "agent:design:input",
        "agent:design_agent:input",
        "agent:coding:input",
        "agent:coding_agent:input",
        "agent:review:input",
        "agent:review_agent:input",
        "agent:test:input",
        "agent:test_agent:input",
    ]

    for url in urls:
        print(f"\n\n===== Inspecting Redis at {url} =====")
        try:
            r = redis.from_url(url)
            await r.ping()
            print("✅ Connection successful")

            for stream in streams:
                try:
                    count = await r.xlen(stream)
                    print(f"\n  Stream: {stream} - {count} messages")

                    # Check consumer groups
                    try:
                        groups = await r.xinfo_groups(stream)
                        print(f"  Consumer groups: {len(groups)}")
                        for group in groups:
                            print(
                                f"    - {group.get(b'name', b'').decode()}: "
                                f"{group.get(b'consumers', 0)} consumers, "
                                f"{group.get(b'pending', 0)} pending"
                            )
                    except Exception as e:
                        if "ERR no such key" not in str(e):
                            print(f"  ⚠️ Error checking consumer groups: {e}")

                    if count > 0:
                        # Get last 5 messages
                        messages = await r.xrevrange(stream, count=5)
                        print(f"  Latest messages in {stream}:")
                        for msg_id, msg_data in messages:
                            print(f"    ID: {msg_id.decode()}")
                            # Pretty print data
                            for k, v in msg_data.items():
                                try:
                                    if k == b"task":
                                        task_json = json.loads(v.decode())
                                        print(
                                            f"      {k.decode()}: {json.dumps(task_json, indent=2)}"
                                        )
                                    else:
                                        print(f"      {k.decode()}: {v.decode()}")
                                except Exception:
                                    print(f"      {k}: {v} (binary)")
                except Exception as e:
                    print(f"  ❌ Error inspecting stream {stream}: {e}")
        except Exception as e:
            print(f"❌ Connection failed: {e}")


if __name__ == "__main__":
    asyncio.run(inspect_streams())
