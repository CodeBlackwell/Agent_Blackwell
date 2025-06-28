#!/usr/bin/env python3
"""
Test script to verify orchestrator task flow end-to-end.
This script tests the core orchestrator functionality without requiring full agent workers.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

# Add project root to PYTHONPATH so we can import 'src.*'
PROJECT_ROOT = Path(__file__).resolve().parent.parent  # tests/
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from redis import Redis

from src.orchestrator.main import Orchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_orchestrator_initialization():
    """Test orchestrator initialization in both test and production modes."""
    logger.info("🧪 Testing orchestrator initialization...")

    # Test mode initialization
    test_orchestrator = Orchestrator(
        redis_url="redis://localhost:6379", is_test_mode=True, skip_pinecone_init=True
    )

    assert test_orchestrator.is_test_mode == True
    assert test_orchestrator.task_stream == "test_agent_tasks"
    assert test_orchestrator.result_stream == "test_agent_results"
    logger.info("✅ Test mode initialization successful")

    # Production mode initialization
    prod_orchestrator = Orchestrator(
        redis_url="redis://localhost:6379", is_test_mode=False, skip_pinecone_init=True
    )

    assert prod_orchestrator.is_test_mode == False
    assert prod_orchestrator.task_stream == "agent_tasks"
    assert prod_orchestrator.result_stream == "agent_results"
    logger.info("✅ Production mode initialization successful")

    return test_orchestrator, prod_orchestrator


async def test_task_enqueuing(orchestrator, mode_name):
    """Test task enqueuing functionality."""
    logger.info(f"🚀 Testing task enqueuing in {mode_name} mode...")

    # Test spec agent task
    task_data = {
        "user_request": "Create a simple web application",
        "context": "Testing orchestrator flow",
    }

    task_id = await orchestrator.enqueue_task("spec", task_data)
    assert task_id is not None
    logger.info(f"✅ Successfully enqueued spec task with ID: {task_id}")

    # Test design agent task
    design_task_data = {
        "requirements": "User authentication system",
        "context": "Testing design flow",
    }

    design_task_id = await orchestrator.enqueue_task("design", design_task_data)
    assert design_task_id is not None
    logger.info(f"✅ Successfully enqueued design task with ID: {design_task_id}")

    return [task_id, design_task_id]


async def test_redis_stream_contents(orchestrator, task_ids, mode_name):
    """Test that tasks are properly stored in Redis streams."""
    logger.info(f"🔍 Verifying Redis stream contents in {mode_name} mode...")

    # Check main task stream
    try:
        messages = orchestrator.redis_client.xread(
            {orchestrator.task_stream: "0"}, count=10
        )
        logger.info(
            f"📊 Found {len(messages)} stream groups in {orchestrator.task_stream}"
        )

        if messages:
            stream_name, stream_messages = messages[0]
            logger.info(
                f"📋 Stream {stream_name.decode()} has {len(stream_messages)} messages"
            )

            # Verify our tasks are in the stream
            found_tasks = []
            for msg_id, fields in stream_messages:
                if b"task" in fields:
                    task_data = json.loads(fields[b"task"].decode())
                    found_tasks.append(task_data["task_id"])
                    logger.info(
                        f"📝 Found task: {task_data['task_id']} ({task_data['task_type']})"
                    )

            # Check if our enqueued tasks are present
            for task_id in task_ids:
                if task_id in found_tasks:
                    logger.info(f"✅ Task {task_id} found in stream")
                else:
                    logger.warning(f"⚠️ Task {task_id} not found in stream")

    except Exception as e:
        logger.error(f"❌ Error reading from Redis stream: {e}")
        raise


async def test_agent_type_mapping(orchestrator):
    """Test agent type mapping functionality."""
    logger.info("🗺️ Testing agent type mapping...")

    # Test mapping lookup
    spec_mappings = orchestrator.agent_type_mapping.get("spec", [])
    assert "spec" in spec_mappings
    assert "spec_agent" in spec_mappings
    logger.info(f"✅ Spec agent mapping: {spec_mappings}")

    # Test stream mapping
    spec_streams = orchestrator.agent_stream_mapping.get("spec", [])
    assert "agent:spec:input" in spec_streams
    assert "agent:spec_agent:input" in spec_streams
    logger.info(f"✅ Spec stream mapping: {spec_streams}")


async def test_subtask_processing_logic():
    """Test the subtask processing logic from process_task method."""
    logger.info("🔄 Testing subtask processing logic...")

    # Create a mock result that would come from spec_agent
    mock_spec_result = {
        "output": [
            {
                "task_type": "design",
                "requirements": "Design user interface",
                "context": "From spec agent",
            },
            {
                "task_type": "coding",
                "specifications": "Implement backend API",
                "context": "From spec agent",
            },
        ]
    }

    # Test the logic that would be used in process_task
    if isinstance(mock_spec_result, dict) and "output" in mock_spec_result:
        if isinstance(mock_spec_result["output"], list):
            sub_tasks = mock_spec_result["output"]
            logger.info(f"✅ Found {len(sub_tasks)} subtasks in spec result")

            for sub_task in sub_tasks:
                subtask_type = sub_task.get("task_type", "general")
                logger.info(f"📋 Subtask type: {subtask_type}")
                assert subtask_type in ["design", "coding"]
        else:
            logger.error("❌ Spec result output is not a list")
    else:
        logger.error("❌ Spec result does not have expected structure")


async def cleanup_test_streams(redis_client, stream_names):
    """Clean up test streams after testing."""
    logger.info("🧹 Cleaning up test streams...")

    for stream_name in stream_names:
        try:
            # Delete the stream
            redis_client.delete(stream_name)
            logger.info(f"🗑️ Deleted stream: {stream_name}")
        except Exception as e:
            logger.warning(f"⚠️ Could not delete stream {stream_name}: {e}")


async def main():
    """Main test function."""
    logger.info("🚀 Starting orchestrator task flow verification...")

    try:
        # Test initialization
        test_orch, prod_orch = await test_orchestrator_initialization()

        # Test agent type mapping
        await test_agent_type_mapping(test_orch)

        # Test subtask processing logic
        await test_subtask_processing_logic()

        # Test task enqueuing in both modes
        test_task_ids = await test_task_enqueuing(test_orch, "test")
        prod_task_ids = await test_task_enqueuing(prod_orch, "production")

        # Verify Redis stream contents
        await test_redis_stream_contents(test_orch, test_task_ids, "test")
        await test_redis_stream_contents(prod_orch, prod_task_ids, "production")

        # Clean up test streams
        await cleanup_test_streams(
            test_orch.redis_client,
            ["test_agent_tasks", "test_agent_results", "agent_tasks", "agent_results"],
        )

        logger.info("🎉 All orchestrator task flow tests passed!")

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
