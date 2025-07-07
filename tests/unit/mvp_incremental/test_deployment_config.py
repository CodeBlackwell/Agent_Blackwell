"""
Unit tests for DeploymentConfigGenerator
"""

import pytest
import json
import yaml
from pathlib import Path
import tempfile
import shutil
from workflows.mvp_incremental.deployment_config import (
    DeploymentConfigGenerator, DeploymentTarget, ServiceConfig
)


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def angular_express_project(temp_project_dir):
    """Create an Angular + Express project"""
    package_json = {
        "name": "test-app",
        "dependencies": {
            "@angular/core": "^15.0.0",
            "express": "^4.18.0",
            "mongodb": "^4.5.0",
            "redis": "^4.0.0"
        }
    }
    (temp_project_dir / "package.json").write_text(json.dumps(package_json))
    return temp_project_dir


@pytest.fixture
def fastapi_project(temp_project_dir):
    """Create a FastAPI project"""
    requirements = """
fastapi==0.95.0
uvicorn==0.21.0
psycopg2-binary==2.9.5
redis==4.5.0
"""
    (temp_project_dir / "requirements.txt").write_text(requirements)
    return temp_project_dir


@pytest.fixture
def deployment_generator(temp_project_dir):
    """Create a DeploymentConfigGenerator instance"""
    return DeploymentConfigGenerator(temp_project_dir)


class TestServiceConfig:
    
    def test_service_config_initialization(self):
        """Test ServiceConfig dataclass"""
        service = ServiceConfig(
            name="backend",
            image="app/backend:latest",
            ports=["3000:3000"],
            environment={"NODE_ENV": "production"},
            depends_on=["database"]
        )
        
        assert service.name == "backend"
        assert service.image == "app/backend:latest"
        assert service.ports == ["3000:3000"]
        assert service.environment == {"NODE_ENV": "production"}
        assert service.depends_on == ["database"]
        assert service.replicas == 1


class TestDeploymentConfigGenerator:
    
    def test_initialization(self, deployment_generator, temp_project_dir):
        """Test DeploymentConfigGenerator initialization"""
        assert deployment_generator.project_path == temp_project_dir
        assert deployment_generator.detected_services == []
        assert deployment_generator.deployment_configs == {}
    
    def test_analyze_angular_express_project(self, angular_express_project):
        """Test analyzing Angular + Express project"""
        generator = DeploymentConfigGenerator(angular_express_project)
        analysis = generator.analyze_project()
        
        assert 'angular' in analysis['frameworks']
        assert 'express' in analysis['frameworks']
        assert 'mongodb' in analysis['databases']
        assert 'redis' in analysis['databases']
        assert analysis['requires_build'] is True
        assert analysis['static_assets'] is True
        assert analysis['api_services'] is True
        
        # Check services detected
        service_names = [s.name for s in generator.detected_services]
        assert 'frontend' in service_names
        assert 'backend' in service_names
        assert 'mongodb' in service_names
        assert 'redis' in service_names
    
    def test_analyze_fastapi_project(self, fastapi_project):
        """Test analyzing FastAPI project"""
        generator = DeploymentConfigGenerator(fastapi_project)
        analysis = generator.analyze_project()
        
        assert 'fastapi' in analysis['frameworks']
        assert 'postgresql' in analysis['databases']
        assert 'redis' in analysis['databases']
        assert analysis['api_services'] is True
        
        service_names = [s.name for s in generator.detected_services]
        assert 'backend' in service_names
        assert 'postgres' in service_names
        assert 'redis' in service_names
    
    def test_generate_docker_compose(self, angular_express_project):
        """Test Docker Compose generation"""
        generator = DeploymentConfigGenerator(angular_express_project)
        generator.analyze_project()
        
        compose_yaml = generator.generate_docker_compose()
        compose_config = yaml.safe_load(compose_yaml)
        
        # Check structure
        assert compose_config['version'] == '3.8'
        assert 'services' in compose_config
        assert 'volumes' in compose_config
        assert 'networks' in compose_config
        
        # Check services
        services = compose_config['services']
        assert 'frontend' in services
        assert 'backend' in services
        assert 'mongodb' in services
        assert 'redis' in services
        
        # Check backend dependencies
        assert 'depends_on' in services['backend']
        assert 'mongodb' in services['backend']['depends_on']
        assert 'redis' in services['backend']['depends_on']
        
        # Check frontend dependencies
        assert services['frontend']['depends_on'] == ['backend']
        
        # Check MongoDB configuration
        mongodb = services['mongodb']
        assert mongodb['image'] == 'mongo:6'
        assert '27017:27017' in mongodb['ports']
        assert 'MONGO_INITDB_ROOT_USERNAME' in mongodb['environment']
        
        # Check volumes
        assert 'mongodb_data' in compose_config['volumes']
        assert 'redis_data' in compose_config['volumes']
    
    def test_generate_kubernetes_manifests(self, angular_express_project):
        """Test Kubernetes manifests generation"""
        generator = DeploymentConfigGenerator(angular_express_project)
        generator.analyze_project()
        
        manifests = generator.generate_kubernetes_manifests()
        
        # Check namespace
        assert 'namespace.yaml' in manifests
        namespace = yaml.safe_load(manifests['namespace.yaml'])
        assert namespace['kind'] == 'Namespace'
        assert namespace['metadata']['name'] == 'app'
        
        # Check deployments
        assert 'frontend-deployment.yaml' in manifests
        assert 'backend-deployment.yaml' in manifests
        assert 'mongodb-deployment.yaml' in manifests
        
        # Check frontend deployment
        frontend_deployment = yaml.safe_load(manifests['frontend-deployment.yaml'])
        assert frontend_deployment['kind'] == 'Deployment'
        assert frontend_deployment['spec']['replicas'] == 1
        container = frontend_deployment['spec']['template']['spec']['containers'][0]
        assert container['name'] == 'frontend'
        assert container['ports'][0]['containerPort'] == 80
        
        # Check services
        assert 'frontend-service.yaml' in manifests
        frontend_service = yaml.safe_load(manifests['frontend-service.yaml'])
        assert frontend_service['kind'] == 'Service'
        assert frontend_service['spec']['type'] == 'LoadBalancer'  # Frontend exposed
        
        # Check backend service
        assert 'backend-service.yaml' in manifests
        backend_service = yaml.safe_load(manifests['backend-service.yaml'])
        assert backend_service['spec']['type'] == 'ClusterIP'  # Backend internal
    
    def test_generate_node_dockerfile(self, angular_express_project):
        """Test Node.js Dockerfile generation"""
        generator = DeploymentConfigGenerator(angular_express_project)
        
        # Frontend Dockerfile
        frontend_dockerfile = generator._generate_node_dockerfile('frontend')
        assert 'FROM node:18-alpine AS builder' in frontend_dockerfile
        assert 'npm run build' in frontend_dockerfile
        assert 'FROM nginx:alpine' in frontend_dockerfile
        assert 'EXPOSE 80' in frontend_dockerfile
        
        # Backend Dockerfile
        backend_dockerfile = generator._generate_node_dockerfile('backend')
        assert 'FROM node:18-alpine' in backend_dockerfile
        assert 'EXPOSE 3000' in backend_dockerfile
        assert 'CMD ["node", "server.js"]' in backend_dockerfile
    
    def test_generate_python_dockerfile(self, fastapi_project):
        """Test Python Dockerfile generation"""
        generator = DeploymentConfigGenerator(fastapi_project)
        
        dockerfile = generator._generate_python_dockerfile('backend')
        assert 'FROM python:3.11-slim' in dockerfile
        assert 'pip install --no-cache-dir -r requirements.txt' in dockerfile
        assert 'EXPOSE 8000' in dockerfile
        assert 'CMD ["uvicorn", "main:app"' in dockerfile
    
    def test_generate_deployment_files(self, angular_express_project):
        """Test complete deployment file generation"""
        generator = DeploymentConfigGenerator(angular_express_project)
        generator.analyze_project()
        
        files = generator.generate_deployment_files()
        
        # Check essential files
        assert 'docker-compose.yml' in files
        assert '.dockerignore' in files
        assert 'deploy.sh' in files
        
        # Check Dockerfiles
        assert 'Dockerfile.frontend' in files
        assert 'Dockerfile.backend' in files
        
        # Check Kubernetes files
        k8s_files = [f for f in files if f.startswith('k8s/')]
        assert len(k8s_files) > 0
        assert 'k8s/namespace.yaml' in files
        
        # Check dockerignore content
        dockerignore = files['.dockerignore']
        assert 'node_modules' in dockerignore
        assert '.env' in dockerignore
        assert '__pycache__' in dockerignore
        
        # Check deploy script
        deploy_script = files['deploy.sh']
        assert '#!/bin/bash' in deploy_script
        assert 'docker-compose build' in deploy_script
        assert 'docker-compose up -d' in deploy_script
    
    def test_save_deployment_files(self, deployment_generator, temp_project_dir):
        """Test saving deployment files to disk"""
        # Add a simple service
        deployment_generator.detected_services.append(
            ServiceConfig(name="test", build_context=".")
        )
        
        deployment_generator.save_deployment_files()
        
        # Check files exist
        assert (temp_project_dir / 'docker-compose.yml').exists()
        assert (temp_project_dir / '.dockerignore').exists()
        assert (temp_project_dir / 'deploy.sh').exists()
        
        # Check deploy script is executable
        import os
        deploy_script = temp_project_dir / 'deploy.sh'
        assert os.access(deploy_script, os.X_OK)
    
    def test_parse_ports_for_k8s(self, deployment_generator):
        """Test port parsing for Kubernetes"""
        # Container ports
        container_ports = deployment_generator._parse_ports_for_k8s(['8080:80', '3000'])
        assert container_ports[0]['containerPort'] == 80
        assert container_ports[1]['containerPort'] == 3000
        
        # Service ports
        service_ports = deployment_generator._parse_service_ports_for_k8s(['8080:80', '3000'])
        assert service_ports[0]['port'] == 8080
        assert service_ports[0]['targetPort'] == 80
        assert service_ports[1]['port'] == 3000
        assert service_ports[1]['targetPort'] == 3000
    
    def test_env_to_k8s_format(self, deployment_generator):
        """Test environment variable conversion for K8s"""
        env_dict = {
            'NODE_ENV': 'production',
            'PORT': '3000',
            'DEBUG': 'false'
        }
        
        k8s_env = deployment_generator._env_to_k8s_format(env_dict)
        
        assert len(k8s_env) == 3
        assert {'name': 'NODE_ENV', 'value': 'production'} in k8s_env
        assert {'name': 'PORT', 'value': '3000'} in k8s_env
        assert {'name': 'DEBUG', 'value': 'false'} in k8s_env