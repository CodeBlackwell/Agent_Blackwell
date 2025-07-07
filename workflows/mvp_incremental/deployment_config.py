"""
Deployment Configuration Generator for MVP Incremental Workflow

Generates deployment-ready configuration files for various platforms.
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum

from workflows.logger import setup_logger

logger = setup_logger(__name__)


class DeploymentTarget(Enum):
    """Supported deployment targets"""
    DOCKER = "docker"
    KUBERNETES = "kubernetes"
    DOCKER_COMPOSE = "docker-compose"
    HEROKU = "heroku"
    AWS = "aws"
    VERCEL = "vercel"
    NETLIFY = "netlify"
    RAILWAY = "railway"
    FLY_IO = "fly.io"


@dataclass
class ServiceConfig:
    """Configuration for a service"""
    name: str
    image: Optional[str] = None
    build_context: Optional[str] = None
    ports: List[str] = field(default_factory=list)
    environment: Dict[str, str] = field(default_factory=dict)
    volumes: List[str] = field(default_factory=list)
    depends_on: List[str] = field(default_factory=list)
    healthcheck: Optional[Dict[str, Any]] = None
    replicas: int = 1
    resources: Optional[Dict[str, Any]] = None


@dataclass
class DeploymentConfig:
    """Complete deployment configuration"""
    target: DeploymentTarget
    services: List[ServiceConfig]
    networks: List[str] = field(default_factory=list)
    volumes: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    secrets: List[str] = field(default_factory=list)
    config_maps: Dict[str, Dict[str, str]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class DeploymentConfigGenerator:
    """Generates deployment configurations for various platforms"""
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.detected_services: List[ServiceConfig] = []
        self.deployment_configs: Dict[DeploymentTarget, DeploymentConfig] = {}
        
    def analyze_project(self) -> Dict[str, Any]:
        """Analyze project structure and detect services"""
        logger.info("🔍 Analyzing project for deployment configuration...")
        
        analysis = {
            'services': [],
            'frameworks': [],
            'databases': [],
            'requires_build': False,
            'static_assets': False,
            'api_services': False
        }
        
        # Detect frontend services
        if (self.project_path / 'package.json').exists():
            try:
                package_json = json.loads((self.project_path / 'package.json').read_text())
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse package.json: {e}")
                package_json = {}
            
            # Check for frontend frameworks
            deps = {**package_json.get('dependencies', {}), **package_json.get('devDependencies', {})}
            
            if '@angular/core' in deps:
                analysis['frameworks'].append('angular')
                analysis['static_assets'] = True
                analysis['requires_build'] = True
                self._add_angular_service()
            elif 'react' in deps:
                analysis['frameworks'].append('react')
                analysis['static_assets'] = True
                analysis['requires_build'] = True
                self._add_react_service()
            elif 'vue' in deps:
                analysis['frameworks'].append('vue')
                analysis['static_assets'] = True
                analysis['requires_build'] = True
                self._add_vue_service()
            
            # Check for backend frameworks
            if 'express' in deps:
                analysis['frameworks'].append('express')
                analysis['api_services'] = True
                self._add_express_service()
            elif 'fastify' in deps:
                analysis['frameworks'].append('fastify')
                analysis['api_services'] = True
                self._add_fastify_service()
        
        # Detect Python services
        if (self.project_path / 'requirements.txt').exists():
            try:
                requirements = (self.project_path / 'requirements.txt').read_text()
            except Exception as e:
                logger.warning(f"Failed to read requirements.txt: {e}")
                requirements = ""
            
            if 'fastapi' in requirements:
                analysis['frameworks'].append('fastapi')
                analysis['api_services'] = True
                self._add_fastapi_service()
            elif 'django' in requirements:
                analysis['frameworks'].append('django')
                analysis['api_services'] = True
                self._add_django_service()
            elif 'flask' in requirements:
                analysis['frameworks'].append('flask')
                analysis['api_services'] = True
                self._add_flask_service()
        
        # Detect databases
        self._detect_databases(analysis)
        
        analysis['services'] = [s.name for s in self.detected_services]
        return analysis
    
    def _detect_databases(self, analysis: Dict[str, Any]):
        """Detect database requirements"""
        # Check for MongoDB
        if self._check_for_database_usage(['mongodb', 'mongoose', 'pymongo']):
            analysis['databases'].append('mongodb')
            self._add_mongodb_service()
        
        # Check for PostgreSQL
        if self._check_for_database_usage(['postgres', 'pg', 'psycopg', 'sequelize']):
            analysis['databases'].append('postgresql')
            self._add_postgresql_service()
        
        # Check for Redis
        if self._check_for_database_usage(['redis', 'ioredis', 'redis-py']):
            analysis['databases'].append('redis')
            self._add_redis_service()
        
        # Check for MySQL
        if self._check_for_database_usage(['mysql', 'mysql2', 'pymysql']):
            analysis['databases'].append('mysql')
            self._add_mysql_service()
    
    def _check_for_database_usage(self, keywords: List[str]) -> bool:
        """Check if project uses specific database"""
        # Check package.json
        package_json_path = self.project_path / 'package.json'
        if package_json_path.exists():
            content = package_json_path.read_text().lower()
            if any(keyword in content for keyword in keywords):
                return True
        
        # Check requirements.txt
        requirements_path = self.project_path / 'requirements.txt'
        if requirements_path.exists():
            content = requirements_path.read_text().lower()
            if any(keyword in content for keyword in keywords):
                return True
        
        return False
    
    def _add_angular_service(self):
        """Add Angular frontend service"""
        self.detected_services.append(ServiceConfig(
            name="frontend",
            build_context=".",
            ports=["80:80"],
            environment={
                "NODE_ENV": "production"
            },
            healthcheck={
                "test": ["CMD", "curl", "-f", "http://localhost:80"],
                "interval": "30s",
                "timeout": "10s",
                "retries": 3
            }
        ))
    
    def _add_react_service(self):
        """Add React frontend service"""
        self.detected_services.append(ServiceConfig(
            name="frontend",
            build_context=".",
            ports=["3000:3000"],
            environment={
                "NODE_ENV": "production"
            }
        ))
    
    def _add_vue_service(self):
        """Add Vue frontend service"""
        self.detected_services.append(ServiceConfig(
            name="frontend",
            build_context=".",
            ports=["8080:8080"],
            environment={
                "NODE_ENV": "production"
            }
        ))
    
    def _add_express_service(self):
        """Add Express backend service"""
        self.detected_services.append(ServiceConfig(
            name="backend",
            build_context=".",
            ports=["3000:3000"],
            environment={
                "NODE_ENV": "production",
                "PORT": "3000"
            },
            healthcheck={
                "test": ["CMD", "curl", "-f", "http://localhost:3000/health"],
                "interval": "30s",
                "timeout": "10s",
                "retries": 3
            }
        ))
    
    def _add_fastapi_service(self):
        """Add FastAPI backend service"""
        self.detected_services.append(ServiceConfig(
            name="backend",
            build_context=".",
            ports=["8000:8000"],
            environment={
                "ENVIRONMENT": "production",
                "PORT": "8000"
            },
            healthcheck={
                "test": ["CMD", "curl", "-f", "http://localhost:8000/health"],
                "interval": "30s",
                "timeout": "10s",
                "retries": 3
            }
        ))
    
    def _add_mongodb_service(self):
        """Add MongoDB service"""
        self.detected_services.append(ServiceConfig(
            name="mongodb",
            image="mongo:6",
            ports=["27017:27017"],
            environment={
                "MONGO_INITDB_ROOT_USERNAME": "${MONGO_USERNAME:-admin}",
                "MONGO_INITDB_ROOT_PASSWORD": "${MONGO_PASSWORD}"
            },
            volumes=[
                "mongodb_data:/data/db"
            ],
            healthcheck={
                "test": ["CMD", "mongosh", "--eval", "db.adminCommand('ping')"],
                "interval": "10s",
                "timeout": "10s",
                "retries": 5
            }
        ))
    
    def _add_postgresql_service(self):
        """Add PostgreSQL service"""
        self.detected_services.append(ServiceConfig(
            name="postgres",
            image="postgres:15",
            ports=["5432:5432"],
            environment={
                "POSTGRES_DB": "${POSTGRES_DB:-app}",
                "POSTGRES_USER": "${POSTGRES_USER:-postgres}",
                "POSTGRES_PASSWORD": "${POSTGRES_PASSWORD}"
            },
            volumes=[
                "postgres_data:/var/lib/postgresql/data"
            ],
            healthcheck={
                "test": ["CMD-SHELL", "pg_isready -U postgres"],
                "interval": "10s",
                "timeout": "5s",
                "retries": 5
            }
        ))
    
    def _add_redis_service(self):
        """Add Redis service"""
        self.detected_services.append(ServiceConfig(
            name="redis",
            image="redis:7-alpine",
            ports=["6379:6379"],
            volumes=[
                "redis_data:/data"
            ],
            healthcheck={
                "test": ["CMD", "redis-cli", "ping"],
                "interval": "10s",
                "timeout": "5s",
                "retries": 5
            }
        ))
    
    def _add_mysql_service(self):
        """Add MySQL service"""
        self.detected_services.append(ServiceConfig(
            name="mysql",
            image="mysql:8",
            ports=["3306:3306"],
            environment={
                "MYSQL_ROOT_PASSWORD": "${MYSQL_ROOT_PASSWORD}",
                "MYSQL_DATABASE": "${MYSQL_DATABASE:-app}",
                "MYSQL_USER": "${MYSQL_USER:-app}",
                "MYSQL_PASSWORD": "${MYSQL_PASSWORD}"
            },
            volumes=[
                "mysql_data:/var/lib/mysql"
            ],
            healthcheck={
                "test": ["CMD", "mysqladmin", "ping", "-h", "localhost"],
                "interval": "10s",
                "timeout": "5s",
                "retries": 5
            }
        ))
    
    def generate_docker_compose(self) -> str:
        """Generate docker-compose.yml"""
        logger.info("📝 Generating docker-compose.yml...")
        
        compose_config = {
            'version': '3.8',
            'services': {},
            'volumes': {},
            'networks': {
                'app-network': {
                    'driver': 'bridge'
                }
            }
        }
        
        # Add services
        for service in self.detected_services:
            service_config = {
                'container_name': f"app-{service.name}",
                'restart': 'unless-stopped',
                'networks': ['app-network']
            }
            
            if service.image:
                service_config['image'] = service.image
            else:
                service_config['build'] = {
                    'context': service.build_context or '.',
                    'dockerfile': 'Dockerfile'
                }
            
            if service.ports:
                service_config['ports'] = service.ports
            
            if service.environment:
                service_config['environment'] = service.environment
            
            if service.volumes:
                service_config['volumes'] = service.volumes
                # Add volume definitions
                for volume in service.volumes:
                    volume_name = volume.split(':')[0]
                    if not volume.startswith('./') and not volume.startswith('/'):
                        compose_config['volumes'][volume_name] = {}
            
            if service.depends_on:
                service_config['depends_on'] = service.depends_on
            
            if service.healthcheck:
                service_config['healthcheck'] = service.healthcheck
            
            compose_config['services'][service.name] = service_config
        
        # Set dependencies
        self._set_service_dependencies(compose_config['services'])
        
        return yaml.dump(compose_config, default_flow_style=False, sort_keys=False)
    
    def _set_service_dependencies(self, services: Dict[str, Any]):
        """Set service dependencies"""
        # Backend depends on databases
        if 'backend' in services:
            dependencies = []
            for db in ['mongodb', 'postgres', 'mysql', 'redis']:
                if db in services:
                    dependencies.append(db)
            if dependencies:
                services['backend']['depends_on'] = dependencies
        
        # Frontend depends on backend
        if 'frontend' in services and 'backend' in services:
            services['frontend']['depends_on'] = ['backend']
    
    def generate_kubernetes_manifests(self) -> Dict[str, str]:
        """Generate Kubernetes manifests"""
        logger.info("📝 Generating Kubernetes manifests...")
        
        manifests = {}
        
        # Generate namespace
        manifests['namespace.yaml'] = yaml.dump({
            'apiVersion': 'v1',
            'kind': 'Namespace',
            'metadata': {
                'name': 'app'
            }
        })
        
        # Generate deployments and services
        for service in self.detected_services:
            # Deployment
            deployment = {
                'apiVersion': 'apps/v1',
                'kind': 'Deployment',
                'metadata': {
                    'name': service.name,
                    'namespace': 'app'
                },
                'spec': {
                    'replicas': service.replicas,
                    'selector': {
                        'matchLabels': {
                            'app': service.name
                        }
                    },
                    'template': {
                        'metadata': {
                            'labels': {
                                'app': service.name
                            }
                        },
                        'spec': {
                            'containers': [{
                                'name': service.name,
                                'image': service.image or f"app/{service.name}:latest",
                                'ports': self._parse_ports_for_k8s(service.ports),
                                'env': self._env_to_k8s_format(service.environment)
                            }]
                        }
                    }
                }
            }
            
            # Add resources if specified
            if service.resources:
                deployment['spec']['template']['spec']['containers'][0]['resources'] = service.resources
            
            manifests[f'{service.name}-deployment.yaml'] = yaml.dump(deployment)
            
            # Service
            if service.ports:
                k8s_service = {
                    'apiVersion': 'v1',
                    'kind': 'Service',
                    'metadata': {
                        'name': service.name,
                        'namespace': 'app'
                    },
                    'spec': {
                        'selector': {
                            'app': service.name
                        },
                        'ports': self._parse_service_ports_for_k8s(service.ports),
                        'type': 'ClusterIP'
                    }
                }
                
                # Expose frontend services
                if service.name == 'frontend':
                    k8s_service['spec']['type'] = 'LoadBalancer'
                
                manifests[f'{service.name}-service.yaml'] = yaml.dump(k8s_service)
        
        return manifests
    
    def _parse_ports_for_k8s(self, ports: List[str]) -> List[Dict[str, Any]]:
        """Parse port mappings for Kubernetes containers"""
        k8s_ports = []
        for port in ports:
            container_port = int(port.split(':')[1] if ':' in port else port)
            k8s_ports.append({
                'containerPort': container_port
            })
        return k8s_ports
    
    def _parse_service_ports_for_k8s(self, ports: List[str]) -> List[Dict[str, Any]]:
        """Parse port mappings for Kubernetes services"""
        k8s_ports = []
        for port in ports:
            if ':' in port:
                host_port, container_port = port.split(':')
                k8s_ports.append({
                    'port': int(host_port),
                    'targetPort': int(container_port)
                })
            else:
                k8s_ports.append({
                    'port': int(port),
                    'targetPort': int(port)
                })
        return k8s_ports
    
    def _env_to_k8s_format(self, environment: Dict[str, str]) -> List[Dict[str, str]]:
        """Convert environment dict to Kubernetes format"""
        return [{'name': k, 'value': v} for k, v in environment.items()]
    
    def generate_dockerfile(self, service_name: str) -> str:
        """Generate Dockerfile for a service"""
        logger.info(f"📝 Generating Dockerfile for {service_name}...")
        
        # Detect service type
        if (self.project_path / 'package.json').exists():
            return self._generate_node_dockerfile(service_name)
        elif (self.project_path / 'requirements.txt').exists():
            return self._generate_python_dockerfile(service_name)
        else:
            logger.warning(f"Could not detect framework for {service_name}")
            return ""
    
    def _generate_node_dockerfile(self, service_name: str) -> str:
        """Generate Dockerfile for Node.js service"""
        is_frontend = service_name == 'frontend'
        
        if is_frontend:
            return '''# Build stage
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
'''
        else:
            return '''FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
EXPOSE 3000
CMD ["node", "server.js"]
'''
    
    def _generate_python_dockerfile(self, service_name: str) -> str:
        """Generate Dockerfile for Python service"""
        return '''FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
'''
    
    def generate_deployment_files(self) -> Dict[str, str]:
        """Generate all deployment files"""
        logger.info("🚀 Generating deployment configuration files...")
        
        files = {}
        
        # Generate docker-compose.yml
        files['docker-compose.yml'] = self.generate_docker_compose()
        
        # Generate Dockerfiles
        for service in self.detected_services:
            if not service.image:  # Only for services that need building
                dockerfile_content = self.generate_dockerfile(service.name)
                if dockerfile_content:
                    files[f'Dockerfile.{service.name}'] = dockerfile_content
        
        # Generate .dockerignore
        files['.dockerignore'] = self._generate_dockerignore()
        
        # Generate Kubernetes manifests
        k8s_manifests = self.generate_kubernetes_manifests()
        for filename, content in k8s_manifests.items():
            files[f'k8s/{filename}'] = content
        
        # Generate deployment scripts
        files['deploy.sh'] = self._generate_deploy_script()
        
        return files
    
    def _generate_dockerignore(self) -> str:
        """Generate .dockerignore file"""
        return '''node_modules
.env
.env.local
.git
.gitignore
*.log
dist
build
coverage
.vscode
.idea
__pycache__
*.pyc
.pytest_cache
.DS_Store
'''
    
    def _generate_deploy_script(self) -> str:
        """Generate deployment script"""
        return '''#!/bin/bash
set -e

echo "🚀 Deploying application..."

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Build and start services
docker-compose build
docker-compose up -d

echo "✅ Deployment complete!"
echo "📊 View logs: docker-compose logs -f"
echo "🛑 Stop services: docker-compose down"
'''
    
    def save_deployment_files(self):
        """Save all deployment files to project"""
        files = self.generate_deployment_files()
        
        for filepath, content in files.items():
            full_path = self.project_path / filepath
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)
            
            # Make scripts executable
            if filepath.endswith('.sh'):
                os.chmod(full_path, 0o755)
            
            logger.info(f"Created {filepath}")
        
        logger.info("✅ Deployment configuration files generated successfully!")