"""
Code Saver Module for MVP Incremental Workflow

This module handles saving generated code to disk, ensuring that all code
created during the workflow is properly persisted to the filesystem.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from workflows.logger import workflow_logger as logger


class CodeSaver:
    """Handles saving generated code to disk with proper organization."""
    
    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize the CodeSaver.
        
        Args:
            base_path: Base directory for saving code. Defaults to orchestrator/generated/
        """
        if base_path is None:
            # Use the standard path from workflow_config
            from workflows.workflow_config import GENERATED_CODE_PATH
            # Use the path directly without orchestrator prefix
            self.base_path = Path(GENERATED_CODE_PATH)
        else:
            self.base_path = Path(base_path)
            
        self.current_session_path = None
        self.files_saved = []
        
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
            # Sanitize session name for filesystem - keep hyphens and underscores
            safe_name = "".join(c for c in session_name if c.isalnum() or c in "-_")[:30]
            dir_name = f"{timestamp}_{safe_name}"
        else:
            dir_name = f"{timestamp}_generated"
            
        self.current_session_path = self.base_path / dir_name
        self.current_session_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Created session directory: {self.current_session_path}")
        return self.current_session_path
        
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
        
        for filename, content in code_dict.items():
            try:
                file_path = self._save_single_file(filename, content, overwrite)
                saved_paths.append(file_path)
                self.files_saved.append(file_path)
                
                logger.info(f"Saved {filename} ({len(content)} chars)" + 
                          (f" for feature: {feature_name}" if feature_name else ""))
                          
            except Exception as e:
                logger.error(f"Failed to save {filename}: {str(e)}")
                raise
                
        return saved_paths
        
    def _save_single_file(self, filename: str, content: str, overwrite: bool) -> Path:
        """
        Save a single file to disk.
        
        Args:
            filename: Name of the file (can include subdirectories)
            content: File content
            overwrite: Whether to overwrite if exists
            
        Returns:
            Path to the saved file
        """
        # Handle nested paths
        file_path = self.current_session_path / filename
        
        # Create parent directories if needed
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if file exists and overwrite is False
        if file_path.exists() and not overwrite:
            # Append a number to make it unique
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
            "session_path": str(self.current_session_path)
        })
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
            
        logger.info(f"Saved session metadata to {metadata_path}")
        return metadata_path
        
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
        req_path.write_text("\n".join(dependencies) + "\n")
        
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
            "",
            "---",
            "_Generated by MVP Incremental Workflow_"
        ])
        
        readme_path = self.current_session_path / "README.md"
        readme_path.write_text("\n".join(readme_content))
        
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
                "file_list": []
            }
            
        total_size = sum(f.stat().st_size for f in self.files_saved if f.exists())
        
        return {
            "session_path": str(self.current_session_path),
            "files_saved": len(self.files_saved),
            "total_size": total_size,
            "total_size_kb": round(total_size / 1024, 2),
            "file_list": [str(f.relative_to(self.current_session_path)) for f in self.files_saved]
        }


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