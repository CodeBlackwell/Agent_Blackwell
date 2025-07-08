"""
Unit tests for the MCP File System Client

Tests client functionality, retry logic, error handling, and metrics.
"""

import unittest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
import tempfile
from pathlib import Path

# Add project root to path
import sys
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from shared.filesystem_client import MCPFileSystemClient, get_filesystem_client
from mcp.types import TextContent


class TestMCPFileSystemClient(unittest.TestCase):
    """Test the MCP File System Client functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.client = MCPFileSystemClient("test_agent")
        
        # Create mock session
        self.mock_session = Mock()
        self.client.session = self.mock_session
        
        # Mock successful response
        self.mock_response = Mock()
        self.mock_response.content = [Mock(text=json.dumps({
            "success": True,
            "path": "test.txt",
            "content": "Test content"
        }))]
    
    async def test_client_initialization(self):
        """Test client initialization."""
        client = MCPFileSystemClient("test_agent")
        
        self.assertEqual(client.agent_name, "test_agent")
        self.assertIsNotNone(client.config)
        self.assertIsNotNone(client.server_config)
        self.assertIsNone(client.session)
        self.assertEqual(client._metrics, {})
    
    async def test_call_tool_success(self):
        """Test successful tool call."""
        # Setup mock
        self.mock_session.call_tool = AsyncMock(return_value=self.mock_response)
        
        # Call tool
        result = await self.client._call_tool("read_file", {"path": "test.txt"})
        
        # Verify
        self.assertTrue(result["success"])
        self.assertEqual(result["path"], "test.txt")
        self.mock_session.call_tool.assert_called_once_with("read_file", {"path": "test.txt"})
    
    async def test_call_tool_retry_logic(self):
        """Test retry logic on failures."""
        # Setup mock to fail twice then succeed
        error_response = Mock()
        error_response.content = [Mock(text=json.dumps({"error": "Connection failed"}))]
        
        self.mock_session.call_tool = AsyncMock(side_effect=[
            Exception("Network error"),
            Exception("Timeout"),
            self.mock_response
        ])
        
        # Reduce retry delay for testing
        self.client._retry_config["retry_delay"] = 0.01
        
        # Call tool
        result = await self.client._call_tool("read_file", {"path": "test.txt"})
        
        # Verify
        self.assertTrue(result["success"])
        self.assertEqual(self.mock_session.call_tool.call_count, 3)
    
    async def test_call_tool_max_retries_exceeded(self):
        """Test behavior when max retries are exceeded."""
        # Setup mock to always fail
        self.mock_session.call_tool = AsyncMock(side_effect=Exception("Persistent error"))
        
        # Reduce retry delay for testing
        self.client._retry_config["retry_delay"] = 0.01
        self.client._retry_config["max_retries"] = 2
        
        # Call tool and expect exception
        with self.assertRaises(Exception) as context:
            await self.client._call_tool("read_file", {"path": "test.txt"})
        
        self.assertIn("failed after 2 retries", str(context.exception))
        self.assertEqual(self.mock_session.call_tool.call_count, 3)  # Initial + 2 retries
    
    async def test_call_tool_no_raise_on_error(self):
        """Test behavior when raise_on_error is False."""
        # Setup
        self.client.config["error_handling"]["raise_on_error"] = False
        self.mock_session.call_tool = AsyncMock(side_effect=Exception("Error"))
        self.client._retry_config["retry_delay"] = 0.01
        self.client._retry_config["max_retries"] = 0
        
        # Call tool
        result = await self.client._call_tool("read_file", {"path": "test.txt"})
        
        # Verify
        self.assertFalse(result["success"])
        self.assertIn("error", result)
    
    async def test_read_file_success(self):
        """Test successful file reading."""
        # Setup mock
        self.mock_session.call_tool = AsyncMock(return_value=Mock(
            content=[Mock(text=json.dumps({
                "success": True,
                "content": "File contents",
                "path": "test.txt"
            }))]
        ))
        
        # Read file
        content = await self.client.read_file("test.txt")
        
        # Verify
        self.assertEqual(content, "File contents")
        self.mock_session.call_tool.assert_called_once_with("read_file", {
            "path": "test.txt",
            "encoding": "utf-8"
        })
    
    async def test_read_file_not_found(self):
        """Test reading non-existent file."""
        # Setup mock
        self.mock_session.call_tool = AsyncMock(return_value=Mock(
            content=[Mock(text=json.dumps({
                "success": False,
                "error": "File not found"
            }))]
        ))
        
        # Read file and expect exception
        with self.assertRaises(FileNotFoundError):
            await self.client.read_file("nonexistent.txt")
    
    async def test_write_file_success(self):
        """Test successful file writing."""
        # Setup mock
        self.mock_session.call_tool = AsyncMock(return_value=Mock(
            content=[Mock(text=json.dumps({
                "success": True,
                "path": "new_file.txt",
                "size": 12
            }))]
        ))
        
        # Write file
        result = await self.client.write_file("new_file.txt", "New content!")
        
        # Verify
        self.assertTrue(result)
        self.mock_session.call_tool.assert_called_once_with("write_file", {
            "path": "new_file.txt",
            "content": "New content!",
            "encoding": "utf-8"
        })
    
    async def test_delete_file_success(self):
        """Test successful file deletion."""
        # Setup mock
        self.mock_session.call_tool = AsyncMock(return_value=Mock(
            content=[Mock(text=json.dumps({
                "success": True,
                "deleted": True
            }))]
        ))
        
        # Delete file
        result = await self.client.delete_file("old_file.txt")
        
        # Verify
        self.assertTrue(result)
        self.mock_session.call_tool.assert_called_once_with("delete_file", {"path": "old_file.txt"})
    
    async def test_list_directory_success(self):
        """Test successful directory listing."""
        # Setup mock
        items = [
            {"path": "dir/file1.txt", "type": "file", "size": 100},
            {"path": "dir/file2.txt", "type": "file", "size": 200},
            {"path": "dir/subdir", "type": "directory", "size": None}
        ]
        self.mock_session.call_tool = AsyncMock(return_value=Mock(
            content=[Mock(text=json.dumps({
                "success": True,
                "items": items,
                "count": 3
            }))]
        ))
        
        # List directory
        result = await self.client.list_directory("dir")
        
        # Verify
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]["path"], "dir/file1.txt")
        self.mock_session.call_tool.assert_called_once_with("list_directory", {
            "path": "dir",
            "recursive": False
        })
    
    async def test_create_directory_success(self):
        """Test successful directory creation."""
        # Setup mock
        self.mock_session.call_tool = AsyncMock(return_value=Mock(
            content=[Mock(text=json.dumps({
                "success": True,
                "created": True
            }))]
        ))
        
        # Create directory
        result = await self.client.create_directory("new_dir/sub_dir")
        
        # Verify
        self.assertTrue(result)
        self.mock_session.call_tool.assert_called_once_with("create_directory", {
            "path": "new_dir/sub_dir",
            "parents": True
        })
    
    async def test_exists_true(self):
        """Test checking existence of existing file."""
        # Setup mock
        self.mock_session.call_tool = AsyncMock(return_value=Mock(
            content=[Mock(text=json.dumps({
                "success": True,
                "exists": True,
                "type": "file"
            }))]
        ))
        
        # Check existence
        result = await self.client.exists("existing.txt")
        
        # Verify
        self.assertTrue(result)
        self.mock_session.call_tool.assert_called_once_with("file_exists", {"path": "existing.txt"})
    
    async def test_get_file_info_success(self):
        """Test getting file information."""
        # Setup mock
        file_info = {
            "success": True,
            "path": "test.txt",
            "type": "file",
            "size": 1024,
            "created": "2024-01-01T00:00:00",
            "modified": "2024-01-02T00:00:00",
            "permissions": "644"
        }
        self.mock_session.call_tool = AsyncMock(return_value=Mock(
            content=[Mock(text=json.dumps(file_info))]
        ))
        
        # Get file info
        result = await self.client.get_file_info("test.txt")
        
        # Verify
        self.assertEqual(result["size"], 1024)
        self.assertEqual(result["type"], "file")
        self.mock_session.call_tool.assert_called_once_with("get_file_info", {"path": "test.txt"})
    
    async def test_metrics_recording(self):
        """Test performance metrics recording."""
        # Enable metrics
        self.client._monitoring_enabled = True
        
        # Setup mock with delay
        async def delayed_response(*args, **kwargs):
            await asyncio.sleep(0.1)
            return self.mock_response
        
        self.mock_session.call_tool = delayed_response
        
        # Make several calls
        await self.client._call_tool("read_file", {"path": "test1.txt"})
        await self.client._call_tool("read_file", {"path": "test2.txt"})
        await self.client._call_tool("write_file", {"path": "test3.txt", "content": "data"})
        
        # Get metrics
        metrics = self.client.get_metrics()
        
        # Verify
        self.assertIn("read_file", metrics)
        self.assertIn("write_file", metrics)
        self.assertEqual(metrics["read_file"]["count"], 2)
        self.assertEqual(metrics["write_file"]["count"], 1)
        self.assertGreater(metrics["read_file"]["avg"], 0.09)  # Should be around 0.1s
    
    async def test_not_connected_error(self):
        """Test error when client is not connected."""
        client = MCPFileSystemClient("test_agent")
        client.session = None
        
        with self.assertRaises(RuntimeError) as context:
            await client._call_tool("read_file", {"path": "test.txt"})
        
        self.assertIn("Not connected to MCP server", str(context.exception))
    
    @patch('shared.filesystem_client.stdio_client')
    @patch('shared.filesystem_client.ClientSession')
    async def test_context_manager(self, mock_client_session, mock_stdio_client):
        """Test client context manager."""
        # Setup mocks
        mock_read = Mock()
        mock_write = Mock()
        mock_stdio_client.return_value.__aenter__.return_value = (mock_read, mock_write)
        
        mock_session = AsyncMock()
        mock_session.list_tools = AsyncMock(return_value=[
            Mock(name="read_file"),
            Mock(name="write_file")
        ])
        mock_client_session.return_value.__aenter__.return_value = mock_session
        
        # Use context manager
        async with MCPFileSystemClient("test_agent").connect() as client:
            self.assertIsNotNone(client.session)
            self.assertEqual(client.session, mock_session)
        
        # Verify cleanup
        self.assertIsNone(client.session)
    
    async def test_get_filesystem_client(self):
        """Test convenience function."""
        client = await get_filesystem_client("test_agent")
        self.assertIsInstance(client, MCPFileSystemClient)
        self.assertEqual(client.agent_name, "test_agent")


if __name__ == "__main__":
    # Run async tests
    unittest.main()