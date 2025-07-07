"""
Integration tests for BuildManager with real functionality
"""

import unittest
import tempfile
import shutil
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.executor.build_manager import BuildManager, BuildConfig, BuildResult


class TestBuildManagerIntegration(unittest.TestCase):
    """Integration tests for BuildManager"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_path = Path(self.temp_dir)
        self.build_manager = BuildManager(cache_dir=self.test_path / "cache")
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir)
    
    def test_detect_angular_project_real(self):
        """Test real Angular project detection"""
        # Create Angular project structure
        (self.test_path / "angular.json").write_text('''{
            "version": 1,
            "projects": {
                "app": {
                    "projectType": "application",
                    "root": "",
                    "sourceRoot": "src"
                }
            }
        }''')
        
        (self.test_path / "package.json").write_text('''{
            "name": "angular-app",
            "dependencies": {
                "@angular/core": "^15.0.0"
            }
        }''')
        
        # Test detection
        build_type = self.build_manager.detect_build_type(self.test_path)
        self.assertEqual(build_type, "angular")
    
    def test_detect_node_typescript_real(self):
        """Test real Node TypeScript detection"""
        # Create TypeScript project
        (self.test_path / "tsconfig.json").write_text('''{
            "compilerOptions": {
                "target": "ES2020",
                "module": "commonjs",
                "outDir": "./dist"
            }
        }''')
        
        (self.test_path / "package.json").write_text('''{
            "name": "ts-app",
            "scripts": {
                "build": "tsc"
            }
        }''')
        
        build_type = self.build_manager.detect_build_type(self.test_path)
        self.assertEqual(build_type, "node_typescript")
    
    def test_detect_react_project(self):
        """Test React project detection"""
        (self.test_path / "package.json").write_text('''{
            "name": "react-app",
            "dependencies": {
                "react": "^18.0.0",
                "react-dom": "^18.0.0"
            }
        }''')
        
        # Create React app structure
        src_dir = self.test_path / "src"
        src_dir.mkdir()
        (src_dir / "App.jsx").write_text("export default function App() {}")
        
        build_type = self.build_manager.detect_build_type(self.test_path)
        self.assertEqual(build_type, "react")
    
    def test_detect_python_project(self):
        """Test Python project detection"""
        (self.test_path / "requirements.txt").write_text("flask==2.0.0\npytest==7.0.0")
        (self.test_path / "main.py").write_text("print('Hello')")
        
        build_type = self.build_manager.detect_build_type(self.test_path)
        self.assertEqual(build_type, "python")
    
    def test_detect_all_builds_monorepo(self):
        """Test detecting all builds in a monorepo"""
        # Create monorepo structure
        backend = self.test_path / "backend"
        frontend = self.test_path / "frontend"
        
        backend.mkdir()
        frontend.mkdir()
        
        # Backend - TypeScript
        (backend / "tsconfig.json").write_text('{}')
        (backend / "package.json").write_text('{"name": "backend"}')
        
        # Frontend - Angular
        (frontend / "angular.json").write_text('{"projects": {}}')
        (frontend / "package.json").write_text('{"name": "frontend"}')
        
        # Root package.json
        (self.test_path / "package.json").write_text('''{
            "name": "monorepo",
            "workspaces": ["backend", "frontend"]
        }''')
        
        # Detect all builds
        builds = self.build_manager.detect_all_builds(self.test_path)
        
        # Should find 3 builds: root (node), backend (node_typescript), frontend (angular)
        self.assertEqual(len(builds), 3)
        
        # Check types
        build_types = {str(b["path"].relative_to(self.test_path)): b["type"] for b in builds}
        self.assertEqual(build_types.get("backend"), "node_typescript")
        self.assertEqual(build_types.get("frontend"), "angular")
        self.assertEqual(build_types.get("."), "node")
    
    def test_build_simple_project(self):
        """Test building a simple Node.js project"""
        # Create simple project
        (self.test_path / "package.json").write_text('''{
            "name": "simple-app",
            "scripts": {
                "build": "echo 'Building...' && mkdir -p dist && echo 'module.exports = {};' > dist/index.js"
            }
        }''')
        
        (self.test_path / "index.js").write_text("console.log('Hello');")
        
        # Create build config
        config = BuildConfig(
            build_type="node",
            path=self.test_path,
            commands={
                "build": "npm run build"
            }
        )
        
        # Execute build
        result = self.build_manager.build(config)
        
        # Check result
        self.assertTrue(result.success)
        self.assertEqual(result.type, "node")
        self.assertIn("Building...", result.output)
        self.assertIn("dist/", result.artifacts)
        
        # Verify artifact was created
        self.assertTrue((self.test_path / "dist" / "index.js").exists())
    
    def test_build_with_install(self):
        """Test building with dependency installation"""
        # Create project that needs install
        (self.test_path / "package.json").write_text('''{
            "name": "app-with-deps",
            "scripts": {
                "build": "echo 'Built successfully'"
            },
            "dependencies": {}
        }''')
        
        config = BuildConfig(
            build_type="node",
            path=self.test_path,
            commands={
                "install": "echo 'Mock npm install'",
                "build": "npm run build"
            }
        )
        
        result = self.build_manager.build(config)
        
        self.assertTrue(result.success)
        self.assertIn("Built successfully", result.output)
    
    def test_cache_functionality(self):
        """Test build caching"""
        # Create project
        (self.test_path / "package.json").write_text('''{
            "name": "cached-app",
            "scripts": {
                "build": "mkdir -p dist && echo 'Built at' > dist/build.txt"
            }
        }''')
        
        config = BuildConfig(
            build_type="node",
            path=self.test_path,
            commands={"build": "npm run build"},
            cache=True
        )
        
        # First build
        result1 = self.build_manager.build(config)
        self.assertTrue(result1.success)
        self.assertNotEqual(result1.cache_key, "")
        
        # Second build should use cache
        result2 = self.build_manager.build(config)
        self.assertTrue(result2.success)
        self.assertEqual(result2.cache_key, result1.cache_key)
        self.assertIn("cached", result2.output.lower())
    
    def test_build_failure(self):
        """Test handling of build failures"""
        # Create project with failing build
        (self.test_path / "package.json").write_text('''{
            "name": "failing-app",
            "scripts": {
                "build": "exit 1"
            }
        }''')
        
        config = BuildConfig(
            build_type="node",
            path=self.test_path,
            commands={"build": "npm run build"}
        )
        
        result = self.build_manager.build(config)
        
        self.assertFalse(result.success)
        self.assertEqual(result.type, "node")
        self.assertNotEqual(result.error, "")
    
    def test_docker_detection(self):
        """Test Docker project detection"""
        (self.test_path / "Dockerfile").write_text("""
FROM node:16
WORKDIR /app
COPY . .
RUN npm install
CMD ["npm", "start"]
""")
        
        build_type = self.build_manager.detect_build_type(self.test_path)
        self.assertEqual(build_type, "docker")
    
    def test_environment_variables(self):
        """Test building with environment variables"""
        (self.test_path / "package.json").write_text('''{
            "name": "env-app",
            "scripts": {
                "build": "echo Build mode: $BUILD_MODE"
            }
        }''')
        
        config = BuildConfig(
            build_type="node",
            path=self.test_path,
            commands={"build": "npm run build"},
            environment={"BUILD_MODE": "production"}
        )
        
        result = self.build_manager.build(config)
        
        self.assertTrue(result.success)
        self.assertIn("Build mode: production", result.output)
    
    def test_artifact_detection(self):
        """Test automatic artifact detection"""
        # Create TypeScript project
        (self.test_path / "tsconfig.json").write_text('''{
            "compilerOptions": {
                "outDir": "./dist"
            }
        }''')
        
        (self.test_path / "package.json").write_text('''{
            "name": "ts-artifacts",
            "scripts": {
                "build": "mkdir -p dist && echo 'export {};' > dist/index.js"
            }
        }''')
        
        config = BuildConfig(
            build_type="node_typescript",
            path=self.test_path,
            commands={"build": "npm run build"}
        )
        
        result = self.build_manager.build(config)
        
        self.assertTrue(result.success)
        self.assertIn("dist/", result.artifacts)
        self.assertTrue((self.test_path / "dist").exists())


if __name__ == '__main__':
    unittest.main()