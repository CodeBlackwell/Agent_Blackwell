"""
Code Saver Module with MCP Integration for MVP Incremental Workflow

This module handles saving generated code using the MCP filesystem server,
ensuring secure and auditable file operations with proper sandboxing.
"""

import os
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from workflows.logger import workflow_logger as logger
from shared.filesystem_client import MCPFileSystemClient, get_filesystem_client


class CodeSaverMCP:
    """Handles saving generated code to disk using MCP filesystem server."""
    
    def __init__(self, base_path: Optional[Path] = None, use_mcp: bool = True, agent_name: str = "mvp_incremental"):
        """
        Initialize the CodeSaver with optional MCP support.
        
        Args:
            base_path: Base directory for saving code. Defaults to orchestrator/generated/
            use_mcp: Whether to use MCP filesystem server (True) or direct file I/O (False)
            agent_name: Name of the agent for MCP permissions
        """
        if base_path is None:
            # Use the standard path from workflow_config
            from workflows.workflow_config import GENERATED_CODE_PATH
            self.base_path = Path(GENERATED_CODE_PATH)
        else:
            self.base_path = Path(base_path)
            
        self.current_session_path = None
        self.files_saved = []
        self.use_mcp = use_mcp
        self.agent_name = agent_name
        self.mcp_client: Optional[MCPFileSystemClient] = None
        
        if self.use_mcp:
            # Initialize MCP client
            self.mcp_client = MCPFileSystemClient(agent_name)
    
    async def __aenter__(self):
        """Async context manager entry"""
        if self.use_mcp and self.mcp_client:
            self._mcp_context = self.mcp_client.connect()
            await self._mcp_context.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.use_mcp and hasattr(self, '_mcp_context'):
            await self._mcp_context.__aexit__(exc_type, exc_val, exc_tb)
    
    def _get_relative_path(self, full_path: Path) -> str:
        """Get path relative to MCP sandbox root"""
        if self.use_mcp:
            from config.mcp_config import MCP_FILESYSTEM_CONFIG
            sandbox_root = Path(MCP_FILESYSTEM_CONFIG["sandbox_root"])
            try:
                return str(full_path.relative_to(sandbox_root))
            except ValueError:
                # If path is not relative to sandbox, use it as is
                return str(full_path)
        return str(full_path)
    
    def create_session_directory(self, session_name: Optional[str] = None) -> Path:
        """
        Create a timestamped directory for this session's code.
        
        Args:
            session_name: Optional name to include in directory name
            
        Returns:
            Path to the created directory
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if session_name:
            # Sanitize session name for filesystem
            safe_name = "".join(c for c in session_name if c.isalnum() or c in "-_")[:30]
            dir_name = f"{timestamp}_{safe_name}"
        else:
            dir_name = f"{timestamp}_generated"
            
        self.current_session_path = self.base_path / dir_name
        
        # Create directory using appropriate method
        if self.use_mcp:
            # Run async operation synchronously
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self._create_directory_mcp(self.current_session_path))
            finally:
                loop.close()
        else:
            self.current_session_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Created session directory: {self.current_session_path}")
        return self.current_session_path
    
    async def _create_directory_mcp(self, path: Path) -> bool:
        """Create directory using MCP client"""
        if not self.mcp_client:
            return False
            
        try:
            relative_path = self._get_relative_path(path)
            return await self.mcp_client.create_directory(relative_path, parents=True)
        except Exception as e:
            logger.error(f"MCP directory creation error: {str(e)}")
            return False
    
    def save_code_files(self, 
                       code_dict: Dict[str, str], 
                       feature_name: Optional[str] = None,
                       overwrite: bool = True) -> List[Path]:
        """
        Save multiple code files to disk.
        
        Args:
            code_dict: Dictionary mapping filenames to code content
            feature_name: Optional feature name for logging
            overwrite: Whether to overwrite existing files
            
        Returns:
            List of paths to saved files
        """
        if not self.current_session_path:
            raise ValueError("No session directory created. Call create_session_directory() first.")
            
        saved_paths = []
        
        # Run async operations if using MCP
        if self.use_mcp:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                saved_paths = loop.run_until_complete(
                    self._save_code_files_async(code_dict, feature_name, overwrite)
                )
            finally:
                loop.close()
        else:
            # Use direct file I/O
            for filename, content in code_dict.items():
                try:
                    file_path = self._save_single_file_direct(filename, content, overwrite)
                    saved_paths.append(file_path)
                    self.files_saved.append(file_path)
                    
                    logger.info(f"Saved {filename} ({len(content)} chars)" + 
                              (f" for feature: {feature_name}" if feature_name else ""))
                              
                except Exception as e:
                    logger.error(f"Failed to save {filename}: {str(e)}")
                    raise
                    
        return saved_paths
    
    async def _save_code_files_async(self, 
                                   code_dict: Dict[str, str], 
                                   feature_name: Optional[str],
                                   overwrite: bool) -> List[Path]:
        """Async version of save_code_files for MCP"""
        saved_paths = []
        
        for filename, content in code_dict.items():
            try:
                file_path = await self._save_single_file_mcp(filename, content, overwrite)
                saved_paths.append(file_path)
                self.files_saved.append(file_path)
                
                logger.info(f"Saved {filename} ({len(content)} chars) via MCP" + 
                          (f" for feature: {feature_name}" if feature_name else ""))
                          
            except Exception as e:
                logger.error(f"Failed to save {filename} via MCP: {str(e)}")
                raise
                
        return saved_paths
    
    async def _save_single_file_mcp(self, filename: str, content: str, overwrite: bool) -> Path:
        """Save a single file using MCP client"""
        if not self.mcp_client:
            raise RuntimeError("MCP client not initialized")
            
        file_path = self.current_session_path / filename
        relative_path = self._get_relative_path(file_path)
        
        # Check if file exists and handle overwrite
        if not overwrite:
            exists = await self.mcp_client.exists(relative_path)
            if exists:
                # Find unique filename
                base = Path(filename).stem
                ext = Path(filename).suffix
                counter = 1
                while exists:
                    new_filename = f"{base}_{counter}{ext}"
                    file_path = self.current_session_path / new_filename
                    relative_path = self._get_relative_path(file_path)
                    exists = await self.mcp_client.exists(relative_path)
                    counter += 1
        
        # Create parent directories if needed
        parent_dir = str(Path(relative_path).parent)
        if parent_dir and parent_dir != ".":
            await self.mcp_client.create_directory(parent_dir, parents=True)
        
        # Write the file
        success = await self.mcp_client.write_file(relative_path, content)
        if not success:
            raise RuntimeError(f"Failed to write file via MCP: {filename}")
            
        return file_path
    
    def _save_single_file_direct(self, filename: str, content: str, overwrite: bool) -> Path:
        """Save a single file using direct I/O"""
        file_path = self.current_session_path / filename
        
        # Create parent directories if needed
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if file exists and overwrite is False
        if file_path.exists() and not overwrite:
            base = file_path.stem
            ext = file_path.suffix
            counter = 1
            while file_path.exists():
                file_path = file_path.parent / f"{base}_{counter}{ext}"
                counter += 1
                
        # Write the file
        file_path.write_text(content, encoding='utf-8')
        
        return file_path
    
    def save_metadata(self, metadata: Dict) -> Path:
        """
        Save session metadata as JSON.
        
        Args:
            metadata: Dictionary of metadata to save
            
        Returns:
            Path to metadata file
        """
        if not self.current_session_path:
            raise ValueError("No session directory created.")
            
        metadata_path = self.current_session_path / "session_metadata.json"
        
        # Add standard metadata
        metadata.update({
            "timestamp": datetime.now().isoformat(),
            "files_count": len(self.files_saved),
            "files": [str(p.relative_to(self.current_session_path)) for p in self.files_saved],
            "session_path": str(self.current_session_path),
            "used_mcp": self.use_mcp
        })
        
        content = json.dumps(metadata, indent=2)
        
        # Save using appropriate method
        if self.use_mcp:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self._save_file_mcp(metadata_path, content))
            finally:
                loop.close()
        else:
            metadata_path.write_text(content)
            
        logger.info(f"Saved session metadata to {metadata_path}")
        return metadata_path
    
    async def _save_file_mcp(self, path: Path, content: str) -> bool:
        """Helper to save a file using MCP"""
        if not self.mcp_client:
            return False
            
        relative_path = self._get_relative_path(path)
        return await self.mcp_client.write_file(relative_path, content)
    
    def create_requirements_file(self, dependencies: List[str]) -> Optional[Path]:
        """
        Create a requirements.txt file from detected dependencies.
        
        Args:
            dependencies: List of Python packages
            
        Returns:
            Path to requirements file if created
        """
        if not dependencies:
            return None
            
        if not self.current_session_path:
            raise ValueError("No session directory created.")
            
        req_path = self.current_session_path / "requirements.txt"
        content = "\n".join(dependencies) + "\n"
        
        # Save using appropriate method
        if self.use_mcp:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self._save_file_mcp(req_path, content))
            finally:
                loop.close()
        else:
            req_path.write_text(content)
        
        logger.info(f"Created requirements.txt with {len(dependencies)} dependencies")
        return req_path
    
    def create_readme(self, 
                     project_name: str,
                     description: str,
                     features: List[str],
                     setup_instructions: Optional[List[str]] = None) -> Path:
        """
        Create a README.md file for the generated project.
        
        Args:
            project_name: Name of the project
            description: Project description
            features: List of implemented features
            setup_instructions: Optional setup instructions
            
        Returns:
            Path to README file
        """
        if not self.current_session_path:
            raise ValueError("No session directory created.")
            
        readme_content = [
            f"# {project_name}",
            "",
            f"{description}",
            "",
            "## Features",
            ""
        ]
        
        for feature in features:
            readme_content.append(f"- {feature}")
            
        if setup_instructions:
            readme_content.extend([
                "",
                "## Setup",
                ""
            ])
            for instruction in setup_instructions:
                readme_content.append(f"{instruction}")
                
        readme_content.extend([
            "",
            "## Generated Information",
            "",
            f"- Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"- Total files: {len(self.files_saved)}",
            f"- Location: `{self.current_session_path}`",
            f"- File operations: {'MCP Server' if self.use_mcp else 'Direct I/O'}",
            "",
            "---",
            "_Generated by MVP Incremental Workflow with MCP Integration_"
        ])
        
        readme_path = self.current_session_path / "README.md"
        content = "\n".join(readme_content)
        
        # Save using appropriate method
        if self.use_mcp:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self._save_file_mcp(readme_path, content))
            finally:
                loop.close()
        else:
            readme_path.write_text(content)
        
        logger.info(f"Created README.md at {readme_path}")
        return readme_path
    
    def get_summary(self) -> Dict:
        """
        Get a summary of saved files.
        
        Returns:
            Dictionary with summary information
        """
        if not self.current_session_path:
            return {
                "session_path": None,
                "files_saved": 0,
                "total_size": 0,
                "file_list": [],
                "used_mcp": self.use_mcp
            }
            
        # Calculate total size
        if self.use_mcp:
            # For MCP, we would need to query file sizes
            # For now, estimate based on content length saved
            total_size = 0  # Would need async operation to get actual sizes
        else:
            total_size = sum(f.stat().st_size for f in self.files_saved if f.exists())
        
        return {
            "session_path": str(self.current_session_path),
            "files_saved": len(self.files_saved),
            "total_size": total_size,
            "total_size_kb": round(total_size / 1024, 2) if total_size > 0 else 0,
            "file_list": [str(f.relative_to(self.current_session_path)) for f in self.files_saved],
            "used_mcp": self.use_mcp
        }
    
    async def get_metrics(self) -> Dict:
        """
        Get MCP performance metrics if available.
        
        Returns:
            Dictionary with metrics or empty dict
        """
        if self.use_mcp and self.mcp_client:
            return self.mcp_client.get_metrics()
        return {}


def extract_dependencies_from_code(code_dict: Dict[str, str]) -> List[str]:
    """
    Extract Python package dependencies from code.
    
    Args:
        code_dict: Dictionary of filename to code content
        
    Returns:
        List of unique dependencies
    """
    dependencies = set()
    
    for filename, content in code_dict.items():
        if filename.endswith('.py'):
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('import ') or line.startswith('from '):
                    # Extract package name
                    if line.startswith('import '):
                        pkg = line.split()[1].split('.')[0]
                    else:  # from X import Y
                        pkg = line.split()[1].split('.')[0]
                        
                    # Filter out standard library modules (basic heuristic)
                    if pkg not in ['os', 'sys', 'json', 'datetime', 'pathlib', 'typing',
                                  're', 'collections', 'itertools', 'functools', 'math',
                                  'random', 'string', 'time', 'unittest', 'asyncio']:
                        dependencies.add(pkg)
                        
    return sorted(list(dependencies))


# Factory function to create code saver with appropriate settings
def create_code_saver(base_path: Optional[Path] = None, 
                     use_mcp: bool = False, 
                     agent_name: str = "mvp_incremental") -> CodeSaverMCP:
    """
    Create a code saver instance
    
    Args:
        base_path: Base directory for saving code
        use_mcp: Whether to use MCP filesystem server
        agent_name: Name of the agent for MCP permissions
        
    Returns:
        CodeSaverMCP instance
    """
    # Check environment variable to enable MCP by default
    if os.getenv("USE_MCP_FILESYSTEM", "false").lower() == "true":
        use_mcp = True
        
    return CodeSaverMCP(base_path=base_path, use_mcp=use_mcp, agent_name=agent_name)