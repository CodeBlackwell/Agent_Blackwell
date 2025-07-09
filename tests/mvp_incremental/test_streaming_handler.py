"""
Unit tests for the streaming response handler.

Tests streaming functionality, buffering, and performance.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime
import time

from workflows.mvp_incremental.streaming_handler import (
    StreamType, StreamChunk, StreamingMetrics, StreamingResponseHandler,
    StreamingCodeAccumulator, create_console_subscriber
)


class TestStreamChunk:
    """Test the StreamChunk dataclass."""
    
    def test_chunk_initialization(self):
        """Test chunk initialization."""
        chunk = StreamChunk(
            type=StreamType.CODE,
            content="def hello():",
            metadata={"filename": "test.py"}
        )
        
        assert chunk.type == StreamType.CODE
        assert chunk.content == "def hello():"
        assert chunk.metadata["filename"] == "test.py"
        assert isinstance(chunk.timestamp, datetime)
    
    def test_chunk_to_dict(self):
        """Test chunk serialization."""
        chunk = StreamChunk(
            type=StreamType.PROGRESS,
            content="Processing...",
            metadata={"progress": 0.5}
        )
        
        data = chunk.to_dict()
        assert data["type"] == "progress"
        assert data["content"] == "Processing..."
        assert data["metadata"]["progress"] == 0.5
        assert "timestamp" in data


class TestStreamingMetrics:
    """Test the StreamingMetrics dataclass."""
    
    def test_metrics_calculation(self):
        """Test metrics calculation."""
        metrics = StreamingMetrics()
        metrics.total_chunks = 100
        metrics.total_bytes = 10000
        metrics.stream_duration_seconds = 10.0
        
        metrics.calculate_metrics()
        
        assert metrics.chunks_per_second == 10.0
        assert metrics.average_chunk_size == 100


class TestStreamingResponseHandler:
    """Test the StreamingResponseHandler class."""
    
    @pytest.fixture
    def handler(self):
        """Create a test handler."""
        return StreamingResponseHandler(
            buffer_size=10,
            flush_interval=0.05,
            max_chunk_size=100
        )
    
    @pytest.mark.asyncio
    async def test_start_stop_streaming(self, handler):
        """Test starting and stopping streaming."""
        assert not handler._streaming
        
        await handler.start_streaming()
        assert handler._streaming
        assert handler._flush_task is not None
        
        await handler.stop_streaming()
        assert not handler._streaming
        assert handler._metrics.stream_duration_seconds > 0
    
    @pytest.mark.asyncio
    async def test_stream_single_chunk(self, handler):
        """Test streaming a single chunk."""
        # Subscribe to chunks
        received_chunks = []
        handler.subscribe(lambda chunk: received_chunks.append(chunk))
        
        # Stream a chunk
        chunk = StreamChunk(StreamType.LOG, "Test message")
        await handler.stream_chunk(chunk)
        
        # Wait for flush
        await asyncio.sleep(0.1)
        
        assert len(received_chunks) == 1
        assert received_chunks[0].content == "Test message"
        
        await handler.stop_streaming()
    
    @pytest.mark.asyncio
    async def test_stream_large_chunk(self, handler):
        """Test streaming a large chunk that needs splitting."""
        received_chunks = []
        handler.subscribe(lambda chunk: received_chunks.append(chunk))
        
        # Create large content
        large_content = "x" * 250  # Larger than max_chunk_size (100)
        chunk = StreamChunk(StreamType.CODE, large_content)
        
        await handler.stream_chunk(chunk)
        await asyncio.sleep(0.1)
        
        # Should be split into 3 chunks
        assert len(received_chunks) == 3
        assert len(received_chunks[0].content) == 100
        assert len(received_chunks[1].content) == 100
        assert len(received_chunks[2].content) == 50
        
        # Check metadata
        assert received_chunks[0].metadata["chunk_index"] == 0
        assert received_chunks[0].metadata["is_partial"] == True
        assert received_chunks[2].metadata["is_partial"] == False
        
        await handler.stop_streaming()
    
    @pytest.mark.asyncio
    async def test_buffer_overflow(self, handler):
        """Test handling of buffer overflow."""
        # Create handler with very small buffer
        small_handler = StreamingResponseHandler(buffer_size=2)
        
        # Don't subscribe so chunks aren't consumed
        await small_handler.start_streaming()
        
        # Fill buffer beyond capacity
        for i in range(5):
            chunk = StreamChunk(StreamType.LOG, f"Message {i}")
            await small_handler.stream_chunk(chunk)
        
        # Check overflow metric
        assert small_handler._metrics.buffer_overflows > 0
        
        await small_handler.stop_streaming()
    
    @pytest.mark.asyncio
    async def test_multiple_subscribers(self, handler):
        """Test multiple subscribers."""
        received1 = []
        received2 = []
        
        sub1 = lambda chunk: received1.append(chunk)
        sub2 = lambda chunk: received2.append(chunk)
        
        handler.subscribe(sub1)
        handler.subscribe(sub2)
        
        chunk = StreamChunk(StreamType.PROGRESS, "Update")
        await handler.stream_chunk(chunk)
        await asyncio.sleep(0.1)
        
        assert len(received1) == 1
        assert len(received2) == 1
        
        # Test unsubscribe
        handler.unsubscribe(sub1)
        
        chunk2 = StreamChunk(StreamType.PROGRESS, "Update 2")
        await handler.stream_chunk(chunk2)
        await asyncio.sleep(0.1)
        
        assert len(received1) == 1  # No new chunk
        assert len(received2) == 2  # Got new chunk
        
        await handler.stop_streaming()
    
    @pytest.mark.asyncio
    async def test_async_subscriber(self, handler):
        """Test async subscriber."""
        received = []
        
        async def async_subscriber(chunk):
            await asyncio.sleep(0.01)  # Simulate async work
            received.append(chunk)
        
        handler.subscribe(async_subscriber)
        
        chunk = StreamChunk(StreamType.LOG, "Async test")
        await handler.stream_chunk(chunk)
        await asyncio.sleep(0.2)
        
        assert len(received) == 1
        
        await handler.stop_streaming()
    
    @pytest.mark.asyncio
    async def test_stream_code_generation(self, handler):
        """Test streaming code generation."""
        received = []
        handler.subscribe(lambda chunk: received.append(chunk))
        
        async def generate():
            yield "def test():\n"
            yield "    return 42\n"
        
        code = await handler.stream_code_generation(generate(), "test.py")
        
        assert code == "def test():\n    return 42\n"
        assert len(received) == 2
        assert all(chunk.type == StreamType.CODE for chunk in received)
        assert all(chunk.metadata["filename"] == "test.py" for chunk in received)
        
        await handler.stop_streaming()
    
    @pytest.mark.asyncio
    async def test_stream_test_execution(self, handler):
        """Test streaming test execution."""
        received = []
        handler.subscribe(lambda chunk: received.append(chunk))
        
        async def test_output():
            yield "Running tests..."
            yield "test_one PASSED"
            yield "test_two FAILED - AssertionError"
        
        lines = await handler.stream_test_execution(test_output(), "test_suite")
        
        assert len(lines) == 3
        assert len(received) == 3
        
        # Check error detection
        assert not received[0].metadata["is_error"]
        assert not received[1].metadata["is_error"]
        assert received[2].metadata["is_error"]
        
        await handler.stop_streaming()
    
    @pytest.mark.asyncio
    async def test_stream_progress(self, handler):
        """Test streaming progress updates."""
        received = []
        handler.subscribe(lambda chunk: received.append(chunk))
        
        await handler.stream_progress("Starting", 0.0, "feature1")
        await handler.stream_progress("Half way", 0.5, "feature1")
        await handler.stream_progress("Complete", 1.0, "feature1")
        
        await asyncio.sleep(0.1)
        
        assert len(received) == 3
        assert all(chunk.type == StreamType.PROGRESS for chunk in received)
        assert received[0].metadata["progress"] == 0.0
        assert received[1].metadata["progress"] == 0.5
        assert received[2].metadata["progress"] == 1.0
        
        await handler.stop_streaming()
    
    @pytest.mark.asyncio
    async def test_get_metrics(self, handler):
        """Test metrics retrieval."""
        # Stream some chunks
        for i in range(5):
            chunk = StreamChunk(StreamType.LOG, f"Message {i}")
            await handler.stream_chunk(chunk)
        
        await asyncio.sleep(0.1)
        await handler.stop_streaming()
        
        metrics = handler.get_metrics()
        assert metrics["total_chunks"] == 5
        assert metrics["total_bytes"] > 0
        assert metrics["chunks_per_second"] > 0
        assert metrics["subscriber_count"] == 0


class TestStreamingCodeAccumulator:
    """Test the StreamingCodeAccumulator class."""
    
    def test_add_and_get_chunks(self):
        """Test adding and retrieving chunks."""
        acc = StreamingCodeAccumulator()
        
        acc.add_chunk("main.py", "def main():\n")
        acc.add_chunk("main.py", "    print('Hello')\n")
        acc.add_chunk("test.py", "def test():\n")
        
        assert acc.get_file("main.py") == "def main():\n    print('Hello')\n"
        assert acc.get_file("test.py") == "def test():\n"
        assert acc.get_file("missing.py") is None
    
    def test_get_all_files(self):
        """Test getting all accumulated files."""
        acc = StreamingCodeAccumulator()
        
        acc.add_chunk("file1.py", "content1")
        acc.add_chunk("file2.py", "content2")
        
        all_files = acc.get_all_files()
        assert len(all_files) == 2
        assert all_files["file1.py"] == "content1"
        assert all_files["file2.py"] == "content2"
    
    def test_clear(self):
        """Test clearing accumulator."""
        acc = StreamingCodeAccumulator()
        
        acc.add_chunk("file.py", "content")
        assert len(acc.get_all_files()) == 1
        
        acc.clear()
        assert len(acc.get_all_files()) == 0


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_create_console_subscriber_verbose(self, capsys):
        """Test console subscriber in verbose mode."""
        subscriber = create_console_subscriber(verbose=True)
        
        # Test different chunk types
        subscriber(StreamChunk(StreamType.ERROR, "Error message"))
        subscriber(StreamChunk(StreamType.PROGRESS, "Working", {"progress": 0.5}))
        subscriber(StreamChunk(StreamType.CODE, "def long_function_name():" + "x" * 50))
        
        captured = capsys.readouterr()
        assert "❌ ERROR: Error message" in captured.out
        assert "📊 PROGRESS [50%]: Working" in captured.out
        assert "💻 CODE: def long_function_name()" in captured.out
        assert "..." in captured.out  # Truncation
    
    def test_create_console_subscriber_quiet(self, capsys):
        """Test console subscriber in quiet mode."""
        subscriber = create_console_subscriber(verbose=False)
        
        # Only errors and progress should show
        subscriber(StreamChunk(StreamType.CODE, "code"))
        subscriber(StreamChunk(StreamType.ERROR, "Error"))
        subscriber(StreamChunk(StreamType.PROGRESS, "Progress", {"progress": 0.5}))
        
        captured = capsys.readouterr()
        assert "CODE" not in captured.out
        assert "❌ ERROR: Error" in captured.out
        assert "📊 PROGRESS [50%]: Progress" in captured.out


@pytest.mark.asyncio
async def test_concurrent_streaming():
    """Test concurrent streaming from multiple sources."""
    handler = StreamingResponseHandler()
    received = []
    handler.subscribe(lambda chunk: received.append(chunk))
    
    async def stream_source1():
        for i in range(5):
            await handler.stream_chunk(StreamChunk(StreamType.LOG, f"Source1-{i}"))
            await asyncio.sleep(0.01)
    
    async def stream_source2():
        for i in range(5):
            await handler.stream_chunk(StreamChunk(StreamType.LOG, f"Source2-{i}"))
            await asyncio.sleep(0.01)
    
    # Run sources concurrently
    await asyncio.gather(stream_source1(), stream_source2())
    await asyncio.sleep(0.1)
    
    assert len(received) == 10
    
    # Check that chunks from both sources are present
    source1_chunks = [c for c in received if "Source1" in c.content]
    source2_chunks = [c for c in received if "Source2" in c.content]
    assert len(source1_chunks) == 5
    assert len(source2_chunks) == 5
    
    await handler.stop_streaming()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])