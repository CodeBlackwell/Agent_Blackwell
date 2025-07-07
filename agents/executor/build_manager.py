"""
Build Manager for Executor Agent
Handles build detection, execution, and caching for various project types
"""

import os
import subprocess
import json
import hashlib
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import tempfile

from workflows.logger import workflow_logger as logger
from workflows.workflow_config import BUILD_CONFIGS


class BuildResult:
    """Result of a build operation"""
    def __init__(self, 
                 success: bool,
                 build_type: str,
                 output: str = "",
                 error: str = "",
                 artifacts: List[str] = None,
                 duration: float = 0.0,
                 cache_key: str = ""):
        self.success = success
        self.type = build_type
        self.output = output
        self.error = error
        self.artifacts = artifacts or []
        self.duration = duration
        self.cache_key = cache_key
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "success": self.success,
            "type": self.type,
            "output": self.output,
            "error": self.error,
            "artifacts": self.artifacts,
            "duration": self.duration,
            "cache_key": self.cache_key
        }


class BuildConfig:
    """Configuration for a build operation"""
    def __init__(self,
                 build_type: str,
                 path: Path,
                 commands: Dict[str, str] = None,
                 environment: Dict[str, str] = None,
                 cache: bool = True):
        self.type = build_type
        self.path = Path(path)
        self.commands = commands or {}
        self.environment = environment or {}
        self.cache = cache
        
        # Use default commands if not provided
        if not self.commands and build_type in BUILD_CONFIGS:
            self.commands = BUILD_CONFIGS[build_type].copy()


class BuildManager:
    """Manages build operations for different project types"""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize BuildManager
        
        Args:
            cache_dir: Directory for caching build artifacts
        """
        self.cache_dir = cache_dir or Path(tempfile.gettempdir()) / "build_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Build detection patterns
        self.detection_patterns = {
            "angular": ["angular.json"],
            "react": ["package.json", "src/App.js", "src/App.jsx", "src/App.tsx"],
            "vue": ["vue.config.js", "src/App.vue"],
            "node_typescript": ["tsconfig.json", "package.json"],
            "node": ["package.json", "index.js", "server.js"],
            "python": ["requirements.txt", "setup.py", "pyproject.toml"],
            "java": ["pom.xml", "build.gradle"],
            "dotnet": ["*.csproj", "*.sln"]
        }
    
    def detect_build_type(self, project_path: Path) -> Optional[str]:
        """
        Detect the build type for a project
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Build type string or None if not detected
        """
        if not project_path.exists():
            return None
        
        # Check for specific build files
        for build_type, patterns in self.detection_patterns.items():
            for pattern in patterns:
                if pattern.startswith("*"):
                    # Glob pattern
                    if list(project_path.glob(pattern)):
                        return build_type
                else:
                    # Exact file
                    if (project_path / pattern).exists():
                        # Additional checks for specific types
                        if build_type == "angular" and (project_path / "angular.json").exists():
                            return "angular"
                        elif build_type == "react":
                            # Check package.json for React
                            pkg_path = project_path / "package.json"
                            if pkg_path.exists():
                                try:
                                    pkg_data = json.loads(pkg_path.read_text())
                                    deps = pkg_data.get("dependencies", {})
                                    dev_deps = pkg_data.get("devDependencies", {})
                                    if "react" in deps or "react" in dev_deps:
                                        return "react"
                                except:
                                    pass
                        elif build_type == "node_typescript":
                            # Must have both tsconfig and package.json
                            if (project_path / "tsconfig.json").exists() and \
                               (project_path / "package.json").exists():
                                return "node_typescript"
                        elif build_type == "node":
                            # Only return node if not TypeScript
                            if not (project_path / "tsconfig.json").exists():
                                return "node"
                        else:
                            return build_type
        
        # Check for Dockerfile as fallback
        if (project_path / "Dockerfile").exists():
            return "docker"
        
        return None
    
    def detect_all_builds(self, root_path: Path) -> List[Dict]:
        """
        Detect all buildable projects in a directory tree
        
        Args:
            root_path: Root directory to search
            
        Returns:
            List of detected builds with paths and types
        """
        builds = []
        detected_paths = set()
        
        # First check root
        root_type = self.detect_build_type(root_path)
        if root_type:
            builds.append({
                "path": root_path,
                "type": root_type
            })
            detected_paths.add(root_path)
        
        # Then check immediate subdirectories
        for subdir in root_path.iterdir():
            if subdir.is_dir() and not subdir.name.startswith('.'):
                if subdir not in detected_paths:
                    build_type = self.detect_build_type(subdir)
                    if build_type:
                        builds.append({
                            "path": subdir,
                            "type": build_type
                        })
                        detected_paths.add(subdir)
        
        # Check nested directories up to 3 levels
        for level in range(1, 3):
            pattern = "*/" * level
            for path in root_path.glob(pattern):
                if path.is_dir() and not path.name.startswith('.') and path not in detected_paths:
                    # Skip if a parent directory is already detected
                    skip = False
                    for detected in detected_paths:
                        if path != detected and path.is_relative_to(detected):
                            skip = True
                            break
                    
                    if not skip:
                        build_type = self.detect_build_type(path)
                        if build_type:
                            builds.append({
                                "path": path,
                                "type": build_type
                            })
                            detected_paths.add(path)
        
        return builds
    
    def _get_cache_key(self, build_config: BuildConfig) -> str:
        """Generate cache key for build artifacts"""
        # Create hash from relevant files
        hasher = hashlib.md5()
        
        # Hash package files
        package_files = ["package.json", "package-lock.json", "yarn.lock",
                        "requirements.txt", "Pipfile", "Pipfile.lock",
                        "pom.xml", "build.gradle"]
        
        for pkg_file in package_files:
            file_path = build_config.path / pkg_file
            if file_path.exists():
                hasher.update(file_path.read_bytes())
        
        # Hash build configuration files
        config_files = ["tsconfig.json", "angular.json", "webpack.config.js",
                       "vite.config.js", ".babelrc", "setup.py"]
        
        for cfg_file in config_files:
            file_path = build_config.path / cfg_file
            if file_path.exists():
                hasher.update(file_path.read_bytes())
        
        # Include build type
        hasher.update(build_config.type.encode())
        
        return f"{build_config.type}_{hasher.hexdigest()[:12]}"
    
    def is_cached(self, cache_key: str) -> bool:
        """Check if build artifacts are cached"""
        cache_path = self.cache_dir / cache_key
        return cache_path.exists()
    
    def get_cached_artifacts(self, cache_key: str) -> List[str]:
        """Get list of cached artifacts"""
        cache_path = self.cache_dir / cache_key
        if not cache_path.exists():
            return []
        
        # List all files in cache
        artifacts = []
        for item in cache_path.rglob("*"):
            if item.is_file():
                artifacts.append(str(item.relative_to(cache_path)))
        
        return artifacts
    
    def _run_command(self, command: str, cwd: Path, env: Dict[str, str] = None) -> Tuple[bool, str, str]:
        """
        Run a shell command
        
        Returns:
            Tuple of (success, stdout, stderr)
        """
        try:
            # Merge environment variables
            cmd_env = os.environ.copy()
            if env:
                cmd_env.update(env)
            
            logger.info(f"Running command: {command} in {cwd}")
            
            result = subprocess.run(
                command,
                shell=True,
                cwd=str(cwd),
                env=cmd_env,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            success = result.returncode == 0
            return success, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out after 10 minutes"
        except Exception as e:
            return False, "", str(e)
    
    def install_dependencies(self, project_path: Path, install_command: str,
                           env: Dict[str, str] = None) -> Dict:
        """
        Install project dependencies
        
        Args:
            project_path: Path to project
            install_command: Command to run
            env: Environment variables
            
        Returns:
            Result dictionary
        """
        logger.info(f"Installing dependencies for {project_path}")
        
        success, stdout, stderr = self._run_command(install_command, project_path, env)
        
        return {
            "success": success,
            "output": stdout,
            "error": stderr
        }
    
    def build(self, build_config: BuildConfig) -> BuildResult:
        """
        Execute a build
        
        Args:
            build_config: Build configuration
            
        Returns:
            BuildResult object
        """
        start_time = datetime.now()
        
        # Check cache first
        cache_key = ""
        if build_config.cache:
            cache_key = self._get_cache_key(build_config)
            if self.is_cached(cache_key):
                logger.info(f"Using cached build for {cache_key}")
                return BuildResult(
                    success=True,
                    build_type=build_config.type,
                    output="Using cached build",
                    artifacts=self.get_cached_artifacts(cache_key),
                    cache_key=cache_key
                )
        
        # Run install if specified
        if "install" in build_config.commands:
            install_result = self.install_dependencies(
                build_config.path,
                build_config.commands["install"],
                build_config.environment
            )
            if not install_result["success"]:
                return BuildResult(
                    success=False,
                    build_type=build_config.type,
                    error=f"Install failed: {install_result['error']}",
                    output=install_result["output"]
                )
        
        # Run build command
        if "build" in build_config.commands:
            logger.info(f"Building {build_config.type} project at {build_config.path}")
            
            success, stdout, stderr = self._run_command(
                build_config.commands["build"],
                build_config.path,
                build_config.environment
            )
            
            if not success:
                return BuildResult(
                    success=False,
                    build_type=build_config.type,
                    error=stderr or "Build command failed",
                    output=stdout
                )
            
            # Detect artifacts
            artifacts = self._detect_artifacts(build_config)
            
            # Cache artifacts if enabled
            if build_config.cache and artifacts:
                self._cache_artifacts(cache_key, build_config.path, artifacts)
            
            duration = (datetime.now() - start_time).total_seconds()
            
            return BuildResult(
                success=True,
                build_type=build_config.type,
                output=stdout,
                artifacts=artifacts,
                duration=duration,
                cache_key=cache_key
            )
        
        # No build command needed
        return BuildResult(
            success=True,
            build_type=build_config.type,
            output="No build required"
        )
    
    def _detect_artifacts(self, build_config: BuildConfig) -> List[str]:
        """Detect build artifacts based on project type"""
        artifacts = []
        
        # Common artifact directories
        artifact_dirs = {
            "angular": ["dist/", "build/"],
            "react": ["build/", "dist/"],
            "vue": ["dist/"],
            "node_typescript": ["dist/", "build/", "lib/"],
            "node": ["dist/", "build/"],
            "python": ["dist/", "build/", "*.egg-info/"],
            "java": ["target/", "build/"],
            "dotnet": ["bin/", "obj/"]
        }
        
        # Check for artifact directories
        if build_config.type in artifact_dirs:
            for artifact_dir in artifact_dirs[build_config.type]:
                if artifact_dir.endswith("/"):
                    # Directory
                    dir_path = build_config.path / artifact_dir[:-1]
                    if dir_path.exists():
                        artifacts.append(artifact_dir)
                else:
                    # Glob pattern
                    for match in build_config.path.glob(artifact_dir):
                        artifacts.append(str(match.relative_to(build_config.path)))
        
        return artifacts
    
    def _cache_artifacts(self, cache_key: str, project_path: Path, artifacts: List[str]):
        """Cache build artifacts"""
        cache_path = self.cache_dir / cache_key
        cache_path.mkdir(parents=True, exist_ok=True)
        
        for artifact in artifacts:
            src = project_path / artifact
            if src.exists():
                dst = cache_path / artifact
                if src.is_dir():
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                else:
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
        
        logger.info(f"Cached {len(artifacts)} artifacts for {cache_key}")
    
    def build_docker_image(self, project_path: Path, tag: str,
                          dockerfile: str = "Dockerfile") -> Dict:
        """
        Build a Docker image
        
        Args:
            project_path: Path to project
            tag: Docker image tag
            dockerfile: Dockerfile name
            
        Returns:
            Result dictionary
        """
        logger.info(f"Building Docker image {tag} from {project_path}")
        
        command = f"docker build -t {tag} -f {dockerfile} ."
        success, stdout, stderr = self._run_command(command, project_path)
        
        if success:
            # Extract image ID from output
            image_id = ""
            for line in stdout.split('\n'):
                if 'Successfully built' in line:
                    image_id = line.split()[-1]
                    break
            
            return {
                "success": True,
                "image_id": image_id,
                "tag": tag,
                "output": stdout
            }
        else:
            return {
                "success": False,
                "error": stderr,
                "output": stdout
            }
    
    def clean_cache(self, older_than_days: int = 7):
        """Clean old cache entries"""
        import time
        
        now = time.time()
        cutoff = now - (older_than_days * 24 * 60 * 60)
        
        for cache_entry in self.cache_dir.iterdir():
            if cache_entry.is_dir():
                mtime = cache_entry.stat().st_mtime
                if mtime < cutoff:
                    shutil.rmtree(cache_entry)
                    logger.info(f"Removed old cache: {cache_entry.name}")