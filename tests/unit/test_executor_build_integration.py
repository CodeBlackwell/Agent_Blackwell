"""
Unit tests for executor agent integration with BuildManager
Tests the integration of build detection and execution before container creation
"""

import unittest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from pathlib import Path
import tempfile
import shutil
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.executor.build_manager import BuildManager, BuildConfig, BuildResult
from agents.executor.docker_manager import DockerEnvironmentManager
from agents.executor.environment_spec import EnvironmentSpec


class TestExecutorBuildIntegration(unittest.TestCase):
    """Test executor integration with BuildManager"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_path = Path(self.temp_dir)
        self.build_manager = BuildManager(cache_dir=self.test_path / "cache")
        self.session_id = "test_session_123"
        
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir)
    
    def test_detect_build_before_docker(self):
        """Test that builds are detected before Docker container creation"""
        # Create a TypeScript project
        (self.test_path / "tsconfig.json").write_text('{"compilerOptions": {"outDir": "./dist"}}')
        (self.test_path / "package.json").write_text('{"name": "test-app", "scripts": {"build": "tsc"}}')
        (self.test_path / "src").mkdir()
        (self.test_path / "src" / "index.ts").write_text("console.log('Hello');")
        
        # Detect build type
        build_type = self.build_manager.detect_build_type(self.test_path)
        self.assertEqual(build_type, "node_typescript")
        
        # Create build config
        config = BuildConfig(
            build_type=build_type,
            path=self.test_path,
            commands={"install": "npm install", "build": "npm run build"}
        )
        
        # Verify build config has correct commands
        self.assertIn("install", config.commands)
        self.assertIn("build", config.commands)
    
    @patch('agents.executor.docker_manager.docker')
    def test_build_execution_before_container(self, mock_docker):
        """Test that builds are executed before creating Docker container"""
        # Create a simple Node.js project
        (self.test_path / "package.json").write_text('''{
            "name": "test-app",
            "scripts": {
                "build": "echo 'Building...' && mkdir -p dist && echo 'export {};' > dist/index.js"
            }
        }''')
        
        # Execute build
        config = BuildConfig(
            build_type="node",
            path=self.test_path,
            commands={"build": "npm run build"}
        )
        
        # Mock successful build
        with patch.object(self.build_manager, '_run_command') as mock_run:
            mock_run.return_value = (True, "Building...\n", "")
            
            result = self.build_manager.build(config)
            
            self.assertTrue(result.success)
            self.assertEqual(result.type, "node")
            mock_run.assert_called_once()
            
            # Verify build command was executed
            call_args = mock_run.call_args
            self.assertIn("npm run build", call_args[0][0])
    
    def test_build_artifacts_copied_to_container(self):
        """Test that build artifacts are included in container context"""
        # Create project with build artifacts
        (self.test_path / "dist").mkdir()
        (self.test_path / "dist" / "app.js").write_text("console.log('Built app');")
        
        # Mock DockerEnvironmentManager
        docker_manager = Mock(spec=DockerEnvironmentManager)
        
        # Test artifact detection
        artifacts = self.build_manager._detect_artifacts(
            BuildConfig("node", self.test_path)
        )
        
        self.assertIn("dist/", artifacts)
    
    def test_failed_build_prevents_container_creation(self):
        """Test that failed builds prevent container creation"""
        config = BuildConfig(
            build_type="node_typescript",
            path=self.test_path,
            commands={"build": "tsc --noEmit"}
        )
        
        # Mock failed build
        with patch.object(self.build_manager, '_run_command') as mock_run:
            mock_run.return_value = (False, "", "error TS2304: Cannot find name 'foo'")
            
            result = self.build_manager.build(config)
            
            self.assertFalse(result.success)
            self.assertIn("Cannot find name", result.error)
    
    def test_multi_project_build_support(self):
        """Test building multiple projects in a monorepo"""
        # Create monorepo structure
        backend = self.test_path / "backend"
        frontend = self.test_path / "frontend"
        
        backend.mkdir()
        frontend.mkdir()
        
        # Backend - Node.js
        (backend / "package.json").write_text('{"name": "backend", "scripts": {"build": "echo Backend built"}}')
        
        # Frontend - Angular
        (frontend / "angular.json").write_text('{"projects": {}}')
        (frontend / "package.json").write_text('{"name": "frontend", "scripts": {"build": "echo Frontend built"}}')
        
        # Detect all builds
        builds = self.build_manager.detect_all_builds(self.test_path)
        
        # Should find both projects
        self.assertEqual(len(builds), 2)
        
        # Test building each
        for build_info in builds:
            # Use BUILD_CONFIGS from workflow_config
            from workflows.workflow_config import BUILD_CONFIGS
            
            config = BuildConfig(
                build_type=build_info["type"],
                path=build_info["path"],
                commands=BUILD_CONFIGS.get(build_info["type"], {})
            )
            
            # Mock build execution
            with patch.object(self.build_manager, '_run_command') as mock_run:
                project_name = build_info["path"].name
                mock_run.return_value = (True, f"{project_name} built", "")
                
                result = self.build_manager.build(config)
                
                self.assertTrue(result.success)
                # Check that result has the expected output
                if "build" in config.commands:
                    self.assertIn(project_name, result.output)
                else:
                    # If no build command, should get "No build required"
                    self.assertEqual(result.output, "No build required")
    
    @patch('subprocess.run')
    def test_environment_variables_in_build(self, mock_run):
        """Test that environment variables are passed to build commands"""
        config = BuildConfig(
            build_type="node",
            path=self.test_path,
            commands={"build": "npm run build"},
            environment={"NODE_ENV": "production", "API_URL": "https://api.example.com"}
        )
        
        # Mock subprocess
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Build complete",
            stderr=""
        )
        
        # Execute build
        result = self.build_manager.build(config)
        
        # Verify environment variables were passed
        call_args = mock_run.call_args
        env = call_args.kwargs.get('env', {})
        
        self.assertIn("NODE_ENV", env)
        self.assertEqual(env["NODE_ENV"], "production")
        self.assertIn("API_URL", env)
    
    def test_build_cache_integration(self):
        """Test that build cache works with executor"""
        # Create project
        (self.test_path / "package.json").write_text('{"name": "cached-app", "scripts": {"build": "echo Built"}}')
        
        config = BuildConfig(
            build_type="node",
            path=self.test_path,
            commands={"build": "echo 'Building...'"},
            cache=True
        )
        
        # First build
        with patch.object(self.build_manager, '_run_command') as mock_run:
            mock_run.return_value = (True, "Building...", "")
            
            # Also mock artifact detection
            with patch.object(self.build_manager, '_detect_artifacts') as mock_artifacts:
                mock_artifacts.return_value = ["dist/"]
                
                result1 = self.build_manager.build(config)
                
                self.assertTrue(result1.success)
                self.assertNotEqual(result1.cache_key, "")
                
                # Verify build was executed
                self.assertEqual(mock_run.call_count, 1)
        
        # Second build should use cache
        result2 = self.build_manager.build(config)
        
        self.assertTrue(result2.success)
        self.assertEqual(result2.cache_key, result1.cache_key)
        self.assertIn("cached", result2.output.lower())
    
    def test_build_manager_in_executor_workflow(self):
        """Test complete workflow: detect -> build -> containerize"""
        # Create Angular project
        (self.test_path / "angular.json").write_text('{"projects": {"app": {}}}')
        (self.test_path / "package.json").write_text('''{
            "name": "angular-app",
            "scripts": {
                "build": "echo 'Angular build complete' && mkdir -p dist/app"
            }
        }''')
        
        # Step 1: Detect build type
        build_type = self.build_manager.detect_build_type(self.test_path)
        self.assertEqual(build_type, "angular")
        
        # Step 2: Create build configuration
        config = BuildConfig(
            build_type=build_type,
            path=self.test_path,
            commands={"build": "npm run build"}
        )
        
        # Step 3: Execute build
        with patch.object(self.build_manager, '_run_command') as mock_run:
            mock_run.return_value = (True, "Angular build complete", "")
            
            # Mock artifact detection for Angular
            with patch.object(self.build_manager, '_detect_artifacts') as mock_artifacts:
                mock_artifacts.return_value = ["dist/"]
                
                result = self.build_manager.build(config)
                
                self.assertTrue(result.success)
                self.assertIn("dist/", result.artifacts)
        
        # Step 4: Pass artifacts to Docker (simulated)
        # In real implementation, executor would:
        # 1. Copy build artifacts to Docker context
        # 2. Skip build steps in Dockerfile since already built
        # 3. Just copy pre-built artifacts
        
        self.assertTrue(len(result.artifacts) > 0)
        
    async def test_async_build_execution(self):
        """Test async execution of builds"""
        # Create async wrapper for build
        async def async_build(config):
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self.build_manager.build, config)
        
        config = BuildConfig(
            build_type="node",
            path=self.test_path,
            commands={"build": "echo 'Async build'"}
        )
        
        with patch.object(self.build_manager, '_run_command') as mock_run:
            mock_run.return_value = (True, "Async build", "")
            
            # Run async build
            result = await async_build(config)
            
            self.assertTrue(result.success)
            self.assertEqual(result.output, "Async build")


class TestDockerManagerBuildIntegration(unittest.TestCase):
    """Test DockerEnvironmentManager integration with builds"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_path = Path(self.temp_dir)
        self.session_id = "test_build_session"
        
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir)
    
    @patch('agents.executor.docker_manager.docker')
    async def test_docker_manager_uses_prebuilt_artifacts(self, mock_docker):
        """Test that DockerEnvironmentManager can use pre-built artifacts"""
        # Create mock environment spec
        env_spec = EnvironmentSpec(
            language="nodejs",
            version="16",
            base_image="node:16-alpine",
            dependencies=["express"],
            system_packages=[],
            build_commands=[],  # No build commands since we pre-built
            execution_commands=["node dist/index.js"],
            working_dir="/app"
        )
        
        # Create pre-built artifacts
        dist_path = self.test_path / "dist"
        dist_path.mkdir()
        (dist_path / "index.js").write_text("console.log('Pre-built app');")
        
        # Mock Docker client
        mock_docker.from_env.return_value = MagicMock()
        
        # Test that Dockerfile generation skips build steps
        docker_manager = DockerEnvironmentManager(self.session_id)
        dockerfile = docker_manager._generate_dockerfile(env_spec)
        
        # Should not contain build commands
        self.assertNotIn("RUN npm run build", dockerfile)
        self.assertNotIn("RUN tsc", dockerfile)
        
        # Should copy all files including dist
        self.assertIn("COPY . .", dockerfile)


# Run async tests
def run_async_test(coro):
    """Helper to run async tests"""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


if __name__ == '__main__':
    # Patch async test methods for both test classes
    for test_class in [TestExecutorBuildIntegration, TestDockerManagerBuildIntegration]:
        for attr_name in dir(test_class):
            attr = getattr(test_class, attr_name)
            if asyncio.iscoroutinefunction(attr):
                setattr(test_class, attr_name, 
                       lambda self, coro=attr: run_async_test(coro(self)))
    
    unittest.main()