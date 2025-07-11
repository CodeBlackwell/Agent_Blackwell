"""Enhanced File Manager for Flagship TDD Workflow

Provides file reading, writing, and caching capabilities for agents
to enable iterative development and code review.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
import json


class EnhancedFileManager:
    """Manages file operations with caching and session/project scoping"""
    
    def __init__(self, session_id: str = None, project_root: Path = None):
        """
        Initialize the file manager
        
        Args:
            session_id: Unique session identifier
            project_root: Root directory for project files
        """
        self.session_id = session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.project_root = project_root or Path.cwd()
        
        # File caches
        self._file_cache: Dict[str, str] = {}  # path -> content
        self._session_files: Dict[str, str] = {}  # files created in this session
        self._file_metadata: Dict[str, Dict] = {}  # path -> metadata
        
        # Initialize session directory
        self.session_dir = self.project_root / "generated" / self.session_id
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
    def read_file(self, file_path: Union[str, Path], use_cache: bool = True) -> Optional[str]:
        """
        Read a file from disk or cache
        
        Args:
            file_path: Path to the file (relative or absolute)
            use_cache: Whether to use cached content if available
            
        Returns:
            File content or None if file doesn't exist
        """
        # First check if it's just a filename and exists in session dir
        if isinstance(file_path, str) and '/' not in file_path and '\\' not in file_path:
            session_path = self.session_dir / file_path
            if session_path.exists():
                path = session_path
            else:
                path = self._normalize_path(file_path)
        else:
            # Normalize path
            path = self._normalize_path(file_path)
        
        # Check cache first
        if use_cache and str(path) in self._file_cache:
            self._update_metadata(path, 'read')
            return self._file_cache[str(path)]
        
        # Try to read from disk
        try:
            if path.exists():
                content = path.read_text(encoding='utf-8')
                self._file_cache[str(path)] = content
                self._update_metadata(path, 'read')
                return content
        except Exception as e:
            print(f"Error reading file {path}: {e}")
            
        return None
    
    def write_file(self, file_path: Union[str, Path], content: str, 
                   session_scope: bool = True) -> bool:
        """
        Write content to a file
        
        Args:
            file_path: Path to the file (relative or absolute)
            content: Content to write
            session_scope: If True, write to session directory; else use project root
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Determine target path
            if session_scope:
                # Write to session directory
                relative_path = Path(file_path).name if Path(file_path).is_absolute() else file_path
                path = self.session_dir / relative_path
            else:
                path = self._normalize_path(file_path)
            
            # Create parent directories
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            path.write_text(content, encoding='utf-8')
            
            # Update caches
            self._file_cache[str(path)] = content
            self._session_files[str(path)] = content
            self._update_metadata(path, 'write')
            
            return True
            
        except Exception as e:
            print(f"Error writing file {file_path}: {e}")
            return False
    
    def update_file(self, file_path: Union[str, Path], content: str) -> bool:
        """
        Update an existing file (preserves location)
        
        Args:
            file_path: Path to the file
            content: New content
            
        Returns:
            True if successful, False otherwise
        """
        path = self._normalize_path(file_path)
        
        # Check if file exists
        if not path.exists():
            print(f"File {path} does not exist. Use write_file to create new files.")
            return False
        
        return self.write_file(path, content, session_scope=False)
    
    def list_files(self, pattern: str = "*", include_session: bool = True, 
                   include_project: bool = True) -> List[Path]:
        """
        List files matching a pattern
        
        Args:
            pattern: Glob pattern for file matching
            include_session: Include files from current session
            include_project: Include files from project root
            
        Returns:
            List of file paths
        """
        files = []
        
        # Session files
        if include_session and self.session_dir.exists():
            files.extend(self.session_dir.glob(pattern))
        
        # Project files
        if include_project:
            # Avoid duplicating session files
            project_files = self.project_root.glob(pattern)
            for f in project_files:
                if not str(f).startswith(str(self.session_dir)):
                    files.append(f)
        
        return sorted(files)
    
    def get_file_context(self, agent_type: str = None) -> Dict[str, Any]:
        """
        Get file context for an agent
        
        Args:
            agent_type: Type of agent requesting context
            
        Returns:
            Dictionary with file information
        """
        context = {
            "session_id": self.session_id,
            "session_files": list(self._session_files.keys()),
            "cached_files": list(self._file_cache.keys()),
            "project_root": str(self.project_root),
            "session_dir": str(self.session_dir)
        }
        
        # Add agent-specific context
        if agent_type == "test_writer":
            # Test writer might want to see existing test files
            test_files = self.list_files("*test*.py")
            context["existing_tests"] = [str(f) for f in test_files]
            
        elif agent_type == "coder":
            # Coder needs to see tests and existing implementations
            test_files = self.list_files("*test*.py")
            impl_files = [f for f in self.list_files("*.py") 
                         if "test" not in f.name.lower()]
            context["test_files"] = [str(f) for f in test_files]
            context["implementation_files"] = [str(f) for f in impl_files]
            
        elif agent_type == "test_runner":
            # Test runner needs all Python files
            context["all_python_files"] = [str(f) for f in self.list_files("*.py")]
        
        return context
    
    def clear_cache(self):
        """Clear the file cache"""
        self._file_cache.clear()
    
    def save_session_metadata(self):
        """Save session metadata to disk"""
        metadata = {
            "session_id": self.session_id,
            "created_at": datetime.now().isoformat(),
            "session_files": list(self._session_files.keys()),
            "file_metadata": self._file_metadata
        }
        
        metadata_path = self.session_dir / "session_metadata.json"
        try:
            metadata_path.write_text(json.dumps(metadata, indent=2))
        except Exception as e:
            print(f"Error saving session metadata: {e}")
    
    def _normalize_path(self, file_path: Union[str, Path]) -> Path:
        """Normalize a file path relative to project root"""
        path = Path(file_path)
        
        # If absolute path, return as is
        if path.is_absolute():
            return path
        
        # Otherwise, make relative to project root
        return self.project_root / path
    
    def _update_metadata(self, path: Path, operation: str):
        """Update file metadata"""
        key = str(path)
        if key not in self._file_metadata:
            self._file_metadata[key] = {
                "first_accessed": datetime.now().isoformat(),
                "operations": []
            }
        
        self._file_metadata[key]["last_accessed"] = datetime.now().isoformat()
        self._file_metadata[key]["operations"].append({
            "type": operation,
            "timestamp": datetime.now().isoformat()
        })