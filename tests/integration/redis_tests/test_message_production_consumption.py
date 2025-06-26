"""
Redis Stream Integration Tests for message production and consumption.
"""
import asyncio
import json
from typing import Any, Dict, List
from unittest.mock import AsyncMock, patch

import pytest
import redis.asyncio as redis

from src.config.settings import get_settings
from tests.fixtures.main import get_fixtures_by_category


class TestRedisMessageProduction:
    """Test message production to Redis streams."""

    @pytest.fixture
    async def redis_client(self):
        """Create Redis client for testing."""
        settings = get_settings("test")
        client = redis.Redis(
            host=settings.redis.host, port=settings.redis.port, decode_responses=True
        )
        yield client
        await client.close()

    @pytest.fixture
    def sample_task_data(self):
        """Get sample task data for testing."""
        user_requests = get_fixtures_by_category("user_requests")
        return user_requests["structured"][0]

    @pytest.mark.asyncio
    async def test_task_creation_and_publishing(self, redis_client, sample_task_data):
        """Test creating and publishing tasks to Redis streams."""
        stream_name = "test:tasks"

        # Create task message
        task_message = {
            "task_id": sample_task_data["id"],
            "user_id": sample_task_data["user_id"],
            "content": sample_task_data["content"],
            "priority": sample_task_data["priority"],
            "timestamp": sample_task_data["timestamp"],
            "status": "pending",
        }

        # Publish to stream
        message_id = await redis_client.xadd(stream_name, task_message)

        assert message_id is not None

        # Verify message was added
        messages = await redis_client.xrange(stream_name, count=1)
        assert len(messages) == 1

        retrieved_message = messages[0]
        assert retrieved_message[1]["task_id"] == task_message["task_id"]
        assert retrieved_message[1]["content"] == task_message["content"]

        # Cleanup
        await redis_client.delete(stream_name)

    @pytest.mark.asyncio
    async def test_batch_task_publishing(self, redis_client):
        """Test publishing multiple tasks in batch."""
        stream_name = "test:batch_tasks"
        user_requests = get_fixtures_by_category("user_requests")
        tasks = user_requests["structured"]

        # Publish multiple tasks
        message_ids = []
        for task in tasks:
            task_message = {
                "task_id": task["id"],
                "content": task["content"],
                "priority": task["priority"],
                "status": "pending",
            }
            message_id = await redis_client.xadd(stream_name, task_message)
            message_ids.append(message_id)

        assert len(message_ids) == len(tasks)

        # Verify all messages were added
        messages = await redis_client.xrange(stream_name)
        assert len(messages) == len(tasks)

        # Cleanup
        await redis_client.delete(stream_name)

    @pytest.mark.asyncio
    async def test_message_with_complex_data(self, redis_client):
        """Test publishing messages with complex data structures."""
        stream_name = "test:complex_data"
        agent_fixtures = get_fixtures_by_category("agent_io")
        spec_output = agent_fixtures["spec_agent"]["outputs"][0]

        # Create complex message with nested data
        complex_message = {
            "task_id": "complex_001",
            "agent_type": "spec_agent",
            "output_data": json.dumps(spec_output),  # Serialize complex data
            "metadata": json.dumps(
                {"processing_time": 120.5, "tokens_used": 1500, "model": "gpt-4"}
            ),
        }

        message_id = await redis_client.xadd(stream_name, complex_message)
        assert message_id is not None

        # Verify complex data integrity
        messages = await redis_client.xrange(stream_name, count=1)
        retrieved_message = messages[0][1]

        # Deserialize and verify
        retrieved_output = json.loads(retrieved_message["output_data"])
        assert retrieved_output["task_id"] == spec_output["task_id"]
        assert "specifications" in retrieved_output

        # Cleanup
        await redis_client.delete(stream_name)


class TestRedisMessageConsumption:
    """Test message consumption from Redis streams."""

    @pytest.fixture
    async def redis_client(self):
        """Create Redis client for testing."""
        settings = get_settings("test")
        client = redis.Redis(
            host=settings.redis.host, port=settings.redis.port, decode_responses=True
        )
        yield client
        await client.close()

    @pytest.fixture
    async def populated_stream(self, redis_client):
        """Create a populated stream for consumption testing."""
        stream_name = "test:consumption"
        user_requests = get_fixtures_by_category("user_requests")
        tasks = user_requests["structured"]

        # Populate stream with test data
        for task in tasks:
            task_message = {
                "task_id": task["id"],
                "content": task["content"],
                "status": "pending",
            }
            await redis_client.xadd(stream_name, task_message)

        yield stream_name

        # Cleanup
        await redis_client.delete(stream_name)

    @pytest.mark.asyncio
    async def test_consumer_group_creation(self, redis_client, populated_stream):
        """Test creating consumer groups for stream processing."""
        consumer_group = "test_processors"

        # Create consumer group
        try:
            await redis_client.xgroup_create(
                populated_stream, consumer_group, id="0", mkstream=True
            )
        except redis.exceptions.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise

        # Verify group exists
        groups = await redis_client.xinfo_groups(populated_stream)
        group_names = [group["name"] for group in groups]
        assert consumer_group in group_names

    @pytest.mark.asyncio
    async def test_message_consumption_with_ack(self, redis_client, populated_stream):
        """Test consuming messages with acknowledgment."""
        consumer_group = "test_ack_processors"
        consumer_name = "test_consumer_1"

        # Create consumer group
        try:
            await redis_client.xgroup_create(
                populated_stream, consumer_group, id="0", mkstream=True
            )
        except redis.exceptions.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise

        # Consume messages
        messages = await redis_client.xreadgroup(
            consumer_group, consumer_name, {populated_stream: ">"}, count=2, block=1000
        )

        assert len(messages) > 0
        stream_messages = messages[0][1]
        assert len(stream_messages) <= 2

        # Acknowledge messages
        for message_id, _ in stream_messages:
            ack_result = await redis_client.xack(
                populated_stream, consumer_group, message_id
            )
            assert ack_result == 1

    @pytest.mark.asyncio
    async def test_multiple_consumers_same_group(self, redis_client, populated_stream):
        """Test multiple consumers in the same group."""
        consumer_group = "test_multi_consumers"
        consumer_1 = "consumer_1"
        consumer_2 = "consumer_2"

        # Create consumer group
        try:
            await redis_client.xgroup_create(
                populated_stream, consumer_group, id="0", mkstream=True
            )
        except redis.exceptions.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise

        # Both consumers read simultaneously
        messages_1 = await redis_client.xreadgroup(
            consumer_group, consumer_1, {populated_stream: ">"}, count=1, block=1000
        )

        messages_2 = await redis_client.xreadgroup(
            consumer_group, consumer_2, {populated_stream: ">"}, count=1, block=1000
        )

        # Verify messages are distributed (no duplicates)
        if messages_1 and messages_2:
            msg_1_ids = [msg[0] for msg in messages_1[0][1]]
            msg_2_ids = [msg[0] for msg in messages_2[0][1]]
            assert not set(msg_1_ids).intersection(set(msg_2_ids))


class TestRedisMessageRetry:
    """Test message retry mechanisms."""

    @pytest.fixture
    async def redis_client(self):
        """Create Redis client for testing."""
        settings = get_settings("test")
        client = redis.Redis(
            host=settings.redis.host, port=settings.redis.port, decode_responses=True
        )
        yield client
        await client.close()

    @pytest.mark.asyncio
    async def test_message_retry_on_failure(self, redis_client):
        """Test message retry when processing fails."""
        stream_name = "test:retry_stream"
        consumer_group = "test_retry_group"
        consumer_name = "test_retry_consumer"

        # Add test message
        message_data = {
            "task_id": "retry_001",
            "content": "Test retry message",
            "retry_count": "0",
        }

        await redis_client.xadd(stream_name, message_data)

        # Create consumer group
        try:
            await redis_client.xgroup_create(
                stream_name, consumer_group, id="0", mkstream=True
            )
        except redis.exceptions.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise

        # Consume message (simulate processing failure by not acknowledging)
        messages = await redis_client.xreadgroup(
            consumer_group, consumer_name, {stream_name: ">"}, count=1, block=1000
        )

        assert len(messages) > 0
        message_id = messages[0][1][0][0]

        # Check pending messages (unacknowledged)
        pending = await redis_client.xpending_range(
            stream_name, consumer_group, min="-", max="+", count=10
        )

        assert len(pending) == 1
        assert pending[0]["message_id"] == message_id

        # Simulate retry by claiming the message
        claimed = await redis_client.xclaim(
            stream_name,
            consumer_group,
            consumer_name,
            min_idle_time=0,
            message_ids=[message_id],
        )

        assert len(claimed) == 1

        # Cleanup
        await redis_client.xack(stream_name, consumer_group, message_id)
        await redis_client.delete(stream_name)

    @pytest.mark.asyncio
    async def test_dead_letter_queue_simulation(self, redis_client):
        """Test dead letter queue for failed messages."""
        main_stream = "test:main_stream"
        dlq_stream = "test:dlq_stream"

        # Add message that will "fail" processing
        failed_message = {
            "task_id": "dlq_001",
            "content": "Message that will fail",
            "retry_count": "3",  # Max retries reached
            "error": "Processing failed after 3 attempts",
        }

        # Add to main stream first
        await redis_client.xadd(main_stream, failed_message)

        # Move to DLQ (simulate failed processing)
        dlq_message = {
            **failed_message,
            "moved_to_dlq_at": "2025-01-01T12:00:00Z",
            "original_stream": main_stream,
        }

        dlq_message_id = await redis_client.xadd(dlq_stream, dlq_message)
        assert dlq_message_id is not None

        # Verify message in DLQ
        dlq_messages = await redis_client.xrange(dlq_stream)
        assert len(dlq_messages) == 1
        assert dlq_messages[0][1]["task_id"] == "dlq_001"

        # Cleanup
        await redis_client.delete(main_stream)
        await redis_client.delete(dlq_stream)
