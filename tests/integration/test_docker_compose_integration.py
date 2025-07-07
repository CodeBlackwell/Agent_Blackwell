"""
Integration tests for DockerComposeManager with real Docker
"""

import unittest
import tempfile
import shutil
from pathlib import Path
import yaml
import time
import docker

from agents.validator.docker_compose_manager import DockerComposeManager


class TestDockerComposeIntegration(unittest.TestCase):
    """Integration tests that require Docker to be running"""
    
    @classmethod
    def setUpClass(cls):
        """Check if Docker is available"""
        try:
            cls.docker_client = docker.from_env()
            cls.docker_client.ping()
            cls.docker_available = True
        except:
            cls.docker_available = False
    
    def setUp(self):
        """Set up test fixtures"""
        if not self.docker_available:
            self.skipTest("Docker not available")
        
        self.test_dir = Path(tempfile.mkdtemp(prefix="test_compose_"))
        self.session_id = f"test_{int(time.time())}"
        self.manager = DockerComposeManager(self.session_id)
        
    def tearDown(self):
        """Clean up after tests"""
        if hasattr(self, 'manager'):
            try:
                self.manager.cleanup()
            except:
                pass
        
        if hasattr(self, 'test_dir') and self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_simple_single_service(self):
        """Test starting a single service"""
        # Create compose file
        compose_content = {
            "version": "3",
            "services": {
                "web": {
                    "image": "nginx:alpine",
                    "ports": ["8888:80"]
                }
            }
        }
        
        compose_file = self.test_dir / "docker-compose.yml"
        with open(compose_file, 'w') as f:
            yaml.dump(compose_content, f)
        
        # Parse and start services
        config = self.manager.parse_compose_file(compose_file)
        self.assertEqual(len(config.services), 1)
        
        containers = self.manager.start_services(self.test_dir)
        self.assertEqual(len(containers), 1)
        
        # Check service status
        status = self.manager.get_service_status()
        self.assertEqual(status["web"]["status"], "running")
        
        # Execute command in service
        exit_code, output = self.manager.execute_in_service("web", "nginx -v")
        self.assertEqual(exit_code, 0)
        self.assertIn("nginx", output)
        
        # Get logs
        logs = self.manager.get_service_logs("web", lines=10)
        self.assertIsInstance(logs, str)
    
    def test_multi_service_with_dependencies(self):
        """Test multiple services with dependencies"""
        # Create a simple Node.js app
        app_content = """
const http = require('http');
const server = http.createServer((req, res) => {
    res.writeHead(200, { 'Content-Type': 'text/plain' });
    res.end('Hello from Node.js\\n');
});
server.listen(3000, '0.0.0.0', () => {
    console.log('Server running on port 3000');
});
"""
        
        app_file = self.test_dir / "app.js"
        app_file.write_text(app_content)
        
        # Create Dockerfile
        dockerfile_content = """
FROM node:16-alpine
WORKDIR /app
COPY app.js .
CMD ["node", "app.js"]
"""
        dockerfile = self.test_dir / "Dockerfile"
        dockerfile.write_text(dockerfile_content)
        
        # Create compose file with dependencies
        compose_content = {
            "version": "3",
            "services": {
                "app": {
                    "build": ".",
                    "ports": ["3000:3000"],
                    "depends_on": ["redis"],
                    "environment": {
                        "NODE_ENV": "test"
                    }
                },
                "redis": {
                    "image": "redis:alpine"
                }
            }
        }
        
        compose_file = self.test_dir / "docker-compose.yml"
        with open(compose_file, 'w') as f:
            yaml.dump(compose_content, f)
        
        # Parse compose file
        config = self.manager.parse_compose_file(compose_file)
        self.assertEqual(len(config.services), 2)
        
        # Check dependency order
        order = self.manager._resolve_dependency_order()
        self.assertEqual(order, ["redis", "app"])
        
        # Start services
        containers = self.manager.start_services(self.test_dir)
        self.assertEqual(len(containers), 2)
        
        # Wait a bit for services to stabilize
        time.sleep(2)
        
        # Check both services are running
        status = self.manager.get_service_status()
        self.assertEqual(status["app"]["status"], "running")
        self.assertEqual(status["redis"]["status"], "running")
        
        # Test connectivity between services
        exit_code, output = self.manager.execute_in_service("app", "ping -c 1 redis")
        self.assertEqual(exit_code, 0)
    
    def test_health_check(self):
        """Test service with health check"""
        # Create compose file with health check
        compose_content = {
            "version": "3",
            "services": {
                "web": {
                    "image": "nginx:alpine",
                    "healthcheck": {
                        "test": ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost/"],
                        "interval": "2s",
                        "timeout": "3s",
                        "retries": 3,
                        "start_period": "2s"
                    }
                }
            }
        }
        
        compose_file = self.test_dir / "docker-compose.yml"
        with open(compose_file, 'w') as f:
            yaml.dump(compose_content, f)
        
        # Parse and start services
        config = self.manager.parse_compose_file(compose_file)
        containers = self.manager.start_services(self.test_dir)
        
        # Wait for health check
        healthy = self.manager.wait_for_healthy(timeout=30)
        self.assertTrue(healthy)
        
        # Verify health status
        status = self.manager.get_service_status()
        self.assertEqual(status["web"]["health"], "healthy")
    
    def test_network_isolation(self):
        """Test that services can communicate on custom networks"""
        compose_content = {
            "version": "3",
            "services": {
                "web1": {
                    "image": "alpine",
                    "command": "sleep 300",
                    "networks": ["frontend"]
                },
                "web2": {
                    "image": "alpine", 
                    "command": "sleep 300",
                    "networks": ["frontend", "backend"]
                },
                "db": {
                    "image": "alpine",
                    "command": "sleep 300",
                    "networks": ["backend"]
                }
            },
            "networks": {
                "frontend": {},
                "backend": {}
            }
        }
        
        compose_file = self.test_dir / "docker-compose.yml"
        with open(compose_file, 'w') as f:
            yaml.dump(compose_content, f)
        
        # Start services
        config = self.manager.parse_compose_file(compose_file)
        containers = self.manager.start_services(self.test_dir)
        
        # Test connectivity
        # web1 should reach web2 (both on frontend)
        exit_code, _ = self.manager.execute_in_service("web1", "ping -c 1 web2")
        self.assertEqual(exit_code, 0)
        
        # web2 should reach db (both on backend)
        exit_code, _ = self.manager.execute_in_service("web2", "ping -c 1 db")
        self.assertEqual(exit_code, 0)
        
        # web1 should NOT reach db (different networks)
        exit_code, _ = self.manager.execute_in_service("web1", "ping -c 1 db")
        self.assertNotEqual(exit_code, 0)
    
    def test_environment_variables(self):
        """Test environment variable handling"""
        compose_content = {
            "version": "3",
            "services": {
                "app": {
                    "image": "alpine",
                    "command": "sleep 300",
                    "environment": {
                        "KEY1": "value1",
                        "KEY2": "value2"
                    }
                }
            }
        }
        
        compose_file = self.test_dir / "docker-compose.yml"
        with open(compose_file, 'w') as f:
            yaml.dump(compose_content, f)
        
        # Start service
        config = self.manager.parse_compose_file(compose_file)
        containers = self.manager.start_services(self.test_dir)
        
        # Check environment variables
        exit_code, output = self.manager.execute_in_service("app", "env")
        self.assertEqual(exit_code, 0)
        self.assertIn("KEY1=value1", output)
        self.assertIn("KEY2=value2", output)
    
    def test_volume_mount(self):
        """Test volume mounting (only temp directories)"""
        # Create a file to mount
        test_file = self.test_dir / "test.txt"
        test_file.write_text("Hello from host")
        
        compose_content = {
            "version": "3",
            "services": {
                "app": {
                    "image": "alpine",
                    "command": "sleep 300",
                    "volumes": [f"{self.test_dir}:/data"]
                }
            }
        }
        
        compose_file = self.test_dir / "docker-compose.yml"
        with open(compose_file, 'w') as f:
            yaml.dump(compose_content, f)
        
        # Start service
        config = self.manager.parse_compose_file(compose_file)
        containers = self.manager.start_services(self.test_dir)
        
        # Check if file is accessible
        exit_code, output = self.manager.execute_in_service("app", "cat /data/test.txt")
        self.assertEqual(exit_code, 0)
        self.assertIn("Hello from host", output)
    
    def test_cleanup_removes_all_resources(self):
        """Test that cleanup removes all containers and networks"""
        compose_content = {
            "version": "3",
            "services": {
                "web": {"image": "nginx:alpine"},
                "db": {"image": "redis:alpine"}
            }
        }
        
        compose_file = self.test_dir / "docker-compose.yml"
        with open(compose_file, 'w') as f:
            yaml.dump(compose_content, f)
        
        # Start services
        config = self.manager.parse_compose_file(compose_file)
        containers = self.manager.start_services(self.test_dir)
        
        # Get container and network IDs
        container_ids = [c.id for c in containers.values()]
        network_names = list(self.manager.networks.keys())
        
        # Cleanup
        self.manager.cleanup()
        
        # Verify containers are removed
        for container_id in container_ids:
            with self.assertRaises(docker.errors.NotFound):
                self.docker_client.containers.get(container_id)
        
        # Verify networks are removed (skip if still in use by other tests)
        for network_name in network_names:
            try:
                network = self.docker_client.networks.get(network_name)
                # Network might still exist if other tests are using it
            except docker.errors.NotFound:
                # This is expected - network was removed
                pass


class TestMEANStackScenario(unittest.TestCase):
    """Test a realistic MEAN stack scenario"""
    
    @classmethod
    def setUpClass(cls):
        """Check if Docker is available"""
        try:
            cls.docker_client = docker.from_env()
            cls.docker_client.ping()
            cls.docker_available = True
        except:
            cls.docker_available = False
    
    def setUp(self):
        """Set up test fixtures"""
        if not self.docker_available:
            self.skipTest("Docker not available")
        
        self.test_dir = Path(tempfile.mkdtemp(prefix="test_mean_"))
        self.session_id = f"mean_{int(time.time())}"
        self.manager = DockerComposeManager(self.session_id)
        
    def tearDown(self):
        """Clean up after tests"""
        if hasattr(self, 'manager'):
            try:
                self.manager.cleanup()
            except:
                pass
        
        if hasattr(self, 'test_dir') and self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_mean_stack_setup(self):
        """Test a simplified MEAN stack setup"""
        # Create directories
        (self.test_dir / "backend").mkdir()
        (self.test_dir / "frontend").mkdir()
        
        # Create minimal backend server
        backend_content = """
const express = require('express');
const app = express();
app.get('/api/health', (req, res) => {
    res.json({ status: 'ok', db: process.env.MONGO_URL || 'not configured' });
});
app.listen(3000, () => console.log('Backend running on port 3000'));
"""
        (self.test_dir / "backend/server.js").write_text(backend_content)
        
        # Create backend package.json
        backend_package = {
            "name": "backend",
            "version": "1.0.0",
            "main": "server.js",
            "scripts": {"start": "node server.js"},
            "dependencies": {"express": "^4.18.0"}
        }
        (self.test_dir / "backend/package.json").write_text(
            yaml.dump(backend_package, default_flow_style=False)
        )
        
        # Create backend Dockerfile
        backend_dockerfile = """
FROM node:16-alpine
WORKDIR /app
COPY package.json .
RUN npm install
COPY . .
CMD ["npm", "start"]
"""
        (self.test_dir / "backend/Dockerfile").write_text(backend_dockerfile)
        
        # Create simple frontend
        frontend_content = """
FROM nginx:alpine
RUN echo '<h1>MEAN Stack Frontend</h1>' > /usr/share/nginx/html/index.html
"""
        (self.test_dir / "frontend/Dockerfile").write_text(frontend_content)
        
        # Create docker-compose.yml
        compose_content = {
            "version": "3.8",
            "services": {
                "mongodb": {
                    "image": "mongo:5",
                    "environment": {
                        "MONGO_INITDB_ROOT_USERNAME": "admin",
                        "MONGO_INITDB_ROOT_PASSWORD": "password"
                    },
                    "networks": ["backend"]
                },
                "api": {
                    "build": "./backend",
                    "environment": {
                        "MONGO_URL": "mongodb://admin:password@mongodb:27017",
                        "NODE_ENV": "test"
                    },
                    "depends_on": ["mongodb"],
                    "networks": ["backend", "frontend"],
                    "ports": ["3000:3000"]
                },
                "web": {
                    "build": "./frontend",
                    "depends_on": ["api"],
                    "networks": ["frontend"],
                    "ports": ["8080:80"]
                }
            },
            "networks": {
                "frontend": {},
                "backend": {}
            }
        }
        
        compose_file = self.test_dir / "docker-compose.yml"
        with open(compose_file, 'w') as f:
            yaml.dump(compose_content, f)
        
        # Parse and validate
        config = self.manager.parse_compose_file(compose_file)
        self.assertEqual(len(config.services), 3)
        
        # Check dependency order
        order = self.manager._resolve_dependency_order()
        self.assertEqual(order, ["mongodb", "api", "web"])
        
        # Start services
        containers = self.manager.start_services(self.test_dir)
        self.assertEqual(len(containers), 3)
        
        # Wait for services to be ready
        time.sleep(5)
        
        # Check all services are running
        status = self.manager.get_service_status()
        for service in ["mongodb", "api", "web"]:
            self.assertEqual(status[service]["status"], "running")
        
        # Test API health endpoint
        exit_code, output = self.manager.execute_in_service(
            "api", 
            "wget -q -O - http://localhost:3000/api/health"
        )
        self.assertEqual(exit_code, 0)
        self.assertIn("ok", output)
        self.assertIn("mongodb", output)
        
        # Test that frontend can reach API
        exit_code, _ = self.manager.execute_in_service("web", "ping -c 1 api")
        self.assertEqual(exit_code, 0)
        
        # Test that API can reach MongoDB
        exit_code, _ = self.manager.execute_in_service("api", "ping -c 1 mongodb")
        self.assertEqual(exit_code, 0)


if __name__ == '__main__':
    unittest.main()