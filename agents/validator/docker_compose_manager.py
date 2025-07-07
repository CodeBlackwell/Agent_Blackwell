"""
Docker Compose Manager for Multi-Container Orchestration
Handles parsing, validation, and orchestration of docker-compose.yml files
"""

import os
import yaml
import docker
import time
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from collections import defaultdict
import networkx as nx

from workflows.logger import workflow_logger as logger


@dataclass
class ServiceDefinition:
    """Represents a single service from docker-compose.yml"""
    name: str
    image: Optional[str] = None
    build: Optional[Dict[str, Any]] = None
    ports: List[str] = None
    environment: Dict[str, str] = None
    volumes: List[str] = None
    depends_on: List[str] = None
    networks: List[str] = None
    command: Optional[str] = None
    healthcheck: Optional[Dict[str, Any]] = None
    restart: str = "no"
    labels: Dict[str, str] = None
    
    def __post_init__(self):
        self.ports = self.ports or []
        self.environment = self.environment or {}
        self.volumes = self.volumes or []
        self.depends_on = self.depends_on or []
        self.networks = self.networks or []
        self.labels = self.labels or {}


@dataclass
class ComposeConfig:
    """Represents parsed docker-compose configuration"""
    version: str
    services: Dict[str, ServiceDefinition]
    networks: Dict[str, Dict] = None
    volumes: Dict[str, Dict] = None
    
    def __post_init__(self):
        self.networks = self.networks or {}
        self.volumes = self.volumes or {}


class DockerComposeManager:
    """Manages multi-container orchestration using docker-compose concepts"""
    
    def __init__(self, session_id: str, project_name: Optional[str] = None):
        """
        Initialize DockerComposeManager
        
        Args:
            session_id: Unique session identifier
            project_name: Optional project name (defaults to session_id)
        """
        self.session_id = session_id
        self.project_name = project_name or f"validator_{session_id}"
        self.client = docker.from_env()
        self.containers: Dict[str, Any] = {}
        self.networks: Dict[str, Any] = {}
        self.compose_config: Optional[ComposeConfig] = None
        
        # Default labels for tracking
        self.default_labels = {
            "validator": "true",
            "session_id": session_id,
            "project": self.project_name,
            "manager": "compose"
        }
    
    def parse_compose_file(self, compose_path: Path) -> ComposeConfig:
        """
        Parse and validate docker-compose.yml file
        
        Args:
            compose_path: Path to docker-compose.yml
            
        Returns:
            ComposeConfig object
            
        Raises:
            ValueError: If compose file is invalid
        """
        logger.info(f"Parsing compose file: {compose_path}")
        
        if not compose_path.exists():
            raise ValueError(f"Compose file not found: {compose_path}")
        
        try:
            with open(compose_path, 'r') as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML syntax: {e}")
        
        # Validate basic structure
        if not isinstance(data, dict):
            raise ValueError("Compose file must be a YAML dictionary")
        
        if 'services' not in data:
            raise ValueError("Compose file must contain 'services' section")
        
        # Parse version
        version = str(data.get('version', '3'))
        
        # Parse services
        services = {}
        for name, config in data.get('services', {}).items():
            if not isinstance(config, dict):
                raise ValueError(f"Service '{name}' must be a dictionary")
            
            # Parse service definition
            service = ServiceDefinition(
                name=name,
                image=config.get('image'),
                build=self._parse_build_config(config.get('build')),
                ports=config.get('ports', []),
                environment=self._parse_environment(config.get('environment')),
                volumes=config.get('volumes', []),
                depends_on=self._parse_depends_on(config.get('depends_on')),
                networks=config.get('networks', []),
                command=config.get('command'),
                healthcheck=config.get('healthcheck'),
                restart=config.get('restart', 'no'),
                labels=config.get('labels', {})
            )
            
            # Validate service has either image or build
            if not service.image and not service.build:
                raise ValueError(f"Service '{name}' must specify either 'image' or 'build'")
            
            services[name] = service
        
        # Parse networks and volumes
        networks = data.get('networks', {})
        volumes = data.get('volumes', {})
        
        self.compose_config = ComposeConfig(
            version=version,
            services=services,
            networks=networks,
            volumes=volumes
        )
        
        logger.info(f"Successfully parsed {len(services)} services")
        return self.compose_config
    
    def _parse_build_config(self, build_config: Any) -> Optional[Dict[str, Any]]:
        """Parse build configuration"""
        if build_config is None:
            return None
        
        if isinstance(build_config, str):
            # Simple build path
            return {"context": build_config}
        elif isinstance(build_config, dict):
            return build_config
        else:
            raise ValueError("Build config must be string or dictionary")
    
    def _parse_environment(self, env_config: Any) -> Dict[str, str]:
        """Parse environment variables"""
        if env_config is None:
            return {}
        
        if isinstance(env_config, dict):
            # Dictionary format
            return {k: str(v) for k, v in env_config.items()}
        elif isinstance(env_config, list):
            # List format (KEY=VALUE)
            env_dict = {}
            for item in env_config:
                if '=' in item:
                    key, value = item.split('=', 1)
                    env_dict[key] = value
                else:
                    # Environment variable from host
                    env_dict[item] = os.environ.get(item, '')
            return env_dict
        else:
            raise ValueError("Environment must be dictionary or list")
    
    def _parse_depends_on(self, depends_config: Any) -> List[str]:
        """Parse service dependencies"""
        if depends_config is None:
            return []
        
        if isinstance(depends_config, list):
            return depends_config
        elif isinstance(depends_config, dict):
            # Extended format with conditions
            return list(depends_config.keys())
        else:
            raise ValueError("depends_on must be list or dictionary")
    
    def _resolve_dependency_order(self) -> List[str]:
        """
        Resolve service startup order based on dependencies
        
        Returns:
            List of service names in startup order
        """
        if not self.compose_config:
            return []
        
        # Build dependency graph
        graph = nx.DiGraph()
        
        for name, service in self.compose_config.services.items():
            graph.add_node(name)
            for dep in service.depends_on:
                if dep in self.compose_config.services:
                    graph.add_edge(dep, name)
                else:
                    logger.warning(f"Service '{name}' depends on unknown service '{dep}'")
        
        # Check for cycles
        if not nx.is_directed_acyclic_graph(graph):
            cycles = list(nx.simple_cycles(graph))
            raise ValueError(f"Circular dependencies detected: {cycles}")
        
        # Topological sort for startup order
        try:
            order = list(nx.topological_sort(graph))
            logger.info(f"Service startup order: {order}")
            return order
        except nx.NetworkXError as e:
            raise ValueError(f"Failed to resolve dependencies: {e}")
    
    def _create_networks(self):
        """Create networks defined in compose file"""
        if not self.compose_config:
            return
        
        # Always create a default network for the project
        default_network_name = f"{self.project_name}_default"
        try:
            network = self.client.networks.create(
                name=default_network_name,
                driver="bridge",
                labels=self.default_labels
            )
            self.networks[default_network_name] = network
            logger.info(f"Created default network: {default_network_name}")
        except docker.errors.APIError as e:
            if "already exists" in str(e):
                network = self.client.networks.get(default_network_name)
                self.networks[default_network_name] = network
            else:
                raise
        
        # Create additional networks
        for name, config in self.compose_config.networks.items():
            network_name = f"{self.project_name}_{name}"
            try:
                driver = config.get('driver', 'bridge') if config else 'bridge'
                network = self.client.networks.create(
                    name=network_name,
                    driver=driver,
                    labels=self.default_labels
                )
                self.networks[name] = network
                logger.info(f"Created network: {network_name}")
            except docker.errors.APIError as e:
                if "already exists" in str(e):
                    network = self.client.networks.get(network_name)
                    self.networks[name] = network
                else:
                    raise
    
    def _build_service_image(self, service: ServiceDefinition, context_path: Path) -> str:
        """
        Build Docker image for a service
        
        Args:
            service: Service definition
            context_path: Base path for build context
            
        Returns:
            Image tag
        """
        if not service.build:
            return service.image
        
        # Determine build context
        build_context = context_path / service.build.get('context', '.')
        dockerfile = service.build.get('dockerfile', 'Dockerfile')
        
        # Generate image tag
        image_tag = f"{self.project_name}_{service.name}:latest"
        
        logger.info(f"Building image for service '{service.name}'")
        
        try:
            # Build the image
            image, build_logs = self.client.images.build(
                path=str(build_context),
                dockerfile=dockerfile,
                tag=image_tag,
                buildargs=service.build.get('args', {}),
                labels=self.default_labels,
                rm=True
            )
            
            # Log build output
            for log in build_logs:
                if 'stream' in log:
                    logger.debug(log['stream'].strip())
            
            logger.info(f"Successfully built image: {image_tag}")
            return image_tag
            
        except docker.errors.BuildError as e:
            logger.error(f"Failed to build image for service '{service.name}': {e}")
            raise
    
    def _create_container(self, service: ServiceDefinition, image: str) -> Any:
        """
        Create a container for a service
        
        Args:
            service: Service definition
            image: Docker image to use
            
        Returns:
            Container object
        """
        container_name = f"{self.project_name}_{service.name}_1"
        
        # Prepare container configuration
        config = {
            "image": image,
            "name": container_name,
            "labels": {**self.default_labels, **service.labels},
            "environment": service.environment,
            "detach": True,
            "auto_remove": False
        }
        
        # Add command if specified
        if service.command:
            config["command"] = service.command
        
        # Add ports
        if service.ports:
            ports = {}
            for port_mapping in service.ports:
                if ':' in port_mapping:
                    host_port, container_port = port_mapping.split(':', 1)
                    ports[container_port] = host_port
                else:
                    ports[port_mapping] = None
            config["ports"] = ports
        
        # Add volumes (with safety checks)
        if service.volumes:
            volumes = {}
            for volume in service.volumes:
                if ':' in volume:
                    # Host mount - restrict to safe paths
                    host_path, container_path = volume.split(':', 1)
                    # Only allow relative paths or temp directories
                    if not host_path.startswith('/') or host_path.startswith('/tmp'):
                        volumes[host_path] = {
                            'bind': container_path,
                            'mode': 'rw'
                        }
                    else:
                        logger.warning(f"Skipping unsafe volume mount: {volume}")
                else:
                    # Named volume
                    volumes[volume] = {'bind': f'/data/{volume}', 'mode': 'rw'}
            if volumes:
                config["volumes"] = volumes
        
        # Add restart policy
        if service.restart != "no":
            config["restart_policy"] = {"Name": service.restart}
        
        # Create container
        try:
            container = self.client.containers.create(**config)
            logger.info(f"Created container: {container_name}")
            return container
        except docker.errors.APIError as e:
            logger.error(f"Failed to create container for service '{service.name}': {e}")
            raise
    
    def _connect_container_networks(self, container: Any, service: ServiceDefinition):
        """Connect container to specified networks"""
        # Always connect to default network
        default_network = self.networks.get(f"{self.project_name}_default")
        if default_network:
            try:
                default_network.connect(container, aliases=[service.name])
            except docker.errors.APIError:
                pass  # Already connected
        
        # Connect to additional networks
        for network_name in service.networks:
            network = self.networks.get(network_name)
            if network:
                try:
                    network.connect(container, aliases=[service.name])
                    logger.debug(f"Connected {service.name} to network {network_name}")
                except docker.errors.APIError:
                    pass  # Already connected
    
    def start_services(self, context_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Start all services in dependency order
        
        Args:
            context_path: Base path for build contexts and compose file
            
        Returns:
            Dictionary of service_name -> container mapping
        """
        if not self.compose_config:
            raise ValueError("No compose configuration loaded")
        
        context_path = context_path or Path.cwd()
        
        # Create networks first
        self._create_networks()
        
        # Resolve startup order
        startup_order = self._resolve_dependency_order()
        
        # Start services
        for service_name in startup_order:
            service = self.compose_config.services[service_name]
            
            try:
                # Build or pull image
                if service.build:
                    image = self._build_service_image(service, context_path)
                else:
                    # Pull image if not exists
                    try:
                        self.client.images.get(service.image)
                        image = service.image
                    except docker.errors.ImageNotFound:
                        logger.info(f"Pulling image: {service.image}")
                        self.client.images.pull(service.image)
                        image = service.image
                
                # Create container
                container = self._create_container(service, image)
                
                # Connect to networks
                self._connect_container_networks(container, service)
                
                # Start container
                container.start()
                logger.info(f"Started service: {service_name}")
                
                self.containers[service_name] = container
                
                # Wait for health check if defined
                if service.healthcheck:
                    self._wait_for_health(service_name, container)
                
            except Exception as e:
                logger.error(f"Failed to start service '{service_name}': {e}")
                # Clean up started containers on failure
                self.stop_services()
                raise
        
        logger.info(f"Successfully started {len(self.containers)} services")
        return self.containers
    
    def _wait_for_health(self, service_name: str, container: Any, timeout: int = 60):
        """Wait for container to become healthy"""
        logger.info(f"Waiting for {service_name} to become healthy...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            container.reload()
            health = container.attrs.get('State', {}).get('Health', {})
            status = health.get('Status', 'none')
            
            if status == 'healthy':
                logger.info(f"Service {service_name} is healthy")
                return
            elif status == 'unhealthy':
                logs = container.logs(tail=50).decode('utf-8')
                raise RuntimeError(f"Service {service_name} is unhealthy. Last logs:\n{logs}")
            
            time.sleep(2)
        
        raise TimeoutError(f"Service {service_name} health check timed out")
    
    def stop_services(self):
        """Stop all managed services"""
        logger.info("Stopping all services...")
        
        # Stop in reverse order
        for service_name in reversed(list(self.containers.keys())):
            container = self.containers[service_name]
            try:
                container.stop(timeout=10)
                container.remove()
                logger.info(f"Stopped service: {service_name}")
            except docker.errors.APIError as e:
                logger.warning(f"Error stopping service {service_name}: {e}")
        
        self.containers.clear()
    
    def get_service_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status of all services
        
        Returns:
            Dictionary of service_name -> status info
        """
        status = {}
        
        for service_name, container in self.containers.items():
            try:
                container.reload()
                status[service_name] = {
                    "status": container.status,
                    "health": container.attrs.get('State', {}).get('Health', {}).get('Status', 'none'),
                    "ports": container.attrs.get('NetworkSettings', {}).get('Ports', {}),
                    "networks": list(container.attrs.get('NetworkSettings', {}).get('Networks', {}).keys())
                }
            except docker.errors.APIError:
                status[service_name] = {"status": "removed"}
        
        return status
    
    def get_service_logs(self, service_name: str, lines: int = 100) -> str:
        """
        Get logs from a specific service
        
        Args:
            service_name: Name of the service
            lines: Number of lines to retrieve
            
        Returns:
            Log output as string
        """
        container = self.containers.get(service_name)
        if not container:
            raise ValueError(f"Service '{service_name}' not found")
        
        try:
            logs = container.logs(tail=lines, timestamps=True).decode('utf-8')
            return logs
        except docker.errors.APIError as e:
            logger.error(f"Failed to get logs for service '{service_name}': {e}")
            raise
    
    def execute_in_service(self, service_name: str, command: str, workdir: Optional[str] = None) -> Tuple[int, str]:
        """
        Execute a command in a running service container
        
        Args:
            service_name: Name of the service
            command: Command to execute
            workdir: Working directory
            
        Returns:
            Tuple of (exit_code, output)
        """
        container = self.containers.get(service_name)
        if not container:
            raise ValueError(f"Service '{service_name}' not found")
        
        try:
            exec_result = container.exec_run(
                command,
                workdir=workdir,
                demux=False
            )
            return exec_result.exit_code, exec_result.output.decode('utf-8')
        except docker.errors.APIError as e:
            logger.error(f"Failed to execute command in service '{service_name}': {e}")
            raise
    
    def cleanup(self):
        """Clean up all resources (containers and networks)"""
        logger.info(f"Cleaning up resources for project: {self.project_name}")
        
        # Stop containers
        self.stop_services()
        
        # Remove networks
        for network_name, network in self.networks.items():
            try:
                network.remove()
                logger.info(f"Removed network: {network_name}")
            except docker.errors.APIError as e:
                logger.warning(f"Error removing network {network_name}: {e}")
        
        self.networks.clear()
    
    def wait_for_healthy(self, timeout: int = 120) -> bool:
        """
        Wait for all services to become healthy
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if all services are healthy, False otherwise
        """
        logger.info("Waiting for all services to become healthy...")
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            all_healthy = True
            status = self.get_service_status()
            
            for service_name, info in status.items():
                service = self.compose_config.services.get(service_name)
                
                # Check container status
                if info['status'] != 'running':
                    all_healthy = False
                    break
                
                # Check health if healthcheck defined
                if service and service.healthcheck:
                    if info['health'] not in ['healthy', 'none']:
                        all_healthy = False
                        break
            
            if all_healthy:
                logger.info("All services are healthy")
                return True
            
            time.sleep(2)
        
        # Log unhealthy services
        for service_name, info in status.items():
            if info['status'] != 'running' or info['health'] == 'unhealthy':
                logger.error(f"Service {service_name} is not healthy: {info}")
        
        return False
    
    @classmethod
    def detect_compose_file(cls, project_path: Path) -> Optional[Path]:
        """
        Detect docker-compose file in project
        
        Args:
            project_path: Root path of the project
            
        Returns:
            Path to compose file or None
        """
        compose_names = [
            'docker-compose.yml',
            'docker-compose.yaml',
            'compose.yml',
            'compose.yaml'
        ]
        
        for name in compose_names:
            compose_path = project_path / name
            if compose_path.exists():
                return compose_path
        
        return None