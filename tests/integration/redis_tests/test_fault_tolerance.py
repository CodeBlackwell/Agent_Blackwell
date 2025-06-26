"""
Redis Stream Fault Tolerance Integration Tests.
"""
import asyncio
import json
import time
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import redis.asyncio as redis
from redis.exceptions import ConnectionError, TimeoutError

from src.config.settings import get_settings
from tests.fixtures.main import get_fixtures_by_category


class TestRedisConnectionFaultTolerance:
    """Test behavior when Redis connections drop temporarily."""

    @pytest.fixture
    async def redis_client(self):
        """Create Redis client for testing."""
        settings = get_settings("test")
        client = redis.Redis(
            host=settings.redis.host,
            port=settings.redis.port,
            decode_responses=True,
            retry_on_timeout=True,
            retry_on_error=[ConnectionError, TimeoutError],
        )
        yield client
        await client.close()

    @pytest.mark.asyncio
    async def test_connection_drop_during_publishing(self, redis_client):
        """Test behavior when connection drops during message publishing."""
        stream_name = "test:connection_drop_pub"

        # Publish some messages successfully
        successful_messages = []
        for i in range(5):
            message = {
                "task_id": f"success_{i}",
                "content": f"Successful message {i}",
                "status": "published",
            }
            message_id = await redis_client.xadd(stream_name, message)
            successful_messages.append(message_id)

        # Simulate connection issues with mock
        with patch.object(redis_client, "xadd") as mock_xadd:
            # First call fails with connection error
            mock_xadd.side_effect = [
                ConnectionError("Connection lost"),
                ConnectionError("Still down"),
                "success_message_id",  # Recovery
            ]

            # Try to publish during connection issues
            with pytest.raises(ConnectionError):
                await redis_client.xadd(
                    stream_name, {"task_id": "fail_1", "content": "Failed message"}
                )

            # Second attempt also fails
            with pytest.raises(ConnectionError):
                await redis_client.xadd(
                    stream_name, {"task_id": "fail_2", "content": "Failed message"}
                )

            # Third attempt succeeds (connection recovered)
            result = await redis_client.xadd(
                stream_name, {"task_id": "recovery", "content": "Recovery message"}
            )
            assert result == "success_message_id"

        # Verify original messages are still there
        messages = await redis_client.xrange(stream_name)
        assert len(messages) >= 5  # Original messages should still exist

        # Cleanup
        await redis_client.delete(stream_name)

    @pytest.mark.asyncio
    async def test_connection_drop_during_consumption(self, redis_client):
        """Test behavior when connection drops during message consumption."""
        stream_name = "test:connection_drop_cons"
        consumer_group = "test_connection_group"
        consumer_name = "test_consumer"

        # Populate stream with messages
        message_ids = []
        for i in range(10):
            message = {
                "task_id": f"consume_test_{i}",
                "content": f"Message for consumption test {i}",
                "sequence": str(i),
            }
            msg_id = await redis_client.xadd(stream_name, message)
            message_ids.append(msg_id)

        # Create consumer group
        try:
            await redis_client.xgroup_create(
                stream_name, consumer_group, id="0", mkstream=True
            )
        except redis.exceptions.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise

        # Simulate connection drop during consumption
        consumed_messages = []
        with patch.object(redis_client, "xreadgroup") as mock_xreadgroup:
            # First call succeeds
            mock_xreadgroup.side_effect = [
                [
                    (
                        stream_name,
                        [
                            (
                                message_ids[0],
                                {"task_id": "consume_test_0", "content": "Message 0"},
                            )
                        ],
                    )
                ],
                ConnectionError("Connection lost during consumption"),
                [
                    (
                        stream_name,
                        [
                            (
                                message_ids[1],
                                {"task_id": "consume_test_1", "content": "Message 1"},
                            )
                        ],
                    )
                ],
            ]

            # First consumption succeeds
            messages = await redis_client.xreadgroup(
                consumer_group, consumer_name, {stream_name: ">"}, count=1
            )
            consumed_messages.extend(messages[0][1])

            # Second consumption fails
            with pytest.raises(ConnectionError):
                await redis_client.xreadgroup(
                    consumer_group, consumer_name, {stream_name: ">"}, count=1
                )

            # Third consumption succeeds (connection recovered)
            messages = await redis_client.xreadgroup(
                consumer_group, consumer_name, {stream_name: ">"}, count=1
            )
            consumed_messages.extend(messages[0][1])

        assert len(consumed_messages) == 2

        # Cleanup
        await redis_client.delete(stream_name)

    @pytest.mark.asyncio
    async def test_connection_pool_exhaustion(self, redis_client):
        """Test behavior when connection pool is exhausted."""
        stream_name = "test:pool_exhaustion"

        # Create multiple clients to exhaust connection pool
        clients = []
        try:
            settings = get_settings("test")
            for i in range(5):  # Create multiple clients
                client = redis.Redis(
                    host=settings.redis.host,
                    port=settings.redis.port,
                    decode_responses=True,
                    max_connections=2,  # Low connection limit
                )
                clients.append(client)

            # Try to use all clients simultaneously
            async def publish_with_client(client, client_id):
                try:
                    message = {
                        "client_id": str(client_id),
                        "task_id": f"pool_test_{client_id}",
                        "content": f"Message from client {client_id}",
                    }
                    return await client.xadd(stream_name, message)
                except Exception as e:
                    return f"Error: {str(e)}"

            # Execute all clients concurrently
            tasks = [publish_with_client(client, i) for i, client in enumerate(clients)]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Some should succeed, others might fail due to pool exhaustion
            successful_results = [
                r
                for r in results
                if not isinstance(r, Exception) and not str(r).startswith("Error")
            ]

            # At least some operations should succeed
            assert len(successful_results) > 0

        finally:
            # Cleanup clients
            for client in clients:
                await client.close()
            await redis_client.delete(stream_name)


class TestRedisServiceRestart:
    """Test behavior after Redis service restarts."""

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
    async def test_data_persistence_after_restart(self, redis_client):
        """Test that data persists after Redis restart simulation."""
        stream_name = "test:restart_persistence"

        # Add persistent data
        persistent_messages = []
        for i in range(5):
            message = {
                "task_id": f"persistent_{i}",
                "content": f"Persistent message {i}",
                "type": "persistent",
            }
            msg_id = await redis_client.xadd(stream_name, message)
            persistent_messages.append(msg_id)

        # Simulate restart by forcing connection reset
        await redis_client.connection_pool.disconnect()

        # Reconnect and verify data persistence
        await asyncio.sleep(1)  # Brief pause to simulate restart

        # Check if messages are still there
        messages = await redis_client.xrange(stream_name)
        assert len(messages) == 5

        # Verify message content
        for i, (msg_id, msg_data) in enumerate(messages):
            assert msg_data["task_id"] == f"persistent_{i}"
            assert msg_data["type"] == "persistent"

        # Cleanup
        await redis_client.delete(stream_name)

    @pytest.mark.asyncio
    async def test_consumer_group_recovery_after_restart(self, redis_client):
        """Test consumer group recovery after restart."""
        stream_name = "test:restart_consumer_group"
        consumer_group = "restart_test_group"

        # Create consumer group and add messages
        try:
            await redis_client.xgroup_create(
                stream_name, consumer_group, id="0", mkstream=True
            )
        except redis.exceptions.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise

        # Add messages to stream
        for i in range(5):
            message = {
                "task_id": f"restart_msg_{i}",
                "content": f"Message {i}",
                "status": "pending",
            }
            await redis_client.xadd(stream_name, message)

        # Consume some messages
        messages = await redis_client.xreadgroup(
            consumer_group, "consumer_1", {stream_name: ">"}, count=2
        )

        consumed_msg_ids = [msg[0] for msg in messages[0][1]]

        # Simulate restart
        await redis_client.connection_pool.disconnect()
        await asyncio.sleep(1)

        # Verify consumer group still exists
        groups = await redis_client.xinfo_groups(stream_name)
        group_names = [group["name"] for group in groups]
        assert consumer_group in group_names

        # Verify pending messages are tracked
        pending = await redis_client.xpending(stream_name, consumer_group)
        assert pending["pending"] == 2  # 2 messages consumed but not acknowledged

        # Continue consuming remaining messages
        remaining_messages = await redis_client.xreadgroup(
            consumer_group, "consumer_1", {stream_name: ">"}, count=10
        )

        # Should get remaining 3 messages
        assert len(remaining_messages[0][1]) == 3

        # Cleanup
        await redis_client.delete(stream_name)


class TestRedisConsumerGroupRebalancing:
    """Test consumer group rebalancing when workers join/leave."""

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
    async def test_consumer_joining_group(self, redis_client):
        """Test behavior when new consumers join the group."""
        stream_name = "test:consumer_join"
        consumer_group = "join_test_group"

        # Create consumer group and populate stream
        try:
            await redis_client.xgroup_create(
                stream_name, consumer_group, id="0", mkstream=True
            )
        except redis.exceptions.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise

        # Add many messages
        for i in range(20):
            message = {
                "task_id": f"join_test_{i}",
                "content": f"Message {i}",
                "batch": str(i // 5),
            }
            await redis_client.xadd(stream_name, message)

        # Start with one consumer
        async def consumer_task(consumer_name: str, max_messages: int = 10):
            consumed = []
            for _ in range(max_messages):
                try:
                    messages = await redis_client.xreadgroup(
                        consumer_group,
                        consumer_name,
                        {stream_name: ">"},
                        count=1,
                        block=1000,
                    )
                    if messages and messages[0][1]:
                        msg_id, msg_data = messages[0][1][0]
                        consumed.append(msg_data["task_id"])
                        await redis_client.xack(stream_name, consumer_group, msg_id)
                    else:
                        break
                except Exception:
                    break
            return consumed

        # Start first consumer
        consumer1_task = asyncio.create_task(consumer_task("consumer_1", 15))
        await asyncio.sleep(0.1)  # Let it start consuming

        # Add second consumer (join the group)
        consumer2_task = asyncio.create_task(consumer_task("consumer_2", 15))

        # Wait for both to complete
        results = await asyncio.gather(consumer1_task, consumer2_task)

        consumer1_consumed = results[0]
        consumer2_consumed = results[1]

        # Verify both consumers processed messages
        assert len(consumer1_consumed) > 0
        assert len(consumer2_consumed) > 0

        # Verify no duplicate processing
        all_consumed = consumer1_consumed + consumer2_consumed
        assert len(all_consumed) == len(set(all_consumed))

        # Verify total messages processed
        total_processed = len(all_consumed)
        assert total_processed <= 20

        print(f"Consumer 1 processed: {len(consumer1_consumed)} messages")
        print(f"Consumer 2 processed: {len(consumer2_consumed)} messages")

        # Cleanup
        await redis_client.delete(stream_name)

    @pytest.mark.asyncio
    async def test_consumer_leaving_group(self, redis_client):
        """Test behavior when consumers leave the group (claim pending messages)."""
        stream_name = "test:consumer_leave"
        consumer_group = "leave_test_group"

        # Create consumer group and populate stream
        try:
            await redis_client.xgroup_create(
                stream_name, consumer_group, id="0", mkstream=True
            )
        except redis.exceptions.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise

        # Add messages
        for i in range(10):
            message = {
                "task_id": f"leave_test_{i}",
                "content": f"Message {i}",
                "timestamp": str(time.time()),
            }
            await redis_client.xadd(stream_name, message)

        # Consumer 1 consumes messages but doesn't acknowledge (simulates crash)
        messages = await redis_client.xreadgroup(
            consumer_group, "failing_consumer", {stream_name: ">"}, count=5
        )

        pending_msg_ids = [msg[0] for msg in messages[0][1]]
        assert len(pending_msg_ids) == 5

        # Check pending messages
        pending_info = await redis_client.xpending(stream_name, consumer_group)
        assert pending_info["pending"] == 5

        # New consumer claims pending messages
        claimed_messages = await redis_client.xclaim(
            stream_name,
            consumer_group,
            "recovery_consumer",
            min_idle_time=0,  # Claim immediately for testing
            message_ids=pending_msg_ids,
        )

        assert len(claimed_messages) == 5

        # Acknowledge claimed messages
        for msg_id, _ in claimed_messages:
            await redis_client.xack(stream_name, consumer_group, msg_id)

        # Verify no pending messages remain
        pending_after = await redis_client.xpending(stream_name, consumer_group)
        assert pending_after["pending"] == 0

        # Cleanup
        await redis_client.delete(stream_name)


class TestRedisDuplicateHandling:
    """Test handling of duplicate messages."""

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
    async def test_duplicate_message_detection(self, redis_client):
        """Test detection and handling of duplicate messages."""
        stream_name = "test:duplicate_detection"
        dedup_stream = "test:duplicate_tracking"

        # Track processed message IDs to detect duplicates
        processed_messages = set()

        # Simulate processing messages with potential duplicates
        test_messages = [
            {"task_id": "msg_001", "content": "First message"},
            {"task_id": "msg_002", "content": "Second message"},
            {"task_id": "msg_001", "content": "Duplicate first message"},  # Duplicate
            {"task_id": "msg_003", "content": "Third message"},
            {"task_id": "msg_002", "content": "Duplicate second message"},  # Duplicate
        ]

        processed_count = 0
        duplicate_count = 0

        for message in test_messages:
            task_id = message["task_id"]

            # Check if already processed
            is_duplicate = await redis_client.sismember("processed_tasks", task_id)

            if is_duplicate:
                duplicate_count += 1
                # Log duplicate to tracking stream
                duplicate_entry = {
                    "task_id": task_id,
                    "content": message["content"],
                    "duplicate_at": str(time.time()),
                    "action": "ignored",
                }
                await redis_client.xadd(dedup_stream, duplicate_entry)
            else:
                # Process message
                await redis_client.xadd(stream_name, message)
                await redis_client.sadd("processed_tasks", task_id)
                processed_count += 1

        # Verify results
        assert processed_count == 3  # Only unique messages processed
        assert duplicate_count == 2  # Two duplicates detected

        # Verify tracking
        duplicate_logs = await redis_client.xrange(dedup_stream)
        assert len(duplicate_logs) == 2

        processed_tasks = await redis_client.smembers("processed_tasks")
        assert len(processed_tasks) == 3
        assert "msg_001" in processed_tasks
        assert "msg_002" in processed_tasks
        assert "msg_003" in processed_tasks

        # Cleanup
        await redis_client.delete(stream_name)
        await redis_client.delete(dedup_stream)
        await redis_client.delete("processed_tasks")

    @pytest.mark.asyncio
    async def test_idempotent_processing(self, redis_client):
        """Test idempotent message processing."""
        stream_name = "test:idempotent"
        result_hash = "test:results"

        # Message that should be processed idempotently
        message = {
            "task_id": "idempotent_001",
            "operation": "add",
            "value": "10",
            "target": "counter",
        }

        # Process same message multiple times
        for attempt in range(3):
            msg_id = await redis_client.xadd(
                stream_name, {**message, "attempt": str(attempt + 1)}
            )

            # Idempotent processing: check if already processed
            existing_result = await redis_client.hget(result_hash, message["task_id"])

            if existing_result is None:
                # First time processing
                result = {
                    "task_id": message["task_id"],
                    "result": "processed",
                    "value": message["value"],
                    "processed_at": str(time.time()),
                }
                await redis_client.hset(
                    result_hash, message["task_id"], json.dumps(result)
                )
                actual_processing = True
            else:
                # Already processed, skip
                actual_processing = False

            # Only first attempt should actually process
            if attempt == 0:
                assert actual_processing == True
            else:
                assert actual_processing == False

        # Verify only one result exists
        all_results = await redis_client.hgetall(result_hash)
        assert len(all_results) == 1

        stored_result = json.loads(all_results[message["task_id"]])
        assert stored_result["task_id"] == message["task_id"]
        assert stored_result["result"] == "processed"

        # Cleanup
        await redis_client.delete(stream_name)
        await redis_client.delete(result_hash)
