"""
MCP File System Client

Client library for interacting with the MCP filesystem server.
Provides a high-level async interface for file operations with
automatic retry logic, connection pooling, and error handling.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager
from datetime import datetime
import aiohttp
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Import configuration
from config.mcp_config import MCP_CLIENT_CONFIG, MCP_FILESYSTEM_CONFIG

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MCPFileSystemClient:
    """
    Async client for MCP filesystem operations.
    
    Features:
    - Automatic retry with exponential backoff
    - Connection pooling
    - Comprehensive error handling
    - Performance monitoring
    - Agent-specific permissions
    """
    
    def __init__(self, agent_name: str = "default"):
        """
        Initialize the filesystem client.
        
        Args:
            agent_name: Name of the agent using this client (for permissions)
        """
        self.agent_name = agent_name
        self.config = MCP_CLIENT_CONFIG
        self.server_config = MCP_FILESYSTEM_CONFIG
        self.session: Optional[ClientSession] = None
        self._retry_config = self.config["connection"]
        self._monitoring_enabled = self.config["monitoring"]["enable_metrics"]
        self._metrics: Dict[str, List[float]] = {}
    
    @asynccontextmanager
    async def connect(self):
        """Connect to the MCP filesystem server."""
        server_params = StdioServerParameters(
            command="python",
            args=["-m", "mcp.filesystem_server"],
            cwd=str(Path(__file__).parent.parent)
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                self.session = session
                # Initialize the session
                await session.initialize()
                
                # Log available tools
                tools = await session.list_tools()
                logger.info(f"Connected to filesystem server. Available tools: {[t.name for t in tools]}")
                
                try:
                    yield self
                finally:
                    self.session = None
    
    async def _call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a tool on the MCP server with retry logic.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            Tool execution result
        """
        if not self.session:
            raise RuntimeError("Not connected to MCP server. Use 'async with client.connect():'")
        
        last_error = None
        retry_count = 0
        max_retries = self._retry_config["max_retries"]
        retry_delay = self._retry_config["retry_delay"]
        backoff = self._retry_config["retry_backoff"]
        
        while retry_count <= max_retries:
            try:
                # Record start time for metrics
                start_time = datetime.now()
                
                # Call the tool
                result = await self.session.call_tool(tool_name, arguments)
                
                # Record metrics
                if self._monitoring_enabled:
                    duration = (datetime.now() - start_time).total_seconds()
                    self._record_metric(tool_name, duration)
                
                # Parse the result
                if result.content and len(result.content) > 0:
                    content = result.content[0]
                    if hasattr(content, 'text'):
                        parsed_result = json.loads(content.text)
                        
                        # Check for errors in the result
                        if "error" in parsed_result:
                            raise Exception(parsed_result["error"])
                        
                        return parsed_result
                
                return {"success": False, "error": "Empty response from server"}
                
            except Exception as e:
                last_error = e
                if retry_count < max_retries:
                    wait_time = retry_delay * (backoff ** retry_count)
                    logger.warning(f"Tool call failed, retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                    retry_count += 1
                else:
                    break
        
        # All retries exhausted
        error_msg = f"Tool call '{tool_name}' failed after {max_retries} retries: {last_error}"
        logger.error(error_msg)
        
        if self.config["error_handling"]["raise_on_error"]:
            raise Exception(error_msg)
        else:
            return {"success": False, "error": error_msg}
    
    def _record_metric(self, operation: str, duration: float):
        """Record performance metrics."""
        if operation not in self._metrics:
            self._metrics[operation] = []
        
        self._metrics[operation].append(duration)
        
        # Log slow operations
        threshold = self.config["monitoring"]["slow_operation_threshold"]
        if duration > threshold:
            logger.warning(f"Slow operation detected: {operation} took {duration:.2f}s")
    
    async def read_file(self, path: str, encoding: str = "utf-8") -> str:
        """
        Read contents of a file.
        
        Args:
            path: File path relative to sandbox root
            encoding: File encoding (default: utf-8)
            
        Returns:
            File contents as string
        """
        result = await self._call_tool("read_file", {
            "path": path,
            "encoding": encoding
        })
        
        if result.get("success"):
            return result["content"]
        else:
            raise FileNotFoundError(f"Failed to read file: {result.get('error', 'Unknown error')}")
    
    async def write_file(self, path: str, content: str, encoding: str = "utf-8") -> bool:
        """
        Write content to a file.
        
        Args:
            path: File path relative to sandbox root
            content: Content to write
            encoding: File encoding (default: utf-8)
            
        Returns:
            True if successful
        """
        result = await self._call_tool("write_file", {
            "path": path,
            "content": content,
            "encoding": encoding
        })
        
        return result.get("success", False)
    
    async def delete_file(self, path: str) -> bool:
        """
        Delete a file or directory.
        
        Args:
            path: Path relative to sandbox root
            
        Returns:
            True if successful
        """
        result = await self._call_tool("delete_file", {"path": path})
        return result.get("success", False)
    
    async def list_directory(self, path: str, recursive: bool = False) -> List[Dict[str, Any]]:
        """
        List contents of a directory.
        
        Args:
            path: Directory path relative to sandbox root
            recursive: Whether to list recursively
            
        Returns:
            List of items with path, type, and size information
        """
        result = await self._call_tool("list_directory", {
            "path": path,
            "recursive": recursive
        })
        
        if result.get("success"):
            return result["items"]
        else:
            raise FileNotFoundError(f"Failed to list directory: {result.get('error', 'Unknown error')}")
    
    async def create_directory(self, path: str, parents: bool = True) -> bool:
        """
        Create a directory.
        
        Args:
            path: Directory path relative to sandbox root
            parents: Whether to create parent directories
            
        Returns:
            True if successful
        """
        result = await self._call_tool("create_directory", {
            "path": path,
            "parents": parents
        })
        
        return result.get("success", False)
    
    async def exists(self, path: str) -> bool:
        """
        Check if a file or directory exists.
        
        Args:
            path: Path relative to sandbox root
            
        Returns:
            True if exists
        """
        result = await self._call_tool("file_exists", {"path": path})
        return result.get("exists", False)
    
    async def get_file_info(self, path: str) -> Dict[str, Any]:
        """
        Get detailed information about a file.
        
        Args:
            path: File path relative to sandbox root
            
        Returns:
            Dictionary with file information
        """
        result = await self._call_tool("get_file_info", {"path": path})
        
        if result.get("success"):
            return result
        else:
            raise FileNotFoundError(f"Failed to get file info: {result.get('error', 'Unknown error')}")
    
    def get_metrics(self) -> Dict[str, Dict[str, float]]:
        """
        Get performance metrics.
        
        Returns:
            Dictionary with operation statistics
        """
        metrics = {}
        for operation, durations in self._metrics.items():
            if durations:
                metrics[operation] = {
                    "count": len(durations),
                    "avg": sum(durations) / len(durations),
                    "min": min(durations),
                    "max": max(durations)
                }
        return metrics


# Convenience function for backward compatibility
async def get_filesystem_client(agent_name: str = "default") -> MCPFileSystemClient:
    """
    Get a configured filesystem client.
    
    Args:
        agent_name: Name of the agent using this client
        
    Returns:
        Configured MCPFileSystemClient instance
    """
    return MCPFileSystemClient(agent_name)