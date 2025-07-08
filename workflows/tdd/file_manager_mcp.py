"""
TDD File Manager with MCP Integration - Unified file management for Test-Driven Development workflow
Handles coordination between coder agent file generation and test execution using MCP filesystem server
"""
import re
import os
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from workflows.logger import workflow_logger as logger
from shared.filesystem_client import MCPFileSystemClient, get_filesystem_client


@dataclass
class ProjectInfo:
    """Information about a generated project"""
    project_name: str
    project_path: Path
    files: Dict[str, str]  # filename -> content
    timestamp: str
    

class TDDFileManagerMCP:
    """Manages file operations for TDD workflow using MCP filesystem server"""
    
    def __init__(self, use_mcp: bool = True, agent_name: str = "tdd_workflow"):
        """
        Initialize the file manager with optional MCP support
        
        Args:
            use_mcp: Whether to use MCP filesystem server (True) or direct file I/O (False)
            agent_name: Name of the agent for MCP permissions
        """
        self.current_project: Optional[ProjectInfo] = None
        self.test_files: Dict[str, str] = {}
        self.implementation_files: Dict[str, str] = {}
        self.use_mcp = use_mcp
        self.agent_name = agent_name
        self.mcp_client: Optional[MCPFileSystemClient] = None
        
        if self.use_mcp:
            # Initialize MCP client
            self.mcp_client = MCPFileSystemClient(agent_name)
        
    async def __aenter__(self):
        """Async context manager entry"""
        if self.use_mcp and self.mcp_client:
            # Connect to MCP server
            self._mcp_context = self.mcp_client.connect()
            await self._mcp_context.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.use_mcp and hasattr(self, '_mcp_context'):
            await self._mcp_context.__aexit__(exc_type, exc_val, exc_tb)
    
    def extract_project_location(self, coder_output: str) -> Optional[str]:
        """
        Extract project location from coder agent output
        
        Looks for patterns like:
        - "Location: /path/to/project"
        - "PROJECT CREATED: app_generated_20250707_113423"
        - "Created project directory: /path/to/project"
        """
        # If we already have a project set, return its path to prevent new directories
        if self.current_project and self.current_project.project_path.exists():
            logger.info(f"Using existing project location: {self.current_project.project_path}")
            return str(self.current_project.project_path)
            
        # Pattern 1: Direct location line
        location_match = re.search(r'(?:Location|📁 Location):\s*(.+?)(?:\n|$)', coder_output)
        if location_match:
            location = location_match.group(1).strip()
            logger.info(f"Found project location: {location}")
            return location
            
        # Pattern 2: Project created with path
        created_match = re.search(r'Created project directory:\s*(.+?)(?:\n|$)', coder_output)
        if created_match:
            location = created_match.group(1).strip()
            logger.info(f"Found created directory: {location}")
            return location
            
        # Pattern 3: Extract from PROJECT CREATED and construct path
        project_match = re.search(r'PROJECT CREATED:\s*(\w+_generated_\d+_\d+)', coder_output)
        if project_match:
            project_name = project_match.group(1)
            # Try to find the base generated directory
            from workflows.workflow_config import GENERATED_CODE_PATH
            base_path = Path(GENERATED_CODE_PATH).resolve()
            project_path = base_path / project_name
            if project_path.exists():
                logger.info(f"Found project via name: {project_path}")
                return str(project_path)
                
        logger.warning("Could not extract project location from coder output")
        return None
        
    def parse_files(self, output: str, extract_location: bool = True) -> Dict[str, str]:
        """
        Parse files from coder or test writer output
        Handles multiple format patterns
        
        Args:
            output: The agent output containing file definitions
            extract_location: Whether to also extract project location
            
        Returns:
            Dictionary of filename -> content
        """
        files = {}
        
        # If extracting location, try to get project info
        if extract_location:
            location = self.extract_project_location(output)
            if location:
                self.current_project = ProjectInfo(
                    project_name=Path(location).name,
                    project_path=Path(location),
                    files={},
                    timestamp=""
                )
        
        # Multiple patterns to catch different formats
        patterns = [
            # Pattern 1: FILENAME: format (coder agent)
            (r'FILENAME:\s*(.+?)\n```(?:\w*)\n([\s\S]+?)\n```', 'FILENAME'),
            # Pattern 2: # filename: format (TDD cycle)
            (r'#\s*filename:\s*(\S+)\n(.*?)(?=#\s*filename:|$)', 'hash_filename'),
            # Pattern 3: File: format
            (r'File:\s*(.+?)\n```(?:\w*)\n([\s\S]+?)\n```', 'File'),
            # Pattern 4: Markdown header format
            (r'###\s*(.+?)\n```(?:\w*)\n([\s\S]+?)\n```', 'markdown'),
        ]
        
        for pattern, pattern_name in patterns:
            matches = re.findall(pattern, output, re.MULTILINE | re.DOTALL)
            if matches:
                logger.info(f"Found {len(matches)} files using {pattern_name} pattern")
                for filename, content in matches:
                    filename = filename.strip()
                    content = content.strip()
                    files[filename] = content
                    
                    # Categorize files
                    if 'test' in filename.lower():
                        self.test_files[filename] = content
                    else:
                        self.implementation_files[filename] = content
                        
        # Update current project files if we have a project
        if self.current_project:
            self.current_project.files.update(files)
            
        return files
        
    def get_test_directory(self, use_project_dir: bool = True) -> Optional[Path]:
        """
        Get directory for test execution
        
        Args:
            use_project_dir: If True, use actual project directory; 
                           if False, return None to use temp directory
                           
        Returns:
            Path to test directory or None
        """
        if use_project_dir and self.current_project:
            return self.current_project.project_path
        return None
    
    async def _read_file_mcp(self, file_path: Path) -> Optional[str]:
        """Read file using MCP client"""
        if not self.mcp_client:
            return None
            
        try:
            # Convert to relative path from sandbox root
            from config.mcp_config import MCP_FILESYSTEM_CONFIG
            sandbox_root = Path(MCP_FILESYSTEM_CONFIG["sandbox_root"])
            relative_path = file_path.relative_to(sandbox_root)
            
            content = await self.mcp_client.read_file(str(relative_path))
            return content
        except Exception as e:
            logger.error(f"MCP read error for {file_path}: {str(e)}")
            return None
    
    async def _write_file_mcp(self, file_path: Path, content: str) -> bool:
        """Write file using MCP client"""
        if not self.mcp_client:
            return False
            
        try:
            # Convert to relative path from sandbox root
            from config.mcp_config import MCP_FILESYSTEM_CONFIG
            sandbox_root = Path(MCP_FILESYSTEM_CONFIG["sandbox_root"])
            relative_path = file_path.relative_to(sandbox_root)
            
            # Create parent directories if needed
            parent_dir = str(relative_path.parent)
            if parent_dir and parent_dir != ".":
                await self.mcp_client.create_directory(parent_dir)
            
            # Write file
            success = await self.mcp_client.write_file(str(relative_path), content)
            return success
        except Exception as e:
            logger.error(f"MCP write error for {file_path}: {str(e)}")
            return False
    
    def _read_file_direct(self, file_path: Path) -> Optional[str]:
        """Read file using direct I/O"""
        try:
            return file_path.read_text(encoding='utf-8')
        except Exception as e:
            logger.error(f"Direct read error for {file_path}: {str(e)}")
            return None
    
    def _write_file_direct(self, file_path: Path, content: str) -> bool:
        """Write file using direct I/O"""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding='utf-8')
            return True
        except Exception as e:
            logger.error(f"Direct write error for {file_path}: {str(e)}")
            return False
    
    def update_files_in_project(self, files: Dict[str, str]) -> bool:
        """
        Update files in the current project directory
        
        Args:
            files: Dictionary of filename -> content to update
            
        Returns:
            True if successful, False otherwise
        """
        if not self.current_project:
            logger.error("No current project set")
            return False
        
        # If using MCP, we need to run this asynchronously
        if self.use_mcp:
            # Create async task and run it
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self._update_files_async(files))
            finally:
                loop.close()
        else:
            # Use direct file I/O
            return self._update_files_direct(files)
    
    async def _update_files_async(self, files: Dict[str, str]) -> bool:
        """Async version of update_files_in_project for MCP"""
        try:
            for filename, content in files.items():
                file_path = self.current_project.project_path / filename
                
                success = await self._write_file_mcp(file_path, content)
                if success:
                    logger.info(f"Updated {filename} in project via MCP")
                else:
                    logger.error(f"Failed to update {filename} via MCP")
                    return False
                    
            return True
            
        except Exception as e:
            logger.error(f"Error updating files via MCP: {str(e)}")
            return False
    
    def _update_files_direct(self, files: Dict[str, str]) -> bool:
        """Direct I/O version of update_files_in_project"""
        try:
            for filename, content in files.items():
                file_path = self.current_project.project_path / filename
                
                success = self._write_file_direct(file_path, content)
                if success:
                    logger.info(f"Updated {filename} in project")
                else:
                    return False
                    
            return True
            
        except Exception as e:
            logger.error(f"Error updating files: {str(e)}")
            return False
    
    def get_file_content(self, filename: str) -> Optional[str]:
        """Get content of a specific file from current project"""
        if self.current_project and filename in self.current_project.files:
            return self.current_project.files[filename]
            
        # Try to read from disk if we have a project path
        if self.current_project:
            file_path = self.current_project.project_path / filename
            if file_path.exists():
                if self.use_mcp:
                    # Run async operation synchronously
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        return loop.run_until_complete(self._read_file_mcp(file_path))
                    finally:
                        loop.close()
                else:
                    return self._read_file_direct(file_path)
                    
        return None
        
    def list_project_files(self) -> List[str]:
        """List all files in current project"""
        if not self.current_project:
            return []
            
        # Get files from memory
        files = list(self.current_project.files.keys())
        
        # Also check disk for any additional files
        if self.current_project.project_path.exists():
            if self.use_mcp:
                # Use MCP to list files
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    additional_files = loop.run_until_complete(self._list_files_mcp())
                    files.extend(additional_files)
                finally:
                    loop.close()
            else:
                # Direct file listing
                for file_path in self.current_project.project_path.rglob('*'):
                    if file_path.is_file() and not file_path.name.startswith('.'):
                        relative_path = file_path.relative_to(self.current_project.project_path)
                        if str(relative_path) not in files:
                            files.append(str(relative_path))
                        
        return sorted(files)
    
    async def _list_files_mcp(self) -> List[str]:
        """List files using MCP client"""
        if not self.mcp_client or not self.current_project:
            return []
            
        try:
            from config.mcp_config import MCP_FILESYSTEM_CONFIG
            sandbox_root = Path(MCP_FILESYSTEM_CONFIG["sandbox_root"])
            relative_path = self.current_project.project_path.relative_to(sandbox_root)
            
            items = await self.mcp_client.list_directory(str(relative_path), recursive=True)
            
            additional_files = []
            for item in items:
                if item["type"] == "file":
                    # Convert back to project-relative path
                    file_path = Path(item["path"]).relative_to(relative_path)
                    if str(file_path) not in self.current_project.files:
                        additional_files.append(str(file_path))
                        
            return additional_files
            
        except Exception as e:
            logger.error(f"Error listing files via MCP: {str(e)}")
            return []
        
    def prepare_test_context(self) -> Dict[str, str]:
        """
        Prepare file context for test execution
        
        Returns:
            Dictionary of all files (tests and implementation)
        """
        context = {}
        context.update(self.test_files)
        context.update(self.implementation_files)
        
        # Add any files from current project
        if self.current_project:
            context.update(self.current_project.files)
            
        return context
        
    def reset(self):
        """Reset file manager state"""
        self.current_project = None
        self.test_files.clear()
        self.implementation_files.clear()
        logger.info("File manager reset")


# Factory function to create file manager with appropriate settings
def create_tdd_file_manager(use_mcp: bool = False, agent_name: str = "tdd_workflow") -> TDDFileManagerMCP:
    """
    Create a TDD file manager instance
    
    Args:
        use_mcp: Whether to use MCP filesystem server
        agent_name: Name of the agent for MCP permissions
        
    Returns:
        TDDFileManagerMCP instance
    """
    # Check environment variable to enable MCP by default
    if os.getenv("USE_MCP_FILESYSTEM", "false").lower() == "true":
        use_mcp = True
        
    return TDDFileManagerMCP(use_mcp=use_mcp, agent_name=agent_name)