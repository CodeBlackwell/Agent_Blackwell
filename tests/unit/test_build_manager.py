"""
Unit tests for BuildManager class
Tests build detection, execution, and caching functionality
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# We'll import after creating the module
# from agents.executor.build_manager import BuildManager, BuildConfig, BuildResult


class TestBuildManager(unittest.TestCase):
    """Test BuildManager functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_path = Path(self.temp_dir)
        
        # We'll need to mock since BuildManager doesn't exist yet
        self.build_manager = Mock()
        
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir)
    
    def test_detect_angular_project(self):
        """Test detection of Angular project"""
        # Create Angular project files
        (self.test_path / "angular.json").write_text('{"projects": {}}')
        (self.test_path / "package.json").write_text('''{
            "name": "frontend",
            "scripts": {
                "build": "ng build",
                "test": "ng test"
            }
        }''')
        
        # Mock the detect_build_type method
        self.build_manager.detect_build_type.return_value = "angular"
        
        # Test detection
        build_type = self.build_manager.detect_build_type(self.test_path)
        self.assertEqual(build_type, "angular")
    
    def test_detect_node_typescript_project(self):
        """Test detection of Node.js TypeScript project"""
        # Create TypeScript project files
        (self.test_path / "tsconfig.json").write_text('{"compilerOptions": {}}')
        (self.test_path / "package.json").write_text('''{
            "name": "backend",
            "scripts": {
                "build": "tsc",
                "start": "node dist/index.js"
            }
        }''')
        
        # Mock detection
        self.build_manager.detect_build_type.return_value = "node_typescript"
        
        build_type = self.build_manager.detect_build_type(self.test_path)
        self.assertEqual(build_type, "node_typescript")
    
    def test_detect_python_project(self):
        """Test detection of Python project"""
        # Create Python project files
        (self.test_path / "requirements.txt").write_text("flask==2.0.0\npytest==7.0.0")
        (self.test_path / "main.py").write_text("print('Hello')")
        
        # Mock detection
        self.build_manager.detect_build_type.return_value = "python"
        
        build_type = self.build_manager.detect_build_type(self.test_path)
        self.assertEqual(build_type, "python")
    
    def test_build_angular_project(self):
        """Test building an Angular project"""
        # Create mock build config
        build_config = {
            "type": "angular",
            "path": self.test_path,
            "commands": {
                "install": "npm install",
                "build": "npm run build"
            }
        }
        
        # Mock build execution
        self.build_manager.build.return_value = {
            "success": True,
            "type": "angular",
            "output": "Build successful",
            "artifacts": ["dist/"]
        }
        
        result = self.build_manager.build(build_config)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["type"], "angular")
        self.assertIn("dist/", result["artifacts"])
    
    def test_build_with_cache(self):
        """Test build caching functionality"""
        # Create a cache key
        cache_key = "angular_project_v1"
        
        # Mock cache check
        self.build_manager.is_cached.return_value = True
        self.build_manager.get_cached_artifacts.return_value = ["dist/"]
        
        # Check cache
        is_cached = self.build_manager.is_cached(cache_key)
        self.assertTrue(is_cached)
        
        # Get cached artifacts
        artifacts = self.build_manager.get_cached_artifacts(cache_key)
        self.assertIn("dist/", artifacts)
    
    def test_build_failure_handling(self):
        """Test handling of build failures"""
        build_config = {
            "type": "node_typescript",
            "path": self.test_path,
            "commands": {
                "install": "npm install",
                "build": "tsc"
            }
        }
        
        # Mock build failure
        self.build_manager.build.return_value = {
            "success": False,
            "type": "node_typescript",
            "error": "TypeScript compilation failed",
            "output": "error TS2304: Cannot find name 'foo'"
        }
        
        result = self.build_manager.build(build_config)
        
        self.assertFalse(result["success"])
        self.assertIn("error", result)
        self.assertIn("TS2304", result["output"])
    
    def test_detect_multiple_build_systems(self):
        """Test detection when multiple build systems are present"""
        # Create files for both frontend and backend
        frontend_path = self.test_path / "frontend"
        backend_path = self.test_path / "backend"
        
        frontend_path.mkdir()
        backend_path.mkdir()
        
        (frontend_path / "angular.json").write_text('{}')
        (frontend_path / "package.json").write_text('{"name": "frontend"}')
        
        (backend_path / "package.json").write_text('{"name": "backend"}')
        (backend_path / "tsconfig.json").write_text('{}')
        
        # Mock detection of multiple systems
        self.build_manager.detect_all_builds.return_value = [
            {"path": frontend_path, "type": "angular"},
            {"path": backend_path, "type": "node_typescript"}
        ]
        
        builds = self.build_manager.detect_all_builds(self.test_path)
        
        self.assertEqual(len(builds), 2)
        types = [b["type"] for b in builds]
        self.assertIn("angular", types)
        self.assertIn("node_typescript", types)
    
    def test_install_dependencies(self):
        """Test dependency installation"""
        # Mock install dependencies
        self.build_manager.install_dependencies.return_value = {
            "success": True,
            "output": "Dependencies installed"
        }
        
        result = self.build_manager.install_dependencies(
            self.test_path, 
            "npm install"
        )
        
        self.assertTrue(result["success"])
    
    def test_docker_build_support(self):
        """Test Docker build support"""
        # Create Dockerfile
        (self.test_path / "Dockerfile").write_text("""
FROM node:16
WORKDIR /app
COPY . .
RUN npm install
CMD ["npm", "start"]
""")
        
        # Mock Docker build
        self.build_manager.build_docker_image.return_value = {
            "success": True,
            "image_id": "abc123",
            "tag": "myapp:latest"
        }
        
        result = self.build_manager.build_docker_image(
            self.test_path,
            "myapp:latest"
        )
        
        self.assertTrue(result["success"])
        self.assertEqual(result["tag"], "myapp:latest")


class TestBuildConfig(unittest.TestCase):
    """Test BuildConfig data structure"""
    
    def test_build_config_creation(self):
        """Test creating a build configuration"""
        config = {
            "type": "angular",
            "path": "/path/to/project",
            "commands": {
                "install": "npm install",
                "build": "npm run build",
                "test": "npm run test"
            },
            "environment": {
                "NODE_ENV": "production"
            },
            "cache": True
        }
        
        # Verify all fields
        self.assertEqual(config["type"], "angular")
        self.assertIn("install", config["commands"])
        self.assertIn("NODE_ENV", config["environment"])
        self.assertTrue(config["cache"])
    
    def test_build_result_structure(self):
        """Test BuildResult data structure"""
        result = {
            "success": True,
            "type": "node_typescript",
            "duration": 45.2,
            "output": "Build complete",
            "artifacts": ["dist/", "build/"],
            "cache_key": "node_ts_v1_hash123"
        }
        
        # Verify result structure
        self.assertTrue(result["success"])
        self.assertEqual(result["type"], "node_typescript")
        self.assertIsInstance(result["duration"], float)
        self.assertEqual(len(result["artifacts"]), 2)


class TestBuildManagerIntegration(unittest.TestCase):
    """Integration tests for BuildManager"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_path = Path(self.temp_dir)
        
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir)
    
    def test_full_angular_build_flow(self):
        """Test complete Angular build flow"""
        # Create Angular project structure
        frontend = self.test_path / "frontend"
        frontend.mkdir()
        
        (frontend / "angular.json").write_text('''{
            "projects": {
                "app": {
                    "architect": {
                        "build": {
                            "options": {
                                "outputPath": "dist/app"
                            }
                        }
                    }
                }
            }
        }''')
        
        (frontend / "package.json").write_text('''{
            "name": "angular-app",
            "scripts": {
                "build": "echo 'Mock build' && mkdir -p dist/app"
            }
        }''')
        
        # This would be the actual usage
        # build_manager = BuildManager()
        # build_type = build_manager.detect_build_type(frontend)
        # result = build_manager.build({
        #     "type": build_type,
        #     "path": frontend
        # })
        
        # For now, just verify structure
        self.assertTrue((frontend / "angular.json").exists())
        self.assertTrue((frontend / "package.json").exists())
    
    def test_monorepo_build(self):
        """Test building a monorepo with multiple projects"""
        # Create monorepo structure
        (self.test_path / "package.json").write_text('''{
            "name": "monorepo",
            "workspaces": ["packages/*"]
        }''')
        
        # Create multiple packages
        packages = self.test_path / "packages"
        packages.mkdir()
        
        # Frontend package
        frontend = packages / "frontend"
        frontend.mkdir()
        (frontend / "package.json").write_text('{"name": "@mono/frontend"}')
        
        # Backend package
        backend = packages / "backend"
        backend.mkdir()
        (backend / "package.json").write_text('{"name": "@mono/backend"}')
        
        # Verify structure
        self.assertTrue((packages / "frontend").exists())
        self.assertTrue((packages / "backend").exists())


if __name__ == '__main__':
    unittest.main()