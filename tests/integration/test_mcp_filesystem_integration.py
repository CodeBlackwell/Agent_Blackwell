"""
Integration test for MCP File System Server and Client

Demonstrates end-to-end usage of the MCP filesystem integration
with the multi-agent system components.
"""

import unittest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch
import sys
import os

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from workflows.tdd.file_manager_mcp import TDDFileManagerMCP, create_tdd_file_manager
from workflows.mvp_incremental.code_saver_mcp import CodeSaverMCP, create_code_saver
from config.mcp_config import MCP_FILESYSTEM_CONFIG


class TestMCPFileSystemIntegration(unittest.TestCase):
    """Test MCP filesystem integration with workflow components."""
    
    def setUp(self):
        """Set up test environment."""
        # Create temporary directories
        self.test_dir = tempfile.mkdtemp()
        self.sandbox_dir = Path(self.test_dir) / "sandbox"
        self.sandbox_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock the MCP configuration to use test directory
        self.config_patch = patch.dict(MCP_FILESYSTEM_CONFIG, {
            "sandbox_root": str(self.sandbox_dir),
            "audit_log_path": str(Path(self.test_dir) / "audit.log")
        })
        self.config_patch.start()
    
    def tearDown(self):
        """Clean up test environment."""
        self.config_patch.stop()
        shutil.rmtree(self.test_dir)
    
    async def test_tdd_file_manager_with_mcp(self):
        """Test TDD File Manager using MCP filesystem."""
        # Create file manager with MCP enabled
        async with TDDFileManagerMCP(use_mcp=True, agent_name="test_tdd") as fm:
            # Simulate coder output
            coder_output = """
PROJECT CREATED: test_app_generated_20240101_120000

FILENAME: main.py
```python
def hello_world():
    return "Hello, World!"

if __name__ == "__main__":
    print(hello_world())
```

FILENAME: test_main.py
```python
import unittest
from main import hello_world

class TestMain(unittest.TestCase):
    def test_hello_world(self):
        self.assertEqual(hello_world(), "Hello, World!")
```

Location: ./generated/test_app_generated_20240101_120000
"""
            
            # Parse files
            files = fm.parse_files(coder_output)
            
            # Verify files were parsed
            self.assertEqual(len(files), 2)
            self.assertIn("main.py", files)
            self.assertIn("test_main.py", files)
            
            # Update files in project
            success = fm.update_files_in_project(files)
            self.assertTrue(success)
            
            # Verify files were created in sandbox
            project_path = self.sandbox_dir / "generated" / "test_app_generated_20240101_120000"
            self.assertTrue((project_path / "main.py").exists())
            self.assertTrue((project_path / "test_main.py").exists())
            
            # Read file content back
            content = fm.get_file_content("main.py")
            self.assertIsNotNone(content)
            self.assertIn("hello_world", content)
            
            # List project files
            file_list = fm.list_project_files()
            self.assertIn("main.py", file_list)
            self.assertIn("test_main.py", file_list)
    
    async def test_code_saver_with_mcp(self):
        """Test Code Saver using MCP filesystem."""
        # Create code saver with MCP enabled
        async with CodeSaverMCP(base_path=self.sandbox_dir / "projects", use_mcp=True) as cs:
            # Create session directory
            session_path = cs.create_session_directory("test_project")
            self.assertIsNotNone(session_path)
            
            # Save code files
            code_dict = {
                "app.py": """
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Welcome to the test app!"

if __name__ == '__main__':
    app.run(debug=True)
""",
                "requirements.txt": "flask>=2.0.0\n",
                "README.md": "# Test Project\n\nA simple Flask application."
            }
            
            saved_paths = cs.save_code_files(code_dict, feature_name="initial_setup")
            self.assertEqual(len(saved_paths), 3)
            
            # Save metadata
            metadata = {
                "project_name": "Test Project",
                "framework": "Flask",
                "features": ["Web server", "Home route"]
            }
            metadata_path = cs.save_metadata(metadata)
            self.assertTrue(metadata_path.exists())
            
            # Create requirements file
            dependencies = ["flask", "pytest", "requests"]
            req_path = cs.create_requirements_file(dependencies)
            self.assertIsNotNone(req_path)
            
            # Create README
            readme_path = cs.create_readme(
                project_name="Test Flask App",
                description="A demonstration Flask application",
                features=["Web server", "REST API", "Testing"],
                setup_instructions=["pip install -r requirements.txt", "python app.py"]
            )
            self.assertTrue(readme_path.exists())
            
            # Get summary
            summary = cs.get_summary()
            self.assertEqual(summary["files_saved"], 5)  # 3 code files + metadata + readme
            self.assertTrue(summary["used_mcp"])
            
            # Get metrics
            metrics = await cs.get_metrics()
            self.assertIsInstance(metrics, dict)
    
    def test_factory_functions(self):
        """Test factory functions for creating managers with MCP."""
        # Test TDD file manager factory
        fm = create_tdd_file_manager(use_mcp=True, agent_name="test_factory")
        self.assertTrue(fm.use_mcp)
        self.assertEqual(fm.agent_name, "test_factory")
        
        # Test code saver factory
        cs = create_code_saver(use_mcp=True, agent_name="test_saver")
        self.assertTrue(cs.use_mcp)
        self.assertEqual(cs.agent_name, "test_saver")
    
    def test_environment_variable_override(self):
        """Test that environment variable enables MCP."""
        with patch.dict(os.environ, {"USE_MCP_FILESYSTEM": "true"}):
            # Factory should enable MCP when env var is set
            fm = create_tdd_file_manager(use_mcp=False)  # Explicitly set to False
            self.assertTrue(fm.use_mcp)  # Should be True due to env var
            
            cs = create_code_saver(use_mcp=False)
            self.assertTrue(cs.use_mcp)
    
    async def test_mcp_audit_logging(self):
        """Test that MCP operations are properly audited."""
        audit_log_path = Path(self.test_dir) / "audit.log"
        
        # Perform some operations
        async with CodeSaverMCP(base_path=self.sandbox_dir, use_mcp=True) as cs:
            cs.create_session_directory("audit_test")
            cs.save_code_files({"test.py": "print('hello')"})
        
        # Check audit log exists
        self.assertTrue(audit_log_path.exists())
        
        # Read audit log
        with open(audit_log_path) as f:
            log_content = f.read()
        
        # Verify operations were logged
        self.assertIn("create_directory", log_content)
        self.assertIn("write_file", log_content)
    
    async def test_error_handling(self):
        """Test error handling in MCP operations."""
        # Test with invalid sandbox path
        with patch.dict(MCP_FILESYSTEM_CONFIG, {
            "sandbox_root": "/nonexistent/path"
        }):
            fm = TDDFileManagerMCP(use_mcp=True)
            
            # This should handle the error gracefully
            files = {"test.py": "content"}
            success = fm.update_files_in_project(files)
            self.assertFalse(success)  # Should fail due to invalid path


class TestMCPFileSystemPerformance(unittest.TestCase):
    """Performance tests for MCP filesystem operations."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.sandbox_dir = Path(self.test_dir) / "sandbox"
        self.sandbox_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock configuration
        self.config_patch = patch.dict(MCP_FILESYSTEM_CONFIG, {
            "sandbox_root": str(self.sandbox_dir)
        })
        self.config_patch.start()
    
    def tearDown(self):
        """Clean up test environment."""
        self.config_patch.stop()
        shutil.rmtree(self.test_dir)
    
    async def test_batch_file_operations(self):
        """Test performance of batch file operations."""
        async with CodeSaverMCP(base_path=self.sandbox_dir, use_mcp=True) as cs:
            cs.create_session_directory("batch_test")
            
            # Create many files
            code_dict = {}
            for i in range(50):
                code_dict[f"module_{i}.py"] = f"# Module {i}\nprint('Module {i}')"
            
            # Time the operation
            import time
            start_time = time.time()
            saved_paths = cs.save_code_files(code_dict)
            end_time = time.time()
            
            # Verify all files were saved
            self.assertEqual(len(saved_paths), 50)
            
            # Check performance
            duration = end_time - start_time
            print(f"Saved 50 files in {duration:.2f} seconds")
            
            # Get metrics
            metrics = await cs.get_metrics()
            if metrics:
                print(f"MCP Metrics: {metrics}")


if __name__ == "__main__":
    # Run async tests
    unittest.main()