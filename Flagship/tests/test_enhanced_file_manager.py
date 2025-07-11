"""Unit tests for EnhancedFileManager"""

import pytest
import tempfile
from pathlib import Path
import json
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.enhanced_file_manager import EnhancedFileManager


class TestEnhancedFileManager:
    """Test suite for EnhancedFileManager"""
    
    @pytest.fixture
    def temp_project_root(self):
        """Create a temporary directory for tests"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def file_manager(self, temp_project_root):
        """Create a file manager instance"""
        return EnhancedFileManager(
            session_id="test_session_123",
            project_root=temp_project_root
        )
    
    def test_initialization(self, file_manager, temp_project_root):
        """Test file manager initialization"""
        assert file_manager.session_id == "test_session_123"
        assert file_manager.project_root == temp_project_root
        assert file_manager.session_dir.exists()
        assert "test_session_123" in str(file_manager.session_dir)
    
    def test_write_and_read_file(self, file_manager):
        """Test writing and reading files"""
        # Write a file
        content = "def hello():\n    return 'Hello, World!'"
        assert file_manager.write_file("hello.py", content)
        
        # Read it back
        read_content = file_manager.read_file("hello.py")
        assert read_content == content
        
        # Check it's in cache
        assert str(file_manager.session_dir / "hello.py") in file_manager._file_cache
    
    def test_write_file_with_subdirectory(self, file_manager):
        """Test writing files in subdirectories"""
        content = "import pytest"
        assert file_manager.write_file("tests/test_example.py", content)
        
        # Verify file exists
        file_path = file_manager.session_dir / "tests" / "test_example.py"
        assert file_path.exists()
        assert file_path.read_text() == content
    
    def test_read_nonexistent_file(self, file_manager):
        """Test reading a file that doesn't exist"""
        content = file_manager.read_file("nonexistent.py")
        assert content is None
    
    def test_update_existing_file(self, file_manager):
        """Test updating an existing file"""
        # First write a file
        original_content = "original content"
        file_manager.write_file("update_me.py", original_content, session_scope=False)
        
        # Update it
        new_content = "updated content"
        assert file_manager.update_file(
            file_manager.project_root / "update_me.py", 
            new_content
        )
        
        # Read and verify
        read_content = file_manager.read_file("update_me.py")
        assert read_content == new_content
    
    def test_update_nonexistent_file(self, file_manager):
        """Test updating a file that doesn't exist"""
        assert not file_manager.update_file("nonexistent.py", "content")
    
    def test_list_files(self, file_manager):
        """Test listing files"""
        # Create some files
        file_manager.write_file("file1.py", "content1")
        file_manager.write_file("file2.py", "content2")
        file_manager.write_file("test_file.py", "test content")
        file_manager.write_file("data.json", "{}")
        
        # List all files
        all_files = file_manager.list_files()
        assert len(all_files) >= 4
        
        # List only Python files
        py_files = file_manager.list_files("*.py")
        py_file_names = [f.name for f in py_files]
        assert "file1.py" in py_file_names
        assert "file2.py" in py_file_names
        assert "test_file.py" in py_file_names
        assert "data.json" not in py_file_names
        
        # List only test files
        test_files = file_manager.list_files("*test*.py")
        test_file_names = [f.name for f in test_files]
        assert "test_file.py" in test_file_names
        assert "file1.py" not in test_file_names
    
    def test_get_file_context_for_test_writer(self, file_manager):
        """Test getting file context for test writer agent"""
        # Create some test files
        file_manager.write_file("test_existing.py", "existing tests")
        file_manager.write_file("test_another.py", "more tests")
        
        context = file_manager.get_file_context("test_writer")
        
        assert "existing_tests" in context
        assert len(context["existing_tests"]) >= 2
        assert any("test_existing.py" in path for path in context["existing_tests"])
    
    def test_get_file_context_for_coder(self, file_manager):
        """Test getting file context for coder agent"""
        # Create test and implementation files
        file_manager.write_file("test_calculator.py", "test code")
        file_manager.write_file("calculator.py", "implementation")
        file_manager.write_file("utils.py", "utilities")
        
        context = file_manager.get_file_context("coder")
        
        assert "test_files" in context
        assert "implementation_files" in context
        assert len(context["test_files"]) >= 1
        assert len(context["implementation_files"]) >= 2
    
    def test_get_file_context_for_test_runner(self, file_manager):
        """Test getting file context for test runner agent"""
        # Create various Python files
        file_manager.write_file("test_main.py", "tests")
        file_manager.write_file("main.py", "code")
        file_manager.write_file("helper.py", "helpers")
        
        context = file_manager.get_file_context("test_runner")
        
        assert "all_python_files" in context
        assert len(context["all_python_files"]) >= 3
    
    def test_cache_functionality(self, file_manager):
        """Test file caching"""
        content = "cached content"
        file_manager.write_file("cached.py", content)
        
        # First read (from disk)
        read1 = file_manager.read_file("cached.py")
        assert read1 == content
        
        # Modify the file on disk directly
        file_path = file_manager.session_dir / "cached.py"
        file_path.write_text("modified on disk")
        
        # Read with cache (should return cached content)
        read2 = file_manager.read_file("cached.py", use_cache=True)
        assert read2 == content  # Still cached
        
        # Read without cache (should return disk content)
        read3 = file_manager.read_file("cached.py", use_cache=False)
        assert read3 == "modified on disk"
    
    def test_clear_cache(self, file_manager):
        """Test clearing the cache"""
        # Add some files to cache
        file_manager.write_file("file1.py", "content1")
        file_manager.write_file("file2.py", "content2")
        
        assert len(file_manager._file_cache) >= 2
        
        # Clear cache
        file_manager.clear_cache()
        assert len(file_manager._file_cache) == 0
    
    def test_save_session_metadata(self, file_manager):
        """Test saving session metadata"""
        # Create some files and operations
        file_manager.write_file("test.py", "test content")
        file_manager.read_file("test.py")
        
        # Save metadata
        file_manager.save_session_metadata()
        
        # Check metadata file exists
        metadata_file = file_manager.session_dir / "session_metadata.json"
        assert metadata_file.exists()
        
        # Load and verify metadata
        metadata = json.loads(metadata_file.read_text())
        assert metadata["session_id"] == "test_session_123"
        assert "created_at" in metadata
        assert "session_files" in metadata
        assert "file_metadata" in metadata
    
    def test_session_vs_project_scope(self, file_manager):
        """Test session-scoped vs project-scoped file writing"""
        # Write to session scope (default)
        file_manager.write_file("session_file.py", "session content")
        session_path = file_manager.session_dir / "session_file.py"
        assert session_path.exists()
        
        # Write to project scope
        file_manager.write_file("project_file.py", "project content", session_scope=False)
        project_path = file_manager.project_root / "project_file.py"
        assert project_path.exists()
        
        # Verify different locations
        assert session_path.parent != project_path.parent
    
    def test_file_metadata_tracking(self, file_manager):
        """Test that file operations are tracked in metadata"""
        # Perform various operations
        file_manager.write_file("tracked.py", "content")
        file_manager.read_file("tracked.py")
        file_manager.update_file(file_manager.session_dir / "tracked.py", "updated")
        
        # Check metadata - look for all possible keys
        possible_keys = [
            str(file_manager.session_dir / "tracked.py"),
            str(file_manager.project_root / "tracked.py"),
            "tracked.py"
        ]
        
        key = None
        for k in possible_keys:
            if k in file_manager._file_metadata:
                key = k
                break
        
        # Debug: print all metadata keys
        print(f"Metadata keys: {list(file_manager._file_metadata.keys())}")
        
        assert key is not None, f"No metadata found for tracked.py. Keys: {list(file_manager._file_metadata.keys())}"
        
        metadata = file_manager._file_metadata[key]
        assert "first_accessed" in metadata
        assert "last_accessed" in metadata
        assert "operations" in metadata
        
        # Check operations were tracked
        operations = metadata["operations"]
        operation_types = [op["type"] for op in operations]
        print(f"Operations tracked: {operation_types}")
        assert "write" in operation_types
        assert "read" in operation_types


if __name__ == "__main__":
    pytest.main([__file__, "-v"])