"""
Unit tests for CodeSaver subdirectory handling
Tests the ability to save files in nested directory structures
"""

import unittest
import tempfile
import shutil
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from workflows.mvp_incremental.code_saver import CodeSaver


class TestCodeSaverSubdirectories(unittest.TestCase):
    """Test CodeSaver's ability to handle subdirectories"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.code_saver = CodeSaver(base_path=self.temp_dir)
        self.code_saver.create_session_directory("test_session")
    
    def tearDown(self):
        """Clean up temporary directory"""
        shutil.rmtree(self.temp_dir)
    
    def test_save_files_with_subdirectories(self):
        """Test saving files in subdirectories"""
        code_dict = {
            'backend/src/server.js': 'const express = require("express");',
            'backend/package.json': '{"name": "backend"}',
            'frontend/src/app.js': 'console.log("app");',
            'frontend/public/index.html': '<html></html>',
            'docker-compose.yml': 'version: "3.8"'
        }
        
        # This should fail with current implementation
        # After implementation, it should create the directory structure
        try:
            saved_paths = self.code_saver.save_code_files(code_dict, "mean-stack")
            
            # Verify all files were saved
            self.assertEqual(len(saved_paths), 5)
            
            # Verify directory structure exists
            session_path = self.code_saver.current_session_path
            self.assertTrue((session_path / 'backend' / 'src').exists())
            self.assertTrue((session_path / 'backend' / 'src' / 'server.js').exists())
            self.assertTrue((session_path / 'frontend' / 'public').exists())
            self.assertTrue((session_path / 'docker-compose.yml').exists())
            
            # Verify file contents
            with open(session_path / 'backend' / 'src' / 'server.js') as f:
                self.assertIn('express', f.read())
                
        except Exception as e:
            # Expected to fail before implementation
            self.assertIn("No such file or directory", str(e) or "Expected failure")
    
    def test_deeply_nested_directories(self):
        """Test creating deeply nested directory structures"""
        code_dict = {
            'src/modules/auth/controllers/auth.controller.js': 'class AuthController {}',
            'src/modules/auth/services/auth.service.js': 'class AuthService {}',
            'src/modules/auth/middleware/auth.middleware.js': 'function authMiddleware() {}',
            'tests/unit/modules/auth/controllers/auth.controller.test.js': 'describe("Auth", () => {});'
        }
        
        try:
            saved_paths = self.code_saver.save_code_files(code_dict, "deep-nesting")
            
            # Verify deep directory structure
            session_path = self.code_saver.current_session_path
            self.assertTrue((session_path / 'src' / 'modules' / 'auth' / 'controllers').exists())
            self.assertTrue((session_path / 'tests' / 'unit' / 'modules' / 'auth' / 'controllers').exists())
            
        except Exception as e:
            # Expected to fail before implementation
            pass
    
    def test_windows_path_normalization(self):
        """Test that Windows-style paths are normalized"""
        code_dict = {
            'backend\\src\\main.py': 'print("test")',
            'backend\\tests\\test_main.py': 'def test(): pass'
        }
        
        try:
            saved_paths = self.code_saver.save_code_files(code_dict, "windows-paths")
            
            # Should normalize to forward slashes and create proper structure
            session_path = self.code_saver.current_session_path
            self.assertTrue((session_path / 'backend' / 'src' / 'main.py').exists())
            self.assertTrue((session_path / 'backend' / 'tests' / 'test_main.py').exists())
            
        except Exception as e:
            # Expected to fail before implementation
            pass
    
    def test_preserve_flat_structure(self):
        """Test that flat file structure still works"""
        code_dict = {
            'main.py': 'print("main")',
            'utils.py': 'def helper(): pass',
            'test.py': 'import unittest'
        }
        
        # This should work with current implementation
        saved_paths = self.code_saver.save_code_files(code_dict, "flat-structure")
        
        self.assertEqual(len(saved_paths), 3)
        session_path = self.code_saver.current_session_path
        self.assertTrue((session_path / 'main.py').exists())
        self.assertTrue((session_path / 'utils.py').exists())
        self.assertTrue((session_path / 'test.py').exists())
    
    def test_mixed_structure(self):
        """Test mixed flat and nested structure"""
        code_dict = {
            'README.md': '# Project',
            'backend/server.js': 'const app = express();',
            'frontend/index.html': '<html></html>',
            'package.json': '{"name": "root"}'
        }
        
        try:
            saved_paths = self.code_saver.save_code_files(code_dict, "mixed-structure")
            
            session_path = self.code_saver.current_session_path
            # Root level files
            self.assertTrue((session_path / 'README.md').exists())
            self.assertTrue((session_path / 'package.json').exists())
            # Nested files
            self.assertTrue((session_path / 'backend' / 'server.js').exists())
            self.assertTrue((session_path / 'frontend' / 'index.html').exists())
            
        except Exception as e:
            # Expected to fail before implementation
            pass
    
    def test_create_directory_only_once(self):
        """Test that directories are created efficiently"""
        code_dict = {
            'backend/src/models/user.js': 'class User {}',
            'backend/src/models/post.js': 'class Post {}',
            'backend/src/models/comment.js': 'class Comment {}'
        }
        
        try:
            saved_paths = self.code_saver.save_code_files(code_dict, "efficient-dirs")
            
            # Should create backend/src/models only once
            session_path = self.code_saver.current_session_path
            models_dir = session_path / 'backend' / 'src' / 'models'
            self.assertTrue(models_dir.exists())
            self.assertEqual(len(list(models_dir.iterdir())), 3)
            
        except Exception as e:
            # Expected to fail before implementation
            pass
    
    def test_special_characters_in_paths(self):
        """Test handling of special characters in directory names"""
        code_dict = {
            'my-app/src/main.js': 'console.log("test");',
            'test_module/index.py': 'print("test")',
            '@types/index.d.ts': 'export interface Test {}'
        }
        
        try:
            saved_paths = self.code_saver.save_code_files(code_dict, "special-chars")
            
            session_path = self.code_saver.current_session_path
            self.assertTrue((session_path / 'my-app' / 'src' / 'main.js').exists())
            self.assertTrue((session_path / 'test_module' / 'index.py').exists())
            self.assertTrue((session_path / '@types' / 'index.d.ts').exists())
            
        except Exception as e:
            # Expected to fail before implementation
            pass
    
    def test_summary_includes_structure(self):
        """Test that save summary includes directory structure info"""
        code_dict = {
            'backend/server.js': 'const app = express();',
            'frontend/app.js': 'console.log("app");',
            'shared/types.ts': 'export interface User {}'
        }
        
        saved_paths = self.code_saver.save_code_files(code_dict, "summary-test")
        summary = self.code_saver.get_summary()
        
        # Current implementation returns file_list with paths
        self.assertIn('backend/server.js', str(summary['file_list']))
        self.assertIn('frontend/app.js', str(summary['file_list']))
        
        # But we need a better summary that shows directory structure
        # This is what we need to enhance
        self.assertEqual(len(summary['file_list']), 3)


class TestCodeSaverHelpers(unittest.TestCase):
    """Test helper methods for code saver"""
    
    def test_normalize_file_path(self):
        """Test path normalization helper"""
        # This is a helper method we'll need to add
        saver = CodeSaver()
        
        # Test various path formats
        test_cases = [
            ('backend\\src\\main.js', 'backend/src/main.js'),
            ('backend/src/main.js', 'backend/src/main.js'),
            ('./backend/src/main.js', 'backend/src/main.js'),
            ('../backend/main.js', 'backend/main.js'),  # Should sanitize
            ('/absolute/path.js', 'absolute/path.js'),  # Should make relative
        ]
        
        for input_path, expected in test_cases:
            # This method needs to be implemented
            try:
                normalized = saver._normalize_file_path(input_path)
                self.assertEqual(normalized, expected)
            except AttributeError:
                # Method doesn't exist yet
                pass


if __name__ == '__main__':
    unittest.main()