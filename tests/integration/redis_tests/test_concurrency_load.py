"""
Redis Stream Concurrency and Load Integration Tests.
"""
import pytest
import asyncio
import time
import json
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import AsyncMock, patch

import redis.asyncio as redis
from src.config.settings import get_settings
from tests.fixtures.main import get_fixtures_by_category


class TestRedisConcurrency:
    """Test concurrent producers and consumers."""

    @pytest.fixture
    async def redis_client(self):
        """Create Redis client for testing."""
        settings = get_settings("test")
        client = redis.Redis(
            host=settings.redis.host,
            port=settings.redis.port,
            decode_responses=True
        )
        yield client
        await client.close()

    @pytest.fixture
    def sample_tasks(self):
        """Get sample task data for load testing."""
        user_requests = get_fixtures_by_category("user_requests")
        return user_requests["structured"] * 10  # Multiply for more test data

    @pytest.mark.asyncio
    async def test_multiple_concurrent_producers(self, redis_client, sample_tasks):
        """Test multiple producers writing to the same stream simultaneously."""
        stream_name = "test:concurrent_producers"
        num_producers = 5
        tasks_per_producer = 20
        
        async def producer_task(producer_id: int, tasks: List[Dict]):
            """Producer task that publishes messages."""
            producer_client = redis.Redis(
                host="redis-test",
                port=6379,
                decode_responses=True
            )
            
            published_count = 0
            for i, task in enumerate(tasks[:tasks_per_producer]):
                message = {
                    "task_id": f"producer_{producer_id}_task_{i}",
                    "producer_id": str(producer_id),
                    "content": task["content"],
                    "sequence": str(i)
                }
                await producer_client.xadd(stream_name, message)
                published_count += 1
            
            await producer_client.close()
            return published_count
        
        # Launch multiple producers concurrently
        start_time = time.time()
        producer_tasks = [
            producer_task(i, sample_tasks) 
            for i in range(num_producers)
        ]
        
        results = await asyncio.gather(*producer_tasks)
        end_time = time.time()
        
        # Verify results
        total_published = sum(results)
        expected_total = num_producers * tasks_per_producer
        assert total_published == expected_total
        
        # Verify all messages are in the stream
        stream_length = await redis_client.xlen(stream_name)
        assert stream_length == expected_total
        
        # Check for message ordering and integrity
        all_messages = await redis_client.xrange(stream_name)
        assert len(all_messages) == expected_total
        
        # Verify producer distribution
        producer_counts = {}
        for _, message_data in all_messages:
            producer_id = message_data["producer_id"]
            producer_counts[producer_id] = producer_counts.get(producer_id, 0) + 1
        
        assert len(producer_counts) == num_producers
        for count in producer_counts.values():
            assert count == tasks_per_producer
        
        print(f"Concurrent producers test completed in {end_time - start_time:.2f} seconds")
        
        # Cleanup
        await redis_client.delete(stream_name)

    @pytest.mark.asyncio
    async def test_multiple_concurrent_consumers(self, redis_client, sample_tasks):
        """Test multiple consumers processing from the same stream."""
        stream_name = "test:concurrent_consumers"
        consumer_group = "test_consumer_group"
        num_consumers = 3
        total_messages = 30
        
        # Populate stream with messages
        for i in range(total_messages):
            message = {
                "task_id": f"task_{i}",
                "content": sample_tasks[i % len(sample_tasks)]["content"],
                "sequence": str(i)
            }
            await redis_client.xadd(stream_name, message)
        
        # Create consumer group
        try:
            await redis_client.xgroup_create(
                stream_name,
                consumer_group,
                id="0",
                mkstream=True
            )
        except redis.exceptions.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise
        
        async def consumer_task(consumer_id: int):
            """Consumer task that processes messages."""
            consumer_client = redis.Redis(
                host="redis-test",
                port=6379,
                decode_responses=True
            )
            
            consumer_name = f"consumer_{consumer_id}"
            processed_count = 0
            processed_messages = []
            
            # Consumer loop
            while True:
                try:
                    messages = await consumer_client.xreadgroup(
                        consumer_group,
                        consumer_name,
                        {stream_name: ">"},
                        count=5,
                        block=1000
                    )
                    
                    if not messages or not messages[0][1]:
                        break  # No more messages
                    
                    for message_id, message_data in messages[0][1]:
                        # Simulate processing
                        await asyncio.sleep(0.01)  # Small processing delay
                        
                        # Acknowledge message
                        await consumer_client.xack(
                            stream_name,
                            consumer_group,
                            message_id
                        )
                        
                        processed_count += 1
                        processed_messages.append({
                            "message_id": message_id,
                            "task_id": message_data["task_id"],
                            "consumer_id": consumer_id
                        })
                
                except asyncio.TimeoutError:
                    break
            
            await consumer_client.close()
            return processed_count, processed_messages
        
        # Launch multiple consumers concurrently
        start_time = time.time()
        consumer_tasks = [
            consumer_task(i) 
            for i in range(num_consumers)
        ]
        
        results = await asyncio.gather(*consumer_tasks)
        end_time = time.time()
        
        # Verify results
        total_processed = sum(result[0] for result in results)
        all_processed_messages = []
        for _, messages in results:
            all_processed_messages.extend(messages)
        
        assert total_processed == total_messages
        assert len(all_processed_messages) == total_messages
        
        # Verify no message was processed twice
        processed_task_ids = [msg["task_id"] for msg in all_processed_messages]
        assert len(processed_task_ids) == len(set(processed_task_ids))
        
        # Verify load distribution among consumers
        consumer_loads = {}
        for msg in all_processed_messages:
            consumer_id = msg["consumer_id"]
            consumer_loads[consumer_id] = consumer_loads.get(consumer_id, 0) + 1
        
        assert len(consumer_loads) == num_consumers
        # Check that load is reasonably distributed (within 50% variance)
        avg_load = total_messages / num_consumers
        for load in consumer_loads.values():
            assert abs(load - avg_load) <= avg_load * 0.5
        
        print(f"Concurrent consumers test completed in {end_time - start_time:.2f} seconds")
        print(f"Consumer loads: {consumer_loads}")
        
        # Cleanup
        await redis_client.delete(stream_name)


class TestRedisLoadTesting:
    """Test Redis performance under load."""

    @pytest.fixture
    async def redis_client(self):
        """Create Redis client for testing."""
        settings = get_settings("test")
        client = redis.Redis(
            host=settings.redis.host,
            port=settings.redis.port,
            decode_responses=True
        )
        yield client
        await client.close()

    @pytest.mark.asyncio
    async def test_high_throughput_publishing(self, redis_client):
        """Test publishing high volume of messages."""
        stream_name = "test:high_throughput"
        num_messages = 1000
        batch_size = 50
        
        # Generate test messages
        messages = []
        for i in range(num_messages):
            messages.append({
                "task_id": f"load_test_{i}",
                "content": f"Load test message {i}",
                "batch": str(i // batch_size),
                "timestamp": str(time.time())
            })
        
        # Batch publishing for better performance
        start_time = time.time()
        
        # Use pipeline for batch operations
        pipe = redis_client.pipeline()
        for i, message in enumerate(messages):
            pipe.xadd(stream_name, message)
            
            # Execute in batches
            if (i + 1) % batch_size == 0:
                await pipe.execute()
                pipe = redis_client.pipeline()
        
        # Execute remaining messages
        await pipe.execute()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Verify all messages were published
        stream_length = await redis_client.xlen(stream_name)
        assert stream_length == num_messages
        
        # Calculate throughput
        throughput = num_messages / duration
        print(f"Published {num_messages} messages in {duration:.2f} seconds")
        print(f"Throughput: {throughput:.0f} messages/second")
        
        # Assert reasonable performance (adjust based on your requirements)
        assert throughput > 100  # At least 100 messages per second
        
        # Cleanup
        await redis_client.delete(stream_name)

    @pytest.mark.asyncio
    async def test_sustained_load_processing(self, redis_client):
        """Test sustained processing under load."""
        stream_name = "test:sustained_load"
        consumer_group = "load_test_group"
        num_messages = 500
        processing_duration = 30  # seconds
        
        # Create consumer group
        try:
            await redis_client.xgroup_create(
                stream_name,
                consumer_group,
                id="0",
                mkstream=True
            )
        except redis.exceptions.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise
        
        # Continuous producer
        async def continuous_producer():
            """Continuously produce messages."""
            producer_client = redis.Redis(
                host="redis-test",
                port=6379,
                decode_responses=True
            )
            
            message_count = 0
            start_time = time.time()
            
            while time.time() - start_time < processing_duration:
                message = {
                    "task_id": f"sustained_{message_count}",
                    "content": f"Sustained load message {message_count}",
                    "timestamp": str(time.time())
                }
                await producer_client.xadd(stream_name, message)
                message_count += 1
                
                # Small delay to simulate realistic production rate
                await asyncio.sleep(0.01)
            
            await producer_client.close()
            return message_count
        
        # Continuous consumer
        async def continuous_consumer(consumer_id: int):
            """Continuously consume and process messages."""
            consumer_client = redis.Redis(
                host="redis-test",
                port=6379,
                decode_responses=True
            )
            
            consumer_name = f"load_consumer_{consumer_id}"
            processed_count = 0
            start_time = time.time()
            
            while time.time() - start_time < processing_duration:
                try:
                    messages = await consumer_client.xreadgroup(
                        consumer_group,
                        consumer_name,
                        {stream_name: ">"},
                        count=10,
                        block=1000
                    )
                    
                    if messages and messages[0][1]:
                        for message_id, message_data in messages[0][1]:
                            # Simulate processing time
                            await asyncio.sleep(0.005)
                            
                            # Acknowledge message
                            await consumer_client.xack(
                                stream_name,
                                consumer_group,
                                message_id
                            )
                            processed_count += 1
                
                except asyncio.TimeoutError:
                    continue
            
            await consumer_client.close()
            return processed_count
        
        # Run producer and consumers concurrently
        start_time = time.time()
        
        producer_task = continuous_producer()
        consumer_tasks = [continuous_consumer(i) for i in range(2)]
        all_tasks = [producer_task] + consumer_tasks
        
        results = await asyncio.gather(*all_tasks)
        
        end_time = time.time()
        actual_duration = end_time - start_time
        
        produced_count = results[0]
        total_processed = sum(results[1:])
        
        print(f"Sustained load test ran for {actual_duration:.2f} seconds")
        print(f"Produced: {produced_count} messages")
        print(f"Processed: {total_processed} messages")
        print(f"Processing rate: {total_processed / actual_duration:.1f} messages/second")
        
        # Verify reasonable processing performance
        assert total_processed > 0
        processing_rate = total_processed / actual_duration
        assert processing_rate > 10  # At least 10 messages per second
        
        # Check that most messages were processed (allowing for some in-flight)
        processing_efficiency = total_processed / produced_count if produced_count > 0 else 0
        assert processing_efficiency > 0.8  # At least 80% processed
        
        # Cleanup
        await redis_client.delete(stream_name)

    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self, redis_client):
        """Test Redis memory usage during high load."""
        stream_name = "test:memory_load"
        
        # Get initial memory usage
        initial_info = await redis_client.info("memory")
        initial_memory = initial_info["used_memory"]
        
        # Add large number of messages
        num_messages = 1000
        large_content = "x" * 1000  # 1KB per message
        
        for i in range(num_messages):
            message = {
                "task_id": f"memory_test_{i}",
                "content": large_content,
                "data": f"Additional data for message {i}"
            }
            await redis_client.xadd(stream_name, message)
        
        # Check memory usage after load
        after_info = await redis_client.info("memory")
        after_memory = after_info["used_memory"]
        
        memory_increase = after_memory - initial_memory
        memory_per_message = memory_increase / num_messages
        
        print(f"Memory increase: {memory_increase / 1024 / 1024:.2f} MB")
        print(f"Memory per message: {memory_per_message:.0f} bytes")
        
        # Verify reasonable memory usage (adjust based on your requirements)
        assert memory_per_message < 2000  # Less than 2KB per message overhead
        
        # Test stream trimming to manage memory
        # Trim to keep only last 100 messages
        trimmed = await redis_client.xtrim(stream_name, maxlen=100, approximate=True)
        
        # Check memory after trimming
        trimmed_info = await redis_client.info("memory")
        trimmed_memory = trimmed_info["used_memory"]
        
        memory_saved = after_memory - trimmed_memory
        print(f"Memory saved by trimming: {memory_saved / 1024 / 1024:.2f} MB")
        
        # Verify trimming reduced memory usage
        assert trimmed_memory < after_memory
        
        # Cleanup
        await redis_client.delete(stream_name)
