#!/usr/bin/env python3
"""
Task Enqueue Diagnostic Tool for Agent Blackwell

This tool tests task enqueuing in isolation to diagnose routing issues.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime

# Add project root to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.orchestrator.main import Orchestrator


async def diagnose_task_routing(orchestrator):
    """Run diagnostic tests on task routing configuration."""
    print("\n===== TASK ROUTING DIAGNOSTIC =====")
    print(f"Redis URL: {orchestrator.redis_url}")
    print(f"Task Stream: {orchestrator.task_stream}")
    print(f"Result Stream: {orchestrator.result_stream}")

    # Check Redis connectivity
    try:
        await orchestrator.redis_client.ping()
        print("✅ Redis connection: OK")
    except Exception as e:
        print(f"❌ Redis connection: FAILED - {e}")

    # List registered agents
    print("\nRegistered agents:")
    for agent_type, agent in orchestrator.agents.items():
        print(f"  - {agent_type}: {type(agent).__name__}")

    # Try publishing a test message
    try:
        test_id = await orchestrator.redis_client.xadd(
            orchestrator.task_stream,
            {"diagnostic": "test", "timestamp": str(datetime.now())},
        )
        print(f"\n✅ Test message published: {test_id}")

        # Try to read back the message
        messages = await orchestrator.redis_client.xrevrange(
            orchestrator.task_stream, count=1
        )
        if messages:
            print(f"✅ Successfully read back test message:")
            msg_id, msg_data = messages[0]
            for k, v in msg_data.items():
                if isinstance(v, bytes):
                    print(
                        f"  {k.decode() if isinstance(k, bytes) else k}: {v.decode()}"
                    )
                else:
                    print(f"  {k}: {v}")
    except Exception as e:
        print(f"❌ Test message failed: {e}")

    print("===================================")


async def test_real_enqueue():
    """Test task enqueuing with both test and live configurations."""
    # Set up logging
    logging.basicConfig(
        level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger("orchestrator_debug")

    # Configurations to test
    configs = [
        {
            "name": "Test Config",
            "redis_url": "redis://localhost:6379",
            "task_stream": "test_agent_tasks",
            "result_stream": "test_agent_results",
        },
        {
            "name": "Docker Test Config",
            "redis_url": "redis://localhost:6380",
            "task_stream": "test_agent_tasks",
            "result_stream": "test_agent_results",
        },
        {
            "name": "Production-Style Config",
            "redis_url": "redis://localhost:6379",
            "task_stream": "agent:tasks",
            "result_stream": "agent:results",
        },
        {
            "name": "Agent-Specific Stream Config",
            "redis_url": "redis://localhost:6379",
            "task_stream": "agent:spec:input",
            "result_stream": "agent:spec:output",
        },
    ]

    # Test each configuration
    for config in configs:
        print(f"\n\n==== Testing {config['name']} ====")
        try:
            # Create orchestrator with this config
            orchestrator = Orchestrator(
                redis_url=config["redis_url"],
                task_stream=config["task_stream"],
                result_stream=config["result_stream"],
                skip_pinecone_init=True,  # Skip Pinecone for testing
            )

            # Run diagnostics
            await diagnose_task_routing(orchestrator)

            # Try to enqueue a task
            logger.info(f"Attempting to enqueue task with {config['name']}...")
            try:
                task_id = await orchestrator.enqueue_task(
                    "spec",
                    {
                        "description": f"Debug test task ({config['name']})",
                        "priority": "high",
                    },
                )
                logger.info(f"Task enqueued with ID: {task_id}")
                print(f"✅ Task enqueued with ID: {task_id}")
            except Exception as e:
                logger.error(f"Failed to enqueue task: {e}", exc_info=True)
                print(f"❌ Failed to enqueue task: {e}")
        except Exception as e:
            logger.error(f"Configuration failed: {e}", exc_info=True)
            print(f"❌ Configuration failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_real_enqueue())
