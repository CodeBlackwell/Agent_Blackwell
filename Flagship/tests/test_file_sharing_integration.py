"""Integration tests for file sharing between agents"""

import asyncio
import pytest
import tempfile
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from agents.test_writer_flagship import TestWriterFlagship
from agents.coder_flagship import CoderFlagship
from agents.test_runner_flagship import TestRunnerFlagship
from utils.enhanced_file_manager import EnhancedFileManager
from models.flagship_models import TestResult, TestStatus


class TestFileSharingIntegration:
    """Test suite for file sharing between agents"""
    
    @pytest.fixture
    def temp_project_root(self):
        """Create a temporary directory for tests"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def file_manager(self, temp_project_root):
        """Create a shared file manager instance"""
        return EnhancedFileManager(
            session_id="integration_test",
            project_root=temp_project_root
        )
    
    @pytest.fixture
    def agents(self, file_manager):
        """Create agents with shared file manager"""
        return {
            'test_writer': TestWriterFlagship(file_manager=file_manager),
            'coder': CoderFlagship(file_manager=file_manager),
            'test_runner': TestRunnerFlagship(file_manager=file_manager)
        }
    
    @pytest.mark.asyncio
    async def test_test_writer_saves_files(self, agents, file_manager):
        """Test that test writer saves files that can be accessed"""
        test_writer = agents['test_writer']
        
        # Run test writer
        output = ""
        async for chunk in test_writer.write_tests("Create a simple greet function"):
            output += chunk
        
        # Verify file was saved
        test_files = file_manager.list_files("*test*.py")
        assert len(test_files) > 0
        
        # Verify content
        test_content = file_manager.read_file("test_generated.py")
        assert test_content is not None
        assert "greet" in test_content
        assert "def test_" in test_content
    
    @pytest.mark.asyncio
    async def test_coder_reads_test_files(self, agents, file_manager):
        """Test that coder can read test files written by test writer"""
        test_writer = agents['test_writer']
        coder = agents['coder']
        
        # First, have test writer create tests
        async for _ in test_writer.write_tests("Create a calculator with add function"):
            pass
        
        # Create mock test results
        test_results = [
            TestResult(
                test_name="test_addition",
                status=TestStatus.FAILED,
                error_message="Calculator not found"
            )
        ]
        
        # Now have coder read the tests and implement
        output = ""
        async for chunk in coder.write_code("", test_results):
            output += chunk
        
        # Verify coder found and loaded test files
        assert "Found 1 test file(s)" in output
        
        # Verify implementation was saved
        impl_content = file_manager.read_file("implementation_generated.py")
        assert impl_content is not None
        assert "Calculator" in impl_content or "add" in impl_content
    
    @pytest.mark.asyncio
    async def test_test_runner_accesses_all_files(self, agents, file_manager):
        """Test that test runner can access both test and implementation files"""
        test_runner = agents['test_runner']
        
        # Pre-create test and implementation files
        test_code = '''import pytest
def test_simple():
    assert 1 + 1 == 2'''
        
        impl_code = '''def add(a, b):
    return a + b'''
        
        file_manager.write_file("test_simple.py", test_code)
        file_manager.write_file("implementation.py", impl_code)
        
        # Run test runner without providing code (should load from files)
        output = ""
        async for chunk in test_runner.run_tests("", ""):
            output += chunk
        
        # Verify files were found and loaded
        assert "Found 2 Python file(s) in session" in output
        # The test runner will try to infer the test file first, so it may load implementation as test
        assert "Loaded test code from" in output or "Loaded implementation from" in output
    
    @pytest.mark.asyncio
    async def test_full_workflow_file_sharing(self, agents, file_manager):
        """Test complete workflow with file sharing"""
        test_writer = agents['test_writer']
        coder = agents['coder']
        test_runner = agents['test_runner']
        
        # Step 1: Write tests
        async for _ in test_writer.write_tests("Create a simple greet function"):
            pass
        
        # Verify test file exists
        test_content = file_manager.read_file("test_generated.py")
        assert test_content is not None
        
        # Step 2: Write implementation
        test_results = [
            TestResult(
                test_name="test_basic_greeting",
                status=TestStatus.FAILED,
                error_message="greet not defined"
            )
        ]
        
        async for _ in coder.write_code(test_content, test_results):
            pass
        
        # Verify implementation file exists
        impl_content = file_manager.read_file("implementation_generated.py")
        assert impl_content is not None
        
        # Step 3: Run tests
        output = ""
        async for chunk in test_runner.run_tests(test_content, impl_content):
            output += chunk
        
        # Tests should find the greet function
        assert "greet" in output.lower()
    
    @pytest.mark.asyncio
    async def test_file_persistence_across_iterations(self, file_manager):
        """Test that files persist across multiple agent interactions"""
        # Create agent, write file, then create new agent instance
        agent1 = TestWriterFlagship(file_manager=file_manager)
        async for _ in agent1.write_tests("Create test"):
            pass
        
        # Create new agent instance with same file manager
        agent2 = CoderFlagship(file_manager=file_manager)
        
        # New agent should see the files
        context = file_manager.get_file_context("coder")
        assert len(context["test_files"]) > 0
        
        # Verify content is accessible
        test_content = file_manager.read_file("test_generated.py")
        assert test_content is not None
    
    @pytest.mark.asyncio
    async def test_agent_builds_on_existing_code(self, agents, file_manager):
        """Test that agents can build upon existing code"""
        coder = agents['coder']
        
        # Pre-create an existing implementation
        existing_code = '''class Calculator:
    def add(self, a, b):
        return a + b'''
        
        file_manager.write_file("calculator.py", existing_code)
        
        # Have coder implement with awareness of existing code
        test_results = [
            TestResult(
                test_name="test_subtract",
                status=TestStatus.FAILED,
                error_message="Calculator.subtract not found"
            )
        ]
        
        output = ""
        async for chunk in coder.write_code("", test_results):
            output += chunk
        
        # Should detect existing implementation
        assert "Found 1 existing implementation file(s)" in output
        assert "calculator.py" in output
    
    @pytest.mark.asyncio
    async def test_session_metadata_tracking(self, file_manager, agents):
        """Test that session metadata tracks all file operations"""
        # Perform operations with different agents
        async for _ in agents['test_writer'].write_tests("test"):
            pass
        async for _ in agents['coder'].write_code("", []):
            pass
        
        # Save and check metadata
        file_manager.save_session_metadata()
        
        metadata_file = file_manager.session_dir / "session_metadata.json"
        assert metadata_file.exists()
        
        import json
        metadata = json.loads(metadata_file.read_text())
        assert len(metadata["session_files"]) >= 2
        assert "test_generated.py" in str(metadata["session_files"])
        assert "implementation_generated.py" in str(metadata["session_files"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])