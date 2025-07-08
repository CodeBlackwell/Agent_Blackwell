# MCP File System Integration Guide

## Overview

The Multi-Agent System now includes integration with MCP (Model Context Protocol) for secure, auditable file system operations. This integration provides centralized file management with sandboxing, permission control, and comprehensive audit logging.

## Architecture

### Components

1. **MCP File System Server** (`mcp/filesystem_server.py`)
   - Provides file operations as MCP tools
   - Enforces sandboxing and permissions
   - Logs all operations for audit trail
   - Supports async operations

2. **MCP File System Client** (`shared/filesystem_client.py`)
   - High-level async interface for agents
   - Automatic retry with exponential backoff
   - Connection pooling
   - Performance metrics collection

3. **Configuration** (`config/mcp_config.py`)
   - Centralized configuration for all MCP services
   - Agent-specific permissions
   - Sandbox paths and limits
   - Performance settings

4. **Updated Components**
   - `workflows/tdd/file_manager_mcp.py` - TDD File Manager with MCP support
   - `workflows/mvp_incremental/code_saver_mcp.py` - Code Saver with MCP support

## Key Features

### 1. Sandboxing
All file operations are restricted to a configured sandbox directory (default: `./generated`). Attempts to access files outside the sandbox are blocked.

### 2. Permission Management
Each agent has specific permissions:
- **Coder agents**: read, write, create, delete
- **Executor agents**: read, write, create
- **Reviewer agents**: read only
- **Validator agents**: read only

### 3. Audit Logging
Every file operation is logged with:
- Timestamp
- Operation type
- Agent performing the operation
- Success/failure status
- Error details (if any)

### 4. Retry Logic
The client automatically retries failed operations with exponential backoff:
- Default: 3 retries
- Initial delay: 1 second
- Backoff multiplier: 2.0

### 5. Performance Monitoring
- Operation duration tracking
- Slow operation warnings (default threshold: 5 seconds)
- Metrics export for analysis

## Usage

### Basic Usage

```python
from shared.filesystem_client import MCPFileSystemClient

# Create client
client = MCPFileSystemClient("my_agent")

# Use as async context manager
async with client.connect() as fs:
    # Read file
    content = await fs.read_file("path/to/file.txt")
    
    # Write file
    success = await fs.write_file("path/to/new.txt", "content")
    
    # Create directory
    await fs.create_directory("path/to/dir", parents=True)
    
    # List directory
    items = await fs.list_directory("path", recursive=True)
    
    # Check existence
    exists = await fs.exists("path/to/check")
    
    # Get file info
    info = await fs.get_file_info("path/to/file.txt")
```

### Using Updated Components

#### TDD File Manager
```python
from workflows.tdd.file_manager_mcp import create_tdd_file_manager

# Create with MCP enabled
file_manager = create_tdd_file_manager(use_mcp=True, agent_name="tdd_workflow")

# Use as before - MCP is transparent
files = file_manager.parse_files(coder_output)
success = file_manager.update_files_in_project(files)
```

#### Code Saver
```python
from workflows.mvp_incremental.code_saver_mcp import create_code_saver

# Create with MCP enabled
async with create_code_saver(use_mcp=True) as saver:
    # Create session directory
    session_path = saver.create_session_directory("my_project")
    
    # Save files
    code_dict = {"app.py": "print('hello')"}
    paths = saver.save_code_files(code_dict)
```

### Environment Configuration

Enable MCP globally via environment variable:
```bash
export USE_MCP_FILESYSTEM=true
```

Configure sandbox and permissions in `.env`:
```bash
MCP_FILESYSTEM_SANDBOX=/path/to/sandbox
MCP_FILESYSTEM_AUDIT_LOG=/path/to/audit.log
MCP_FILESYSTEM_HOST=localhost
MCP_FILESYSTEM_PORT=8090
```

## Migration Guide

### Updating Existing Agents

1. **Replace Direct File I/O**
   ```python
   # Before
   Path(file_path).write_text(content)
   
   # After
   await fs_client.write_file(file_path, content)
   ```

2. **Use Factory Functions**
   ```python
   # For TDD workflows
   file_manager = create_tdd_file_manager(use_mcp=True)
   
   # For code saving
   code_saver = create_code_saver(use_mcp=True)
   ```

3. **Handle Async Operations**
   ```python
   # Wrap in async context
   async def my_workflow():
       async with MCPFileSystemClient("my_agent").connect() as fs:
           # Perform file operations
           pass
   ```

### Backward Compatibility

Both updated components support a `use_mcp` parameter:
- `use_mcp=True`: Use MCP filesystem server
- `use_mcp=False`: Use direct file I/O (legacy behavior)

This allows gradual migration without breaking existing workflows.

## Security Considerations

1. **Sandbox Enforcement**: All paths are validated against the sandbox root
2. **Path Traversal Protection**: Attempts to use `../` are blocked
3. **Permission Checks**: Operations are validated against agent permissions
4. **Audit Trail**: All operations are logged for security review

## Performance Considerations

1. **Connection Pooling**: Reuse connections for better performance
2. **Async Operations**: Use async/await for non-blocking I/O
3. **Batch Operations**: Group multiple operations when possible
4. **Caching**: Read operations can be cached (configurable TTL)

## Monitoring and Debugging

### Viewing Audit Logs
```bash
tail -f logs/mcp_filesystem_audit.log | jq .
```

### Performance Metrics
```python
# Get metrics from client
metrics = client.get_metrics()
print(f"Average read time: {metrics['read_file']['avg']}s")
```

### Debug Mode
Enable debug logging:
```python
import logging
logging.getLogger('shared.filesystem_client').setLevel(logging.DEBUG)
```

## Troubleshooting

### Common Issues

1. **"Not connected to MCP server"**
   - Ensure you're using the client within an async context manager
   - Check that the MCP server is running

2. **"Path is outside the sandbox"**
   - Verify your paths are relative to the sandbox root
   - Check `MCP_FILESYSTEM_SANDBOX` configuration

3. **"Permission denied"**
   - Check agent permissions in `mcp_config.py`
   - Verify the agent name is correct

4. **Slow Operations**
   - Check network connectivity if using remote MCP server
   - Review metrics for performance bottlenecks
   - Consider enabling caching for read operations

## Testing

Run the integration tests:
```bash
pytest tests/integration/test_mcp_filesystem_integration.py -v
```

Run unit tests:
```bash
pytest tests/unit/mcp/test_filesystem_server.py -v
pytest tests/unit/mcp/test_filesystem_client.py -v
```

## Future Enhancements

1. **Cloud Storage Support**: S3, Azure Blob, GCS backends
2. **Encryption**: At-rest encryption for sensitive files
3. **Versioning**: File version tracking and rollback
4. **Quota Management**: Per-agent storage quotas
5. **Real-time Sync**: Multi-node file synchronization
6. **WebDAV Support**: Standard protocol for file access

## Summary

The MCP filesystem integration provides a secure, auditable, and performant foundation for all file operations in the multi-agent system. By centralizing file access through MCP, we gain better control, monitoring, and flexibility for future enhancements.