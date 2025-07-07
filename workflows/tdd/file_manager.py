"""
TDD File Manager - Unified file management for Test-Driven Development workflow
Handles coordination between coder agent file generation and test execution
"""
import re
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from workflows.logger import workflow_logger as logger


@dataclass
class ProjectInfo:
    """Information about a generated project"""
    project_name: str
    project_path: Path
    files: Dict[str, str]  # filename -> content
    timestamp: str
    

class TDDFileManager:
    """Manages file operations for TDD workflow"""
    
    def __init__(self):
        self.current_project: Optional[ProjectInfo] = None
        self.test_files: Dict[str, str] = {}
        self.implementation_files: Dict[str, str] = {}
        
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
            
        try:
            for filename, content in files.items():
                file_path = self.current_project.project_path / filename
                
                # Create parent directories if needed
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Write file
                file_path.write_text(content, encoding='utf-8')
                logger.info(f"Updated {filename} in project")
                
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
                try:
                    return file_path.read_text(encoding='utf-8')
                except Exception as e:
                    logger.error(f"Error reading {filename}: {str(e)}")
                    
        return None
        
    def list_project_files(self) -> List[str]:
        """List all files in current project"""
        if not self.current_project:
            return []
            
        # Get files from memory
        files = list(self.current_project.files.keys())
        
        # Also check disk for any additional files
        if self.current_project.project_path.exists():
            for file_path in self.current_project.project_path.rglob('*'):
                if file_path.is_file() and not file_path.name.startswith('.'):
                    relative_path = file_path.relative_to(self.current_project.project_path)
                    if str(relative_path) not in files:
                        files.append(str(relative_path))
                        
        return sorted(files)
        
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