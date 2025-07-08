"""
MCP File System Service

This module implements an MCP server exposing file system operations as tools
for use by the pipeline agents. Provides centralized, secure, and auditable
file operations with permission management and sandboxing.
"""

import os
import sys
import asyncio
import json
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import Tool, TextContent
import mcp.server.stdio
import logging

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.mcp_config import MCP_FILESYSTEM_CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FileSystemServer:
    """
    MCP server providing file system operations as tools.
    
    Features:
    - Secure file operations with sandboxing
    - Permission management
    - Audit logging
    - Error handling and validation
    """
    
    def __init__(self):
        """Initialize the file system server."""
        self.server = Server("filesystem-server")
        self.config = MCP_FILESYSTEM_CONFIG
        self.sandbox_root = Path(self.config.get("sandbox_root", "./generated"))
        self.audit_log_path = Path(self.config.get("audit_log_path", "./logs/mcp_filesystem_audit.log"))
        self.permissions = self.config.get("permissions", {})
        
        # Ensure directories exist
        self.sandbox_root.mkdir(parents=True, exist_ok=True)
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Register tools
        self._register_tools()
    
    def _register_tools(self):
        """Register all file system operations as MCP tools."""
        
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available file system tools."""
            return [
                Tool(
                    name="read_file",
                    description="Read contents of a file",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "File path relative to sandbox root"}
                        },
                        "required": ["path"]
                    }
                ),
                Tool(
                    name="write_file",
                    description="Write content to a file",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "File path relative to sandbox root"},
                            "content": {"type": "string", "description": "Content to write"},
                            "encoding": {"type": "string", "description": "File encoding", "default": "utf-8"}
                        },
                        "required": ["path", "content"]
                    }
                ),
                Tool(
                    name="delete_file",
                    description="Delete a file",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "File path relative to sandbox root"}
                        },
                        "required": ["path"]
                    }
                ),
                Tool(
                    name="list_directory",
                    description="List contents of a directory",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Directory path relative to sandbox root"},
                            "recursive": {"type": "boolean", "description": "List recursively", "default": False}
                        },
                        "required": ["path"]
                    }
                ),
                Tool(
                    name="create_directory",
                    description="Create a directory",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Directory path relative to sandbox root"},
                            "parents": {"type": "boolean", "description": "Create parent directories", "default": True}
                        },
                        "required": ["path"]
                    }
                ),
                Tool(
                    name="file_exists",
                    description="Check if a file or directory exists",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Path relative to sandbox root"}
                        },
                        "required": ["path"]
                    }
                ),
                Tool(
                    name="get_file_info",
                    description="Get information about a file",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "File path relative to sandbox root"}
                        },
                        "required": ["path"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> list[TextContent]:
            """Handle tool calls."""
            try:
                # Log the operation
                self._audit_log("tool_call", {
                    "tool": name,
                    "arguments": arguments,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Validate and sanitize the path
                if "path" in arguments:
                    sanitized_path = self._sanitize_path(arguments["path"])
                    arguments["path"] = sanitized_path
                
                # Route to appropriate handler
                handlers = {
                    "read_file": self._read_file,
                    "write_file": self._write_file,
                    "delete_file": self._delete_file,
                    "list_directory": self._list_directory,
                    "create_directory": self._create_directory,
                    "file_exists": self._file_exists,
                    "get_file_info": self._get_file_info
                }
                
                handler = handlers.get(name)
                if not handler:
                    raise ValueError(f"Unknown tool: {name}")
                
                result = await handler(**arguments)
                
                # Log successful operation
                self._audit_log("tool_success", {
                    "tool": name,
                    "result_summary": str(result)[:200]
                })
                
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
                
            except Exception as e:
                # Log error
                self._audit_log("tool_error", {
                    "tool": name,
                    "error": str(e)
                })
                
                error_result = {
                    "error": str(e),
                    "tool": name,
                    "timestamp": datetime.now().isoformat()
                }
                return [TextContent(type="text", text=json.dumps(error_result, indent=2))]
    
    def _sanitize_path(self, path_str: str) -> Path:
        """Sanitize and validate a path to ensure it's within the sandbox."""
        # Convert to Path object
        path = Path(path_str)
        
        # Resolve to absolute path within sandbox
        absolute_path = (self.sandbox_root / path).resolve()
        
        # Ensure the path is within the sandbox
        if not str(absolute_path).startswith(str(self.sandbox_root.resolve())):
            raise ValueError(f"Path '{path_str}' is outside the sandbox")
        
        return absolute_path
    
    def _audit_log(self, action: str, details: Dict[str, Any]):
        """Log an audit entry."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "details": details
        }
        
        # Write to audit log file
        with open(self.audit_log_path, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
        
        # Also log to standard logger
        logger.info(f"Audit: {action} - {details}")
    
    async def _read_file(self, path: Path, encoding: str = "utf-8") -> Dict[str, Any]:
        """Read contents of a file."""
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        if not path.is_file():
            raise ValueError(f"Path is not a file: {path}")
        
        content = path.read_text(encoding=encoding)
        
        return {
            "success": True,
            "path": str(path.relative_to(self.sandbox_root)),
            "content": content,
            "size": len(content),
            "encoding": encoding
        }
    
    async def _write_file(self, path: Path, content: str, encoding: str = "utf-8") -> Dict[str, Any]:
        """Write content to a file."""
        # Create parent directories if needed
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write the file
        path.write_text(content, encoding=encoding)
        
        return {
            "success": True,
            "path": str(path.relative_to(self.sandbox_root)),
            "size": len(content),
            "encoding": encoding
        }
    
    async def _delete_file(self, path: Path) -> Dict[str, Any]:
        """Delete a file."""
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        if path.is_file():
            path.unlink()
        else:
            shutil.rmtree(path)
        
        return {
            "success": True,
            "path": str(path.relative_to(self.sandbox_root)),
            "deleted": True
        }
    
    async def _list_directory(self, path: Path, recursive: bool = False) -> Dict[str, Any]:
        """List contents of a directory."""
        if not path.exists():
            raise FileNotFoundError(f"Directory not found: {path}")
        
        if not path.is_dir():
            raise ValueError(f"Path is not a directory: {path}")
        
        items = []
        
        if recursive:
            for item in path.rglob("*"):
                relative_path = item.relative_to(self.sandbox_root)
                items.append({
                    "path": str(relative_path),
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None
                })
        else:
            for item in path.iterdir():
                relative_path = item.relative_to(self.sandbox_root)
                items.append({
                    "path": str(relative_path),
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None
                })
        
        return {
            "success": True,
            "path": str(path.relative_to(self.sandbox_root)),
            "items": items,
            "count": len(items)
        }
    
    async def _create_directory(self, path: Path, parents: bool = True) -> Dict[str, Any]:
        """Create a directory."""
        path.mkdir(parents=parents, exist_ok=True)
        
        return {
            "success": True,
            "path": str(path.relative_to(self.sandbox_root)),
            "created": True
        }
    
    async def _file_exists(self, path: Path) -> Dict[str, Any]:
        """Check if a file or directory exists."""
        exists = path.exists()
        
        return {
            "success": True,
            "path": str(path.relative_to(self.sandbox_root)),
            "exists": exists,
            "type": "directory" if path.is_dir() else "file" if path.is_file() else None
        }
    
    async def _get_file_info(self, path: Path) -> Dict[str, Any]:
        """Get information about a file."""
        if not path.exists():
            raise FileNotFoundError(f"Path not found: {path}")
        
        stat = path.stat()
        
        return {
            "success": True,
            "path": str(path.relative_to(self.sandbox_root)),
            "type": "directory" if path.is_dir() else "file",
            "size": stat.st_size,
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "permissions": oct(stat.st_mode)[-3:]
        }
    
    async def run_server(self):
        """Run the MCP server."""
        # Load environment variables
        load_dotenv()
        
        # Log startup
        self._audit_log("server_start", {
            "sandbox_root": str(self.sandbox_root),
            "config": self.config
        })
        
        # Run the server using stdio transport
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="filesystem-server",
                    server_version="1.0.0"
                )
            )


# Server entry point
if __name__ == "__main__":
    server = FileSystemServer()
    asyncio.run(server.run_server())