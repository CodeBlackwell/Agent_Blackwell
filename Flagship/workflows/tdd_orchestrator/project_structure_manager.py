"""Project Structure Manager for handling multi-file project generation"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from .enhanced_models import ProjectArchitecture, MultiFileOutput


class ProjectStructureManager:
    """Manages project structure and file generation for multi-file projects"""
    
    def __init__(self, base_output_dir: str = "./generated"):
        """
        Initialize project structure manager
        Args:
            base_output_dir: Base directory for generated projects
        """
        self.base_output_dir = Path(base_output_dir)
        self.base_output_dir.mkdir(exist_ok=True)
        
        # Current project directory
        self.current_project_dir: Optional[Path] = None
        
        # Temporary directory for test execution
        self.temp_dir = Path("/tmp/tdd_temp") if os.name != 'nt' else Path("C:/temp/tdd_temp")
        self.temp_dir.mkdir(exist_ok=True)
    
    def setup_project_structure(self, architecture: ProjectArchitecture) -> Path:
        """
        Set up project directory structure based on architecture
        Returns: Path to project root
        """
        # Create project directory with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        project_name = f"{architecture.project_type}_{timestamp}"
        self.current_project_dir = self.base_output_dir / project_name
        self.current_project_dir.mkdir(exist_ok=True)
        
        print(f"📁 Setting up project structure in: {self.current_project_dir}")
        
        # Create directory structure
        for category, paths in architecture.structure.items():
            category_dir = self.current_project_dir / category
            category_dir.mkdir(exist_ok=True)
            
            # Create placeholder files
            for filepath in paths:
                file_path = self.current_project_dir / filepath
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Create placeholder content based on file type
                placeholder = self._get_placeholder_content(filepath, architecture)
                file_path.write_text(placeholder)
        
        # Create project metadata
        metadata = {
            "project_type": architecture.project_type,
            "created_at": timestamp,
            "technology_stack": architecture.technology_stack,
            "structure": architecture.structure
        }
        
        metadata_path = self.current_project_dir / "project_metadata.json"
        metadata_path.write_text(json.dumps(metadata, indent=2))
        
        print(f"✅ Project structure created with {len(architecture.structure)} categories")
        return self.current_project_dir
    
    def save_generated_files(self, files: Dict[str, str]) -> Dict[str, Path]:
        """
        Save generated files to project directory
        Returns: Dictionary mapping relative paths to absolute paths
        """
        if not self.current_project_dir:
            # Create default project directory if not set
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.current_project_dir = self.base_output_dir / f"project_{timestamp}"
            self.current_project_dir.mkdir(exist_ok=True)
        
        saved_files = {}
        
        for relative_path, content in files.items():
            # Determine full path
            if relative_path.startswith("/"):
                # Absolute path provided, make it relative
                relative_path = relative_path[1:]
            
            file_path = self.current_project_dir / relative_path
            
            # Create parent directories
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save file
            file_path.write_text(content)
            saved_files[relative_path] = file_path
            
            print(f"💾 Saved: {relative_path}")
        
        # Update project manifest
        self._update_project_manifest(saved_files)
        
        return saved_files
    
    def save_temp_files(self, files: Dict[str, str]) -> Path:
        """
        Save files temporarily for test execution
        Returns: Path to temporary directory
        """
        # Create unique temp directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        temp_project_dir = self.temp_dir / f"test_run_{timestamp}"
        temp_project_dir.mkdir(exist_ok=True)
        
        for relative_path, content in files.items():
            file_path = temp_project_dir / relative_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
        
        return temp_project_dir
    
    def organize_by_file_type(self, files: Dict[str, str]) -> Dict[str, List[str]]:
        """
        Organize files by their type/category
        Returns: Dictionary mapping categories to file lists
        """
        organized = {
            "frontend": [],
            "backend": [],
            "tests": [],
            "config": [],
            "documentation": [],
            "other": []
        }
        
        for filepath in files.keys():
            category = self._categorize_file(filepath)
            organized[category].append(filepath)
        
        return organized
    
    def create_project_summary(self) -> Dict[str, Any]:
        """Create a summary of the generated project"""
        if not self.current_project_dir:
            return {"error": "No project directory set"}
        
        # Count files by type
        file_counts = {
            "python": 0,
            "javascript": 0,
            "html": 0,
            "css": 0,
            "config": 0,
            "test": 0,
            "other": 0
        }
        
        total_lines = 0
        
        for file_path in self.current_project_dir.rglob("*"):
            if file_path.is_file() and file_path.name != "project_metadata.json":
                # Count by type
                if file_path.suffix == ".py":
                    if "test" in file_path.name:
                        file_counts["test"] += 1
                    else:
                        file_counts["python"] += 1
                elif file_path.suffix in [".js", ".jsx", ".ts", ".tsx"]:
                    file_counts["javascript"] += 1
                elif file_path.suffix == ".html":
                    file_counts["html"] += 1
                elif file_path.suffix == ".css":
                    file_counts["css"] += 1
                elif file_path.name in ["requirements.txt", "package.json", "Dockerfile", ".env"]:
                    file_counts["config"] += 1
                else:
                    file_counts["other"] += 1
                
                # Count lines
                try:
                    total_lines += len(file_path.read_text().splitlines())
                except:
                    pass
        
        return {
            "project_directory": str(self.current_project_dir),
            "file_counts": file_counts,
            "total_files": sum(file_counts.values()),
            "total_lines": total_lines,
            "structure": self._get_directory_tree()
        }
    
    def _get_placeholder_content(self, filepath: str, architecture: ProjectArchitecture) -> str:
        """Generate placeholder content based on file type"""
        filename = Path(filepath).name
        
        # Python files
        if filepath.endswith(".py"):
            if "test" in filename:
                return f'"""Tests for {architecture.project_type}"""\n\nimport pytest\n\n# TODO: Implement tests'
            elif filename == "__init__.py":
                return f'"""Package initialization for {Path(filepath).parent}"""'
            else:
                return f'"""Module: {filename}"""\n\n# TODO: Implement module'
        
        # JavaScript files
        elif filepath.endswith((".js", ".jsx")):
            return f'// {filename} - TODO: Implement\n\n'
        
        # HTML files
        elif filepath.endswith(".html"):
            return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{architecture.project_type}</title>
</head>
<body>
    <!-- TODO: Implement UI -->
</body>
</html>'''
        
        # CSS files
        elif filepath.endswith(".css"):
            return f'/* Styles for {architecture.project_type} */\n\n/* TODO: Add styles */'
        
        # Configuration files
        elif filename == "requirements.txt":
            stack = architecture.technology_stack.get("backend", "").lower()
            if "flask" in stack:
                return "Flask>=2.0.0\npytest>=7.0.0\n"
            elif "fastapi" in stack:
                return "fastapi>=0.100.0\nuvicorn>=0.23.0\npytest>=7.0.0\n"
            else:
                return "# Add Python dependencies here\n"
        
        elif filename == "package.json":
            return json.dumps({
                "name": architecture.project_type,
                "version": "1.0.0",
                "description": f"Generated {architecture.project_type} project",
                "dependencies": {},
                "devDependencies": {}
            }, indent=2)
        
        # Default
        return f"# {filename} - Generated by Enhanced TDD Workflow\n"
    
    def _categorize_file(self, filepath: str) -> str:
        """Categorize a file based on its path and name"""
        filepath_lower = filepath.lower()
        
        if any(x in filepath_lower for x in ["test", "spec"]):
            return "tests"
        elif any(x in filepath_lower for x in ["frontend", "static", "public", "client", ".html", ".css", ".js", ".jsx"]):
            return "frontend"
        elif any(x in filepath_lower for x in ["backend", "server", "api", ".py", ".rb", ".java"]) and "test" not in filepath_lower:
            return "backend"
        elif any(x in filepath_lower for x in ["requirements", "package.json", "dockerfile", ".env", "config"]):
            return "config"
        elif any(x in filepath_lower for x in ["readme", ".md", "docs"]):
            return "documentation"
        else:
            return "other"
    
    def _update_project_manifest(self, saved_files: Dict[str, Path]):
        """Update the project manifest with newly saved files"""
        if not self.current_project_dir:
            return
        
        manifest_path = self.current_project_dir / "file_manifest.json"
        
        # Load existing manifest or create new
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text())
        else:
            manifest = {
                "created_at": datetime.now().isoformat(),
                "files": {}
            }
        
        # Update with new files
        for relative_path, absolute_path in saved_files.items():
            manifest["files"][relative_path] = {
                "absolute_path": str(absolute_path),
                "size": absolute_path.stat().st_size,
                "modified_at": datetime.now().isoformat()
            }
        
        manifest["last_updated"] = datetime.now().isoformat()
        manifest["total_files"] = len(manifest["files"])
        
        # Save updated manifest
        manifest_path.write_text(json.dumps(manifest, indent=2))
    
    def _get_directory_tree(self) -> List[str]:
        """Get directory tree structure as list of strings"""
        if not self.current_project_dir:
            return []
        
        tree = []
        
        def add_tree_level(path: Path, prefix: str = "", is_last: bool = True):
            if path == self.current_project_dir:
                tree.append(path.name + "/")
            else:
                connector = "└── " if is_last else "├── "
                tree.append(prefix + connector + path.name + ("/" if path.is_dir() else ""))
            
            if path.is_dir():
                children = sorted(list(path.iterdir()))
                for i, child in enumerate(children):
                    # Skip metadata files
                    if child.name in ["project_metadata.json", "file_manifest.json"]:
                        continue
                    
                    extension = "    " if is_last else "│   "
                    add_tree_level(child, prefix + extension, i == len(children) - 1)
        
        add_tree_level(self.current_project_dir)
        return tree
    
    def cleanup_temp_files(self):
        """Clean up temporary test files"""
        if self.temp_dir.exists():
            # Remove directories older than 1 hour
            import time
            current_time = time.time()
            
            for temp_project in self.temp_dir.iterdir():
                if temp_project.is_dir():
                    # Check age
                    age = current_time - temp_project.stat().st_mtime
                    if age > 3600:  # 1 hour
                        shutil.rmtree(temp_project)
                        print(f"🧹 Cleaned up old temp directory: {temp_project.name}")