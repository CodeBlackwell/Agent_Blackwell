"""
Docker Environment Manager

Manages Docker containers for code execution with session-based persistence.
"""

import docker
import hashlib
import asyncio
import re
import shutil
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import aiodocker

# Import GENERATED_CODE_PATH from workflow_config
from workflows.workflow_config import GENERATED_CODE_PATH

@dataclass
class EnvironmentSpec:
    """Specification for a Docker environment"""
    language: str
    version: str
    base_image: str
    dependencies: List[str]
    system_packages: List[str]
    build_commands: List[str]
    execution_commands: List[str]
    working_dir: str = "/app"

class DockerEnvironmentManager:
    """Manages Docker environments for code execution"""
    
    # Container registry to track active containers
    _container_registry = {}  # session_id -> container_info
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.docker_client = None
        self.async_docker = None
        
    async def initialize(self):
        """Initialize Docker clients"""
        try:
            self.docker_client = docker.from_env()
            # Test connection
            self.docker_client.ping()
            print("✅ Docker connection established")
        except Exception as e:
            raise RuntimeError(f"Failed to connect to Docker: {e}")
    
    async def get_or_create_environment(self, 
                                      env_spec: EnvironmentSpec, 
                                      code_content: str) -> Dict:
        """Get existing container or create new one"""
        # Generate environment hash
        env_hash = self._generate_environment_hash(env_spec)
        container_key = f"{self.session_id}_{env_hash}"
        
        # Check if container already exists
        existing_container = await self._find_existing_container(container_key)
        if existing_container:
            print(f"♻️  Reusing existing container: {existing_container['container_id'][:12]}")
            return existing_container
        
        # Build new container
        print(f"🔨 Building new container for session: {self.session_id}")
        container_info = await self._build_container(env_spec, code_content, container_key)
        
        # Store in registry
        self._container_registry[container_key] = container_info
        
        return container_info
    
    async def _find_existing_container(self, container_key: str) -> Optional[Dict]:
        """Find existing container by key"""
        # Check registry first
        if container_key in self._container_registry:
            container_info = self._container_registry[container_key]
            try:
                # Verify container still exists and is running
                container = self.docker_client.containers.get(container_info['container_id'])
                if container.status == 'running':
                    return container_info
            except docker.errors.NotFound:
                # Container was removed, clean up registry
                del self._container_registry[container_key]
        
        # Check by label
        try:
            containers = self.docker_client.containers.list(
                filters={
                    "label": [
                        f"session_id={self.session_id}",
                        "executor=true"
                    ]
                }
            )
            for container in containers:
                if container.labels.get('container_key') == container_key:
                    return {
                        "container_id": container.id,
                        "container_name": container.name,
                        "status": container.status
                    }
        except Exception:
            pass
        
        return None
    
    async def _build_container(self, env_spec: EnvironmentSpec, 
                              code_content: str, container_key: str) -> Dict:
        """Build a new Docker container"""
        # Create build context in the GENERATED_CODE_PATH directory
        # Create a session-specific directory structure
        generated_path = Path(GENERATED_CODE_PATH)
        generated_path.mkdir(parents=True, exist_ok=True)
        
        # Create a unique directory for this session and build
        build_path = generated_path / f"{self.session_id}_{container_key}"
        # Remove directory if it already exists (to avoid conflicts)
        if build_path.exists():
            shutil.rmtree(build_path)
        build_path.mkdir(parents=True)
        
        try:
            # Create Dockerfile
            dockerfile_content = self._generate_dockerfile(env_spec)
            dockerfile_path = build_path / "Dockerfile"
            dockerfile_path.write_text(dockerfile_content)
            
            # Write code files
            code_files = self._parse_code_files(code_content)
            for file_info in code_files:
                file_path = build_path / file_info['filename']
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(file_info['content'])
            
            # Write dependency files if needed
            self._write_dependency_files(build_path, env_spec, code_files)
            
            # Build image
            image_tag = f"executor_{container_key}:latest"
            print(f"🏗️  Building Docker image: {image_tag}")
            
            try:
                image, build_logs = self.docker_client.images.build(
                    path=str(build_path),
                    tag=image_tag,
                    rm=True,
                    forcerm=True,
                    pull=True  # Always pull base image for security
                )
                
                # Print build logs for debugging
                for log in build_logs:
                    if 'stream' in log:
                        print(f"   {log['stream'].strip()}")
                
            except docker.errors.BuildError as e:
                raise RuntimeError(f"Failed to build Docker image: {e}")
            
            # Create and start container
            container_name = f"executor_{container_key}"
            print(f"🚀 Starting container: {container_name}")
            
            container = self.docker_client.containers.run(
                image_tag,
                detach=True,
                remove=False,
                name=container_name,
                working_dir=env_spec.working_dir,
                labels={
                    "session_id": self.session_id,
                    "env_hash": self._generate_environment_hash(env_spec),
                    "container_key": container_key,
                    "executor": "true",
                    "build_path": str(build_path)  # Store build path in container label
                },
                # Resource limits
                mem_limit="512m",
                cpu_quota=50000,  # 50% CPU
                network_mode="none",  # No network for security
                # Keep container running
                command="tail -f /dev/null"
            )
            
            return {
                "container_id": container.id,
                "container_name": container.name,
                "image_tag": image_tag,
                "build_path": str(build_path),  # Return build path for reference
                "status": "running"
            }
        except Exception as e:
            # Clean up the directory if build fails
            if build_path.exists():
                shutil.rmtree(build_path)
            raise e
    
    def _generate_dockerfile(self, env_spec: EnvironmentSpec) -> str:
        """Generate minimal Dockerfile based on requirements"""
        dockerfile = [f"FROM {env_spec.base_image}"]
        
        # Set working directory
        dockerfile.append(f"WORKDIR {env_spec.working_dir}")
        
        # Install system packages if needed
        if env_spec.system_packages:
            if "alpine" in env_spec.base_image:
                dockerfile.append(f"RUN apk add --no-cache {' '.join(env_spec.system_packages)}")
            elif "ubuntu" in env_spec.base_image or "debian" in env_spec.base_image:
                dockerfile.append("RUN apt-get update && apt-get install -y " + 
                                " ".join(env_spec.system_packages) + 
                                " && rm -rf /var/lib/apt/lists/*")
        
        # Language-specific setup
        if env_spec.language == "python":
            # Copy requirements first for better caching
            dockerfile.append("COPY requirements.txt* ./")
            dockerfile.append("RUN pip install --no-cache-dir -r requirements.txt || echo 'No requirements.txt'")
        elif env_spec.language == "nodejs":
            # Copy package files first for better caching
            dockerfile.append("COPY package*.json ./")
            dockerfile.append("RUN npm ci --only=production || npm install || echo 'No package.json'")
        
        # Copy application code
        dockerfile.append("COPY . .")
        
        # Run any build commands
        for cmd in env_spec.build_commands:
            dockerfile.append(f"RUN {cmd}")
        
        # Keep container running
        dockerfile.append('CMD ["tail", "-f", "/dev/null"]')
        
        return "\n".join(dockerfile)
    
    def _parse_code_files(self, code_content: str) -> List[Dict[str, str]]:
        """Parse code files from input"""
        files = []
        
        # Look for FILENAME: pattern
        filename_pattern = r'FILENAME:\s*(.+?)\n```(?:\w*)\n(.*?)\n```'
        matches = re.findall(filename_pattern, code_content, re.DOTALL)
        
        for filename, content in matches:
            files.append({
                'filename': filename.strip(),
                'content': content.strip()
            })
        
        return files
    
    def _write_dependency_files(self, build_path: Path, env_spec: EnvironmentSpec, code_files: List[Dict[str, str]]) -> None:
        """Write dependency files based on language"""
        if env_spec.language == "python":
            req_path = build_path / "requirements.txt"
            if env_spec.dependencies:
                req_path.write_text("\n".join(env_spec.dependencies))
            else:
                # Create empty requirements.txt file to satisfy Dockerfile COPY command
                req_path.write_text("# No dependencies specified")
        elif env_spec.language == "nodejs" and env_spec.dependencies:
            pkg_path = build_path / "package.json"
            pkg_data = {
                "name": "code-execution",
                "version": "1.0.0",
                "private": True,
                "dependencies": {}
            }
            for dep in env_spec.dependencies:
                if ">" in dep or "=" in dep:
                    # Handle version specification
                    parts = re.split(r"[>=<~^]", dep, 1)
                    name = parts[0].strip()
                    version = dep[len(name):].strip()
                    pkg_data["dependencies"][name] = version
                else:
                    pkg_data["dependencies"][dep] = "*"
                    
            pkg_path.write_text(json.dumps(pkg_data, indent=2))
    
    async def execute_in_container(self, container_id: str, 
                                  commands: List[str]) -> Dict:
        """Execute commands in running container"""
        try:
            container = self.docker_client.containers.get(container_id)
        except docker.errors.NotFound:
            raise RuntimeError(f"Container {container_id[:12]} not found")
        
        results = []
        overall_success = True
        
        for command in commands:
            print(f"▶️  Executing: {command}")
            
            try:
                # Execute command with timeout
                exec_result = container.exec_run(
                    command,
                    stdout=True,
                    stderr=True,
                    stream=False,
                    demux=True,
                    workdir="/app"
                )
                
                stdout, stderr = exec_result.output or (b'', b'')
                
                result = {
                    "command": command,
                    "exit_code": exec_result.exit_code,
                    "stdout": stdout.decode('utf-8', errors='ignore') if stdout else "",
                    "stderr": stderr.decode('utf-8', errors='ignore') if stderr else "",
                    "success": exec_result.exit_code == 0
                }
                
                results.append(result)
                
                if not result["success"]:
                    overall_success = False
                    # Don't continue if a command fails
                    if "test" not in command.lower():  # Unless it's a test command
                        break
                        
            except Exception as e:
                result = {
                    "command": command,
                    "exit_code": -1,
                    "stdout": "",
                    "stderr": str(e),
                    "success": False
                }
                results.append(result)
                overall_success = False
        
        return {
            "container_id": container_id,
            "executions": results,
            "overall_success": overall_success
        }
    
    async def cleanup_session(self, session_id: str):
        """Clean up all containers for a session"""
        print(f"🧹 Cleaning up containers for session: {session_id}")
        
        containers = self.docker_client.containers.list(
            all=True,
            filters={"label": f"session_id={session_id}"}
        )
        
        for container in containers:
            try:
                print(f"   Stopping container: {container.name}")
                container.stop(timeout=5)
                container.remove()
            except Exception as e:
                print(f"   Warning: Failed to clean up {container.name}: {e}")
        
        # Clean up images
        images = self.docker_client.images.list(
            name=f"executor_{session_id}"
        )
        for image in images:
            try:
                self.docker_client.images.remove(image.id, force=True)
            except Exception:
                pass
    
    def _generate_environment_hash(self, env_spec: EnvironmentSpec) -> str:
        """Generate hash of environment specification"""
        spec_str = f"{env_spec.language}:{env_spec.version}:{env_spec.base_image}"
        spec_str += ":".join(sorted(env_spec.dependencies))
        spec_str += ":".join(sorted(env_spec.system_packages))
        return hashlib.md5(spec_str.encode()).hexdigest()[:8]

    @classmethod
    async def cleanup_all_sessions(cls):
        """Clean up all executor containers (maintenance function)"""
        try:
            client = docker.from_env()
            containers = client.containers.list(
                all=True,
                filters={"label": "executor=true"}
            )
            
            for container in containers:
                try:
                    container.stop(timeout=5)
                    container.remove()
                    print(f"Cleaned up: {container.name}")
                except Exception:
                    pass
                    
        except Exception as e:
            print(f"Cleanup error: {e}")
