"""
Streaming Response Handler for MVP Incremental Workflow

Provides real-time streaming of agent responses to improve user experience
and reduce memory consumption for large outputs.
"""

import asyncio
from typing import AsyncGenerator, Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
import json
from enum import Enum

from workflows.logger import workflow_logger as logger


class StreamType(Enum):
    """Types of streaming content."""
    CODE = "code"
    LOG = "log"
    TEST_OUTPUT = "test_output"
    REVIEW_FEEDBACK = "review_feedback"
    PROGRESS = "progress"
    ERROR = "error"


@dataclass
class StreamChunk:
    """A single chunk of streamed data."""
    type: StreamType
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "type": self.type.value,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class StreamingMetrics:
    """Metrics for streaming performance."""
    total_chunks: int = 0
    total_bytes: int = 0
    stream_duration_seconds: float = 0.0
    chunks_per_second: float = 0.0
    average_chunk_size: int = 0
    buffer_overflows: int = 0
    
    def calculate_metrics(self):
        """Calculate derived metrics."""
        if self.stream_duration_seconds > 0:
            self.chunks_per_second = self.total_chunks / self.stream_duration_seconds
        if self.total_chunks > 0:
            self.average_chunk_size = self.total_bytes // self.total_chunks


class StreamingResponseHandler:
    """
    Handles streaming of agent responses with buffering and flow control.
    """
    
    def __init__(self,
                 buffer_size: int = 100,
                 flush_interval: float = 0.1,
                 max_chunk_size: int = 4096):
        """
        Initialize streaming handler.
        
        Args:
            buffer_size: Maximum chunks to buffer before blocking
            flush_interval: Seconds between automatic buffer flushes
            max_chunk_size: Maximum size of a single chunk in bytes
        """
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        self.max_chunk_size = max_chunk_size
        
        # Streaming state
        self._buffer: asyncio.Queue = asyncio.Queue(maxsize=buffer_size)
        self._subscribers: List[Callable[[StreamChunk], None]] = []
        self._metrics = StreamingMetrics()
        self._streaming = False
        self._flush_task: Optional[asyncio.Task] = None
        
    async def start_streaming(self):
        """Start the streaming process."""
        if self._streaming:
            return
            
        self._streaming = True
        self._metrics = StreamingMetrics()
        self._start_time = datetime.now()
        
        # Start flush task
        self._flush_task = asyncio.create_task(self._flush_loop())
        logger.info("Streaming started")
        
    async def stop_streaming(self):
        """Stop the streaming process."""
        if not self._streaming:
            return
            
        self._streaming = False
        
        # Flush remaining chunks first
        await self._flush_buffer()
        
        # Cancel flush task
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
            self._flush_task = None
                
        # Calculate final metrics
        duration = (datetime.now() - self._start_time).total_seconds()
        self._metrics.stream_duration_seconds = duration
        self._metrics.calculate_metrics()
        
        logger.info(f"Streaming stopped. Metrics: {self._metrics.total_chunks} chunks, "
                   f"{self._metrics.total_bytes} bytes, {duration:.1f}s")
        
    async def stream_chunk(self, chunk: StreamChunk):
        """
        Stream a single chunk of data.
        
        Args:
            chunk: The chunk to stream
        """
        if not self._streaming:
            await self.start_streaming()
            
        # Update metrics
        chunk_size = len(chunk.content.encode())
        self._metrics.total_chunks += 1
        self._metrics.total_bytes += chunk_size
        
        # Split large chunks
        if chunk_size > self.max_chunk_size:
            await self._stream_large_chunk(chunk)
        else:
            try:
                self._buffer.put_nowait(chunk)
            except asyncio.QueueFull:
                self._metrics.buffer_overflows += 1
                logger.warning("Buffer overflow - dropping chunk")
                
    async def _stream_large_chunk(self, chunk: StreamChunk):
        """Split and stream a large chunk."""
        content = chunk.content
        chunk_count = 0
        
        while content:
            # Take a slice
            slice_content = content[:self.max_chunk_size]
            content = content[self.max_chunk_size:]
            
            # Create sub-chunk
            sub_chunk = StreamChunk(
                type=chunk.type,
                content=slice_content,
                metadata={
                    **chunk.metadata,
                    "chunk_index": chunk_count,
                    "is_partial": len(content) > 0
                },
                timestamp=chunk.timestamp
            )
            
            try:
                self._buffer.put_nowait(sub_chunk)
            except asyncio.QueueFull:
                self._metrics.buffer_overflows += 1
                logger.warning(f"Buffer overflow - dropping chunk {chunk_count}")
            chunk_count += 1
            
    async def _flush_loop(self):
        """Periodically flush the buffer."""
        while self._streaming:
            await asyncio.sleep(self.flush_interval)
            await self._flush_buffer()
            
    async def _flush_buffer(self):
        """Flush all chunks in the buffer to subscribers."""
        chunks_flushed = 0
        
        while not self._buffer.empty():
            try:
                chunk = self._buffer.get_nowait()
                await self._notify_subscribers(chunk)
                chunks_flushed += 1
            except asyncio.QueueEmpty:
                break
                
        if chunks_flushed > 0:
            logger.debug(f"Flushed {chunks_flushed} chunks")
            
    async def _notify_subscribers(self, chunk: StreamChunk):
        """Notify all subscribers of a new chunk."""
        for subscriber in self._subscribers:
            try:
                if asyncio.iscoroutinefunction(subscriber):
                    await subscriber(chunk)
                else:
                    subscriber(chunk)
            except Exception as e:
                logger.error(f"Subscriber error: {e}")
                
    def subscribe(self, callback: Callable[[StreamChunk], None]):
        """
        Subscribe to streaming updates.
        
        Args:
            callback: Function to call with each chunk
        """
        self._subscribers.append(callback)
        
    def unsubscribe(self, callback: Callable[[StreamChunk], None]):
        """
        Unsubscribe from streaming updates.
        
        Args:
            callback: Function to remove
        """
        if callback in self._subscribers:
            self._subscribers.remove(callback)
            
    async def stream_code_generation(self, 
                                    code_generator: AsyncGenerator[str, None],
                                    filename: str) -> str:
        """
        Stream code generation from an async generator.
        
        Args:
            code_generator: Async generator yielding code chunks
            filename: Name of the file being generated
            
        Returns:
            Complete generated code
        """
        accumulated_code = []
        
        async for code_chunk in code_generator:
            accumulated_code.append(code_chunk)
            
            # Stream the chunk
            await self.stream_chunk(StreamChunk(
                type=StreamType.CODE,
                content=code_chunk,
                metadata={"filename": filename}
            ))
        
        # Ensure chunks are flushed
        await self._flush_buffer()
            
        return "".join(accumulated_code)
        
    async def stream_test_execution(self,
                                  test_output: AsyncGenerator[str, None],
                                  test_name: str) -> List[str]:
        """
        Stream test execution output.
        
        Args:
            test_output: Async generator yielding test output lines
            test_name: Name of the test being executed
            
        Returns:
            All output lines
        """
        output_lines = []
        
        async for line in test_output:
            output_lines.append(line)
            
            # Determine if this is an error line
            is_error = any(keyword in line.lower() for keyword in 
                          ["error", "failed", "assertion", "exception"])
            
            # Stream the line
            await self.stream_chunk(StreamChunk(
                type=StreamType.TEST_OUTPUT,
                content=line,
                metadata={
                    "test_name": test_name,
                    "is_error": is_error
                }
            ))
        
        # Ensure chunks are flushed
        await self._flush_buffer()
            
        return output_lines
        
    async def stream_progress(self,
                            message: str,
                            progress: float,
                            feature_id: Optional[str] = None):
        """
        Stream a progress update.
        
        Args:
            message: Progress message
            progress: Progress value (0.0 to 1.0)
            feature_id: Optional feature ID
        """
        await self.stream_chunk(StreamChunk(
            type=StreamType.PROGRESS,
            content=message,
            metadata={
                "progress": progress,
                "feature_id": feature_id
            }
        ))
        
    def get_metrics(self) -> Dict[str, Any]:
        """Get streaming metrics."""
        return {
            "total_chunks": self._metrics.total_chunks,
            "total_bytes": self._metrics.total_bytes,
            "stream_duration_seconds": self._metrics.stream_duration_seconds,
            "chunks_per_second": self._metrics.chunks_per_second,
            "average_chunk_size": self._metrics.average_chunk_size,
            "buffer_overflows": self._metrics.buffer_overflows,
            "subscriber_count": len(self._subscribers)
        }


class StreamingCodeAccumulator:
    """
    Accumulates streamed code chunks into complete files.
    """
    
    def __init__(self):
        self._files: Dict[str, List[str]] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}
        
    def add_chunk(self, filename: str, chunk: str, metadata: Optional[Dict[str, Any]] = None):
        """Add a code chunk to a file."""
        if filename not in self._files:
            self._files[filename] = []
            self._metadata[filename] = metadata or {}
            
        self._files[filename].append(chunk)
        
    def get_file(self, filename: str) -> Optional[str]:
        """Get the accumulated content of a file."""
        if filename in self._files:
            return "".join(self._files[filename])
        return None
        
    def get_all_files(self) -> Dict[str, str]:
        """Get all accumulated files."""
        return {
            filename: "".join(chunks)
            for filename, chunks in self._files.items()
        }
        
    def clear(self):
        """Clear all accumulated content."""
        self._files.clear()
        self._metadata.clear()


def create_console_subscriber(verbose: bool = True) -> Callable[[StreamChunk], None]:
    """
    Create a console subscriber for debugging.
    
    Args:
        verbose: Whether to show all chunks or just important ones
        
    Returns:
        Subscriber function
    """
    def console_subscriber(chunk: StreamChunk):
        if chunk.type == StreamType.ERROR:
            print(f"❌ ERROR: {chunk.content}")
        elif chunk.type == StreamType.PROGRESS:
            progress = chunk.metadata.get("progress", 0) * 100
            print(f"📊 PROGRESS [{progress:.0f}%]: {chunk.content}")
        elif verbose:
            if chunk.type == StreamType.CODE:
                print(f"💻 CODE: {chunk.content[:50]}...")
            elif chunk.type == StreamType.TEST_OUTPUT:
                if chunk.metadata.get("is_error"):
                    print(f"🧪 TEST ERROR: {chunk.content}")
                elif verbose:
                    print(f"🧪 TEST: {chunk.content}")
                    
    return console_subscriber


async def demo_streaming():
    """Demonstrate streaming functionality."""
    handler = StreamingResponseHandler()
    
    # Add console subscriber
    handler.subscribe(create_console_subscriber(verbose=True))
    
    await handler.start_streaming()
    
    # Simulate code generation
    async def generate_code():
        code_parts = [
            "def calculate_sum(a, b):\n",
            "    \"\"\"Calculate the sum of two numbers.\"\"\"\n",
            "    result = a + b\n",
            "    return result\n"
        ]
        for part in code_parts:
            yield part
            await asyncio.sleep(0.1)
            
    # Stream code generation
    code = await handler.stream_code_generation(
        generate_code(),
        "calculator.py"
    )
    
    # Stream progress
    await handler.stream_progress("Testing implementation", 0.5, "feature_calc")
    
    # Simulate test output
    async def generate_test_output():
        lines = [
            "Running tests...",
            "test_calculate_sum PASSED",
            "test_edge_cases FAILED - AssertionError",
            "1 passed, 1 failed"
        ]
        for line in lines:
            yield line
            await asyncio.sleep(0.05)
            
    # Stream test execution
    output = await handler.stream_test_execution(
        generate_test_output(),
        "test_calculator"
    )
    
    await handler.stop_streaming()
    
    # Show metrics
    print(f"\nStreaming metrics: {handler.get_metrics()}")
    print(f"Generated code:\n{code}")
    print(f"Test output: {output}")


if __name__ == "__main__":
    asyncio.run(demo_streaming())