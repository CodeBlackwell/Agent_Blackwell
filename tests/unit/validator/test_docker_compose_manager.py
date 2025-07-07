"""
Unit tests for DockerComposeManager
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path
import yaml
import tempfile
import os

from agents.validator.docker_compose_manager import (
    DockerComposeManager, ServiceDefinition, ComposeConfig
)


class TestServiceDefinition(unittest.TestCase):
    """Test ServiceDefinition dataclass"""
    
    def test_service_definition_defaults(self):
        """Test default values for ServiceDefinition"""
        service = ServiceDefinition(name="test_service", image="test:latest")
        
        self.assertEqual(service.name, "test_service")
        self.assertEqual(service.image, "test:latest")
        self.assertEqual(service.ports, [])
        self.assertEqual(service.environment, {})
        self.assertEqual(service.volumes, [])
        self.assertEqual(service.depends_on, [])
        self.assertEqual(service.networks, [])
        self.assertEqual(service.restart, "no")
        self.assertIsNone(service.build)
        self.assertIsNone(service.command)
        self.assertIsNone(service.healthcheck)


class TestComposeConfig(unittest.TestCase):
    """Test ComposeConfig dataclass"""
    
    def test_compose_config_defaults(self):
        """Test default values for ComposeConfig"""
        config = ComposeConfig(
            version="3",
            services={"web": ServiceDefinition(name="web", image="nginx")}
        )
        
        self.assertEqual(config.version, "3")
        self.assertEqual(len(config.services), 1)
        self.assertEqual(config.networks, {})
        self.assertEqual(config.volumes, {})


class TestDockerComposeManager(unittest.TestCase):
    """Test DockerComposeManager class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.session_id = "test_session_123"
        self.manager = DockerComposeManager(self.session_id)
        
    @patch('docker.from_env')
    def test_initialization(self, mock_docker):
        """Test manager initialization"""
        manager = DockerComposeManager("test_session", "test_project")
        
        self.assertEqual(manager.session_id, "test_session")
        self.assertEqual(manager.project_name, "test_project")
        self.assertEqual(manager.default_labels["session_id"], "test_session")
        self.assertEqual(manager.default_labels["project"], "test_project")
        self.assertEqual(manager.default_labels["manager"], "compose")
        mock_docker.assert_called_once()
    
    def test_parse_compose_file_not_found(self):
        """Test parsing non-existent compose file"""
        with self.assertRaises(ValueError) as cm:
            self.manager.parse_compose_file(Path("/non/existent/file.yml"))
        
        self.assertIn("Compose file not found", str(cm.exception))
    
    def test_parse_compose_file_invalid_yaml(self):
        """Test parsing invalid YAML"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write("invalid: yaml: content: [}")
            temp_file = f.name
        
        try:
            with self.assertRaises(ValueError) as cm:
                self.manager.parse_compose_file(Path(temp_file))
            
            self.assertIn("Invalid YAML syntax", str(cm.exception))
        finally:
            os.unlink(temp_file)
    
    def test_parse_compose_file_no_services(self):
        """Test parsing compose file without services section"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump({"version": "3", "networks": {}}, f)
            temp_file = f.name
        
        try:
            with self.assertRaises(ValueError) as cm:
                self.manager.parse_compose_file(Path(temp_file))
            
            self.assertIn("must contain 'services' section", str(cm.exception))
        finally:
            os.unlink(temp_file)
    
    def test_parse_compose_file_valid(self):
        """Test parsing valid compose file"""
        compose_content = {
            "version": "3.8",
            "services": {
                "web": {
                    "image": "nginx:latest",
                    "ports": ["80:80"],
                    "environment": {
                        "ENV_VAR": "value"
                    }
                },
                "api": {
                    "build": "./api",
                    "depends_on": ["db"],
                    "networks": ["backend"]
                },
                "db": {
                    "image": "postgres:13",
                    "volumes": ["db_data:/var/lib/postgresql/data"]
                }
            },
            "networks": {
                "backend": {"driver": "bridge"}
            },
            "volumes": {
                "db_data": {}
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump(compose_content, f)
            temp_file = f.name
        
        try:
            config = self.manager.parse_compose_file(Path(temp_file))
            
            self.assertEqual(config.version, "3.8")
            self.assertEqual(len(config.services), 3)
            
            # Check web service
            web = config.services["web"]
            self.assertEqual(web.name, "web")
            self.assertEqual(web.image, "nginx:latest")
            self.assertEqual(web.ports, ["80:80"])
            self.assertEqual(web.environment["ENV_VAR"], "value")
            
            # Check api service
            api = config.services["api"]
            self.assertEqual(api.name, "api")
            self.assertEqual(api.build, {"context": "./api"})
            self.assertEqual(api.depends_on, ["db"])
            self.assertEqual(api.networks, ["backend"])
            
            # Check networks and volumes
            self.assertIn("backend", config.networks)
            self.assertIn("db_data", config.volumes)
            
        finally:
            os.unlink(temp_file)
    
    def test_parse_environment_dict(self):
        """Test parsing environment as dictionary"""
        env = self.manager._parse_environment({"KEY1": "value1", "KEY2": 123})
        
        self.assertEqual(env["KEY1"], "value1")
        self.assertEqual(env["KEY2"], "123")  # Converted to string
    
    def test_parse_environment_list(self):
        """Test parsing environment as list"""
        with patch.dict(os.environ, {"HOST_VAR": "host_value"}):
            env = self.manager._parse_environment([
                "KEY1=value1",
                "KEY2=value2",
                "HOST_VAR"  # From host environment
            ])
            
            self.assertEqual(env["KEY1"], "value1")
            self.assertEqual(env["KEY2"], "value2")
            self.assertEqual(env["HOST_VAR"], "host_value")
    
    def test_parse_depends_on_list(self):
        """Test parsing depends_on as list"""
        deps = self.manager._parse_depends_on(["db", "cache"])
        self.assertEqual(deps, ["db", "cache"])
    
    def test_parse_depends_on_dict(self):
        """Test parsing depends_on as dictionary (extended format)"""
        deps = self.manager._parse_depends_on({
            "db": {"condition": "service_healthy"},
            "cache": {"condition": "service_started"}
        })
        self.assertEqual(sorted(deps), ["cache", "db"])
    
    def test_resolve_dependency_order_simple(self):
        """Test dependency resolution with simple dependencies"""
        self.manager.compose_config = ComposeConfig(
            version="3",
            services={
                "web": ServiceDefinition(name="web", image="nginx", depends_on=["api"]),
                "api": ServiceDefinition(name="api", image="node", depends_on=["db"]),
                "db": ServiceDefinition(name="db", image="postgres")
            }
        )
        
        order = self.manager._resolve_dependency_order()
        
        # db should come before api, api before web
        self.assertEqual(order, ["db", "api", "web"])
    
    def test_resolve_dependency_order_circular(self):
        """Test circular dependency detection"""
        self.manager.compose_config = ComposeConfig(
            version="3",
            services={
                "a": ServiceDefinition(name="a", image="img", depends_on=["b"]),
                "b": ServiceDefinition(name="b", image="img", depends_on=["c"]),
                "c": ServiceDefinition(name="c", image="img", depends_on=["a"])
            }
        )
        
        with self.assertRaises(ValueError) as cm:
            self.manager._resolve_dependency_order()
        
        self.assertIn("Circular dependencies detected", str(cm.exception))
    
    @patch('docker.from_env')
    def test_create_networks(self, mock_docker):
        """Test network creation"""
        mock_client = Mock()
        mock_docker.return_value = mock_client
        
        # Mock network creation
        mock_network = Mock()
        mock_client.networks.create.return_value = mock_network
        
        manager = DockerComposeManager("test_session")
        manager.compose_config = ComposeConfig(
            version="3",
            services={},
            networks={"backend": {"driver": "bridge"}}
        )
        
        manager._create_networks()
        
        # Should create default network
        mock_client.networks.create.assert_any_call(
            name="validator_test_session_default",
            driver="bridge",
            labels=manager.default_labels
        )
        
        # Should create backend network
        mock_client.networks.create.assert_any_call(
            name="validator_test_session_backend",
            driver="bridge",
            labels=manager.default_labels
        )
    
    def test_detect_compose_file(self):
        """Test compose file detection"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # No compose file
            self.assertIsNone(DockerComposeManager.detect_compose_file(temp_path))
            
            # Create docker-compose.yml
            compose_path = temp_path / "docker-compose.yml"
            compose_path.write_text("version: '3'")
            
            detected = DockerComposeManager.detect_compose_file(temp_path)
            self.assertEqual(detected, compose_path)
            
            # Test other valid names
            compose_path.unlink()
            alt_path = temp_path / "compose.yaml"
            alt_path.write_text("version: '3'")
            
            detected = DockerComposeManager.detect_compose_file(temp_path)
            self.assertEqual(detected, alt_path)
    
    @patch('docker.from_env')
    def test_get_service_status(self, mock_docker):
        """Test getting service status"""
        mock_container = Mock()
        mock_container.status = "running"
        mock_container.attrs = {
            "State": {"Health": {"Status": "healthy"}},
            "NetworkSettings": {
                "Ports": {"80/tcp": [{"HostPort": "8080"}]},
                "Networks": {"default": {}, "backend": {}}
            }
        }
        
        self.manager.containers = {"web": mock_container}
        
        status = self.manager.get_service_status()
        
        self.assertEqual(status["web"]["status"], "running")
        self.assertEqual(status["web"]["health"], "healthy")
        self.assertIn("80/tcp", status["web"]["ports"])
        self.assertIn("default", status["web"]["networks"])
    
    @patch('docker.from_env')
    def test_get_service_logs(self, mock_docker):
        """Test getting service logs"""
        mock_container = Mock()
        mock_container.logs.return_value = b"Service log output\nAnother line"
        
        self.manager.containers = {"web": mock_container}
        
        logs = self.manager.get_service_logs("web", lines=10)
        
        self.assertIn("Service log output", logs)
        self.assertIn("Another line", logs)
        mock_container.logs.assert_called_with(tail=10, timestamps=True)
    
    @patch('docker.from_env')
    def test_execute_in_service(self, mock_docker):
        """Test command execution in service"""
        mock_container = Mock()
        mock_result = Mock()
        mock_result.exit_code = 0
        mock_result.output = b"Command output"
        mock_container.exec_run.return_value = mock_result
        
        self.manager.containers = {"api": mock_container}
        
        exit_code, output = self.manager.execute_in_service("api", "echo test")
        
        self.assertEqual(exit_code, 0)
        self.assertEqual(output, "Command output")
        mock_container.exec_run.assert_called_with(
            "echo test",
            workdir=None,
            demux=False
        )
    
    @patch('docker.from_env')
    def test_cleanup(self, mock_docker):
        """Test cleanup of resources"""
        # Mock containers
        mock_container = Mock()
        self.manager.containers = {"web": mock_container}
        
        # Mock networks
        mock_network = Mock()
        self.manager.networks = {"default": mock_network}
        
        self.manager.cleanup()
        
        # Should stop and remove containers
        mock_container.stop.assert_called_with(timeout=10)
        mock_container.remove.assert_called_once()
        
        # Should remove networks
        mock_network.remove.assert_called_once()
        
        # Should clear internal state
        self.assertEqual(len(self.manager.containers), 0)
        self.assertEqual(len(self.manager.networks), 0)


if __name__ == '__main__':
    unittest.main()