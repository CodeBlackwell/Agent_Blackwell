"""
Environment Variable Templating for MVP Incremental Workflow

Handles creation and management of environment variable templates.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass
from string import Template

from workflows.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class EnvTemplate:
    """Environment variable template"""
    template_string: str
    variables: Dict[str, Any]
    description: Optional[str] = None
    target_file: Optional[str] = None


class EnvTemplater:
    """Manages environment variable templating"""
    
    # Common template patterns for different frameworks
    FRAMEWORK_TEMPLATES = {
        'express': {
            'server': '''PORT=${PORT:-3000}
NODE_ENV=${NODE_ENV:-development}
DATABASE_URL=${DATABASE_URL}
SESSION_SECRET=${SESSION_SECRET}
CORS_ORIGIN=${CORS_ORIGIN:-http://localhost:3000}
''',
            'database': '''DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME}
DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASSWORD}
DB_SSL=${DB_SSL:-false}
''',
            'auth': '''JWT_SECRET=${JWT_SECRET}
JWT_EXPIRES_IN=${JWT_EXPIRES_IN:-7d}
REFRESH_TOKEN_SECRET=${REFRESH_TOKEN_SECRET}
REFRESH_TOKEN_EXPIRES_IN=${REFRESH_TOKEN_EXPIRES_IN:-30d}
''',
        },
        'fastapi': {
            'server': '''PORT=${PORT:-8000}
HOST=${HOST:-0.0.0.0}
ENVIRONMENT=${ENVIRONMENT:-development}
DATABASE_URL=${DATABASE_URL}
SECRET_KEY=${SECRET_KEY}
ALGORITHM=${ALGORITHM:-HS256}
ACCESS_TOKEN_EXPIRE_MINUTES=${ACCESS_TOKEN_EXPIRE_MINUTES:-30}
''',
            'redis': '''REDIS_HOST=${REDIS_HOST:-localhost}
REDIS_PORT=${REDIS_PORT:-6379}
REDIS_PASSWORD=${REDIS_PASSWORD}
REDIS_DB=${REDIS_DB:-0}
''',
        },
        'angular': {
            'api': '''API_URL=${API_URL:-http://localhost:3000/api}
AUTH_URL=${AUTH_URL:-http://localhost:3000/auth}
WEBSOCKET_URL=${WEBSOCKET_URL:-ws://localhost:3000}
''',
            'features': '''ENABLE_ANALYTICS=${ENABLE_ANALYTICS:-false}
ENABLE_DEBUG=${ENABLE_DEBUG:-false}
ENABLE_SERVICE_WORKER=${ENABLE_SERVICE_WORKER:-true}
''',
        },
        'react': {
            'api': '''REACT_APP_API_URL=${REACT_APP_API_URL:-http://localhost:3000/api}
REACT_APP_AUTH_URL=${REACT_APP_AUTH_URL:-http://localhost:3000/auth}
REACT_APP_WEBSOCKET_URL=${REACT_APP_WEBSOCKET_URL:-ws://localhost:3000}
''',
            'features': '''REACT_APP_ENABLE_ANALYTICS=${REACT_APP_ENABLE_ANALYTICS:-false}
REACT_APP_ENABLE_DEBUG=${REACT_APP_ENABLE_DEBUG:-false}
REACT_APP_VERSION=${REACT_APP_VERSION:-1.0.0}
''',
        },
        'mongodb': {
            'connection': '''MONGODB_URI=${MONGODB_URI:-mongodb://localhost:27017}
MONGODB_DB_NAME=${MONGODB_DB_NAME}
MONGODB_USERNAME=${MONGODB_USERNAME}
MONGODB_PASSWORD=${MONGODB_PASSWORD}
MONGODB_AUTH_SOURCE=${MONGODB_AUTH_SOURCE:-admin}
''',
        },
        'postgresql': {
            'connection': '''POSTGRES_HOST=${POSTGRES_HOST:-localhost}
POSTGRES_PORT=${POSTGRES_PORT:-5432}
POSTGRES_DB=${POSTGRES_DB}
POSTGRES_USER=${POSTGRES_USER}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
POSTGRES_SSL_MODE=${POSTGRES_SSL_MODE:-disable}
''',
        },
        'docker': {
            'compose': '''COMPOSE_PROJECT_NAME=${COMPOSE_PROJECT_NAME}
DOCKER_REGISTRY=${DOCKER_REGISTRY}
IMAGE_TAG=${IMAGE_TAG:-latest}
DOCKER_BUILDKIT=${DOCKER_BUILDKIT:-1}
''',
        }
    }
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.templates: Dict[str, EnvTemplate] = {}
        self.detected_frameworks: Set[str] = set()
        
    def detect_frameworks(self) -> Set[str]:
        """Detect frameworks used in the project"""
        logger.info("🔍 Detecting project frameworks...")
        
        # Check package.json for Node.js frameworks
        package_json = self.project_path / 'package.json'
        if package_json.exists():
            try:
                with open(package_json, 'r') as f:
                    package_data = json.load(f)
                    dependencies = {**package_data.get('dependencies', {}), 
                                    **package_data.get('devDependencies', {})}
                    
                    if 'express' in dependencies:
                        self.detected_frameworks.add('express')
                    if '@angular/core' in dependencies:
                        self.detected_frameworks.add('angular')
                    if 'react' in dependencies:
                        self.detected_frameworks.add('react')
                    if 'mongodb' in dependencies or 'mongoose' in dependencies:
                        self.detected_frameworks.add('mongodb')
                    if 'pg' in dependencies:
                        self.detected_frameworks.add('postgresql')
            except Exception as e:
                logger.warning(f"Failed to parse package.json: {e}")
        
        # Check requirements.txt for Python frameworks
        requirements = self.project_path / 'requirements.txt'
        if requirements.exists():
            try:
                content = requirements.read_text()
                if 'fastapi' in content:
                    self.detected_frameworks.add('fastapi')
                if 'redis' in content:
                    self.detected_frameworks.add('redis')
                if 'psycopg' in content or 'postgresql' in content:
                    self.detected_frameworks.add('postgresql')
                if 'pymongo' in content:
                    self.detected_frameworks.add('mongodb')
            except Exception as e:
                logger.warning(f"Failed to read requirements.txt: {e}")
        
        # Check for Docker files
        if (self.project_path / 'docker-compose.yml').exists() or \
           (self.project_path / 'docker-compose.yaml').exists() or \
           (self.project_path / 'Dockerfile').exists():
            self.detected_frameworks.add('docker')
        
        logger.info(f"Detected frameworks: {', '.join(self.detected_frameworks)}")
        return self.detected_frameworks
    
    def generate_templates(self) -> Dict[str, EnvTemplate]:
        """Generate environment templates based on detected frameworks"""
        logger.info("📝 Generating environment templates...")
        
        # Detect frameworks if not already done
        if not self.detected_frameworks:
            self.detect_frameworks()
        
        # Generate templates for each detected framework
        for framework in self.detected_frameworks:
            if framework in self.FRAMEWORK_TEMPLATES:
                for template_name, template_content in self.FRAMEWORK_TEMPLATES[framework].items():
                    key = f"{framework}_{template_name}"
                    self.templates[key] = EnvTemplate(
                        template_string=template_content,
                        variables=self._extract_variables(template_content),
                        description=f"{framework.capitalize()} {template_name} configuration"
                    )
        
        # Add custom templates based on code analysis
        custom_templates = self._analyze_custom_patterns()
        self.templates.update(custom_templates)
        
        return self.templates
    
    def _extract_variables(self, template_string: str) -> Dict[str, Any]:
        """Extract variables from template string"""
        variables = {}
        
        # Pattern to match ${VAR_NAME:-default_value} or ${VAR_NAME}
        pattern = r'\$\{([A-Z_]+)(?::-([^}]*))?\}'
        matches = re.findall(pattern, template_string)
        
        for var_name, default_value in matches:
            variables[var_name] = {
                'name': var_name,
                'default': default_value if default_value else None,
                'required': not bool(default_value)
            }
        
        return variables
    
    def _analyze_custom_patterns(self) -> Dict[str, EnvTemplate]:
        """Analyze codebase for custom environment patterns"""
        custom_templates = {}
        
        # Look for environment variable usage patterns
        env_usage = self._scan_env_usage()
        
        # Group by functional area
        groups = self._group_env_vars(env_usage)
        
        # Create templates for each group
        for group_name, vars in groups.items():
            if vars:
                template_lines = []
                variables = {}
                
                for var in sorted(vars):
                    template_lines.append(f"{var}=${{{var}}}")
                    variables[var] = {
                        'name': var,
                        'default': None,
                        'required': True
                    }
                
                custom_templates[f"custom_{group_name}"] = EnvTemplate(
                    template_string='\n'.join(template_lines),
                    variables=variables,
                    description=f"Custom {group_name} configuration"
                )
        
        return custom_templates
    
    def _scan_env_usage(self) -> Set[str]:
        """Scan codebase for environment variable usage"""
        env_vars = set()
        patterns = [
            r'process\.env\.([A-Z_]+)',
            r'os\.environ\[["\']([A-Z_]+)["\']\]',
            r'os\.getenv\(["\']([A-Z_]+)["\']',
            r'ENV\[["\']([A-Z_]+)["\']\]',
        ]
        
        for file_path in self.project_path.rglob('*'):
            if file_path.is_file() and file_path.suffix in ['.js', '.ts', '.py', '.rb']:
                try:
                    content = file_path.read_text(encoding='utf-8')
                    for pattern in patterns:
                        matches = re.findall(pattern, content)
                        env_vars.update(matches)
                except Exception:
                    pass
        
        return env_vars
    
    def _group_env_vars(self, env_vars: Set[str]) -> Dict[str, Set[str]]:
        """Group environment variables by functional area"""
        groups = {
            'auth': set(),
            'database': set(),
            'api': set(),
            'cache': set(),
            'email': set(),
            'storage': set(),
            'monitoring': set(),
            'general': set()
        }
        
        # Keywords for grouping (order matters - more specific patterns first)
        group_keywords = {
            'email': ['EMAIL', 'SMTP', 'MAIL', 'SENDGRID', 'MAILGUN'],
            'auth': ['AUTH', 'JWT', 'TOKEN', 'SECRET', 'SESSION', 'OAUTH'],
            'database': ['DB', 'DATABASE', 'POSTGRES', 'MYSQL', 'MONGO', 'REDIS'],
            'cache': ['CACHE', 'REDIS', 'MEMCACHED'],
            'storage': ['S3', 'STORAGE', 'BUCKET', 'UPLOAD'],
            'monitoring': ['SENTRY', 'DATADOG', 'NEWRELIC', 'LOG', 'METRICS'],
            'api': ['API', 'ENDPOINT', 'URL', 'HOST', 'PORT'],
        }
        
        for var in env_vars:
            grouped = False
            for group, keywords in group_keywords.items():
                if any(keyword in var for keyword in keywords):
                    groups[group].add(var)
                    grouped = True
                    break
            
            if not grouped:
                groups['general'].add(var)
        
        # Remove empty groups
        return {k: v for k, v in groups.items() if v}
    
    def merge_templates(self, *template_names: str) -> EnvTemplate:
        """Merge multiple templates into one"""
        merged_lines = []
        merged_variables = {}
        descriptions = []
        
        for name in template_names:
            if name in self.templates:
                template = self.templates[name]
                merged_lines.append(f"# {template.description}")
                merged_lines.append(template.template_string)
                merged_lines.append("")
                merged_variables.update(template.variables)
                descriptions.append(template.description)
        
        return EnvTemplate(
            template_string='\n'.join(merged_lines),
            variables=merged_variables,
            description=' + '.join(descriptions) if descriptions else "Merged configuration"
        )
    
    def generate_env_file(self, template: EnvTemplate, output_path: Path, 
                         values: Optional[Dict[str, str]] = None):
        """Generate an environment file from a template"""
        logger.info(f"Generating environment file: {output_path}")
        
        # Apply values if provided
        content = template.template_string
        if values:
            for var_name, value in values.items():
                # Replace ${VAR_NAME} or ${VAR_NAME:-default}
                pattern = f"\\$\\{{{var_name}(?::-[^}}]*)?\\}}"
                content = re.sub(pattern, value, content)
        
        # Write file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content)
        logger.info(f"Created {output_path}")
    
    def validate_template(self, template: EnvTemplate, env_file: Path) -> List[str]:
        """Validate an environment file against a template"""
        errors = []
        
        if not env_file.exists():
            errors.append(f"Environment file {env_file} does not exist")
            return errors
        
        # Parse environment file
        env_vars = {}
        try:
            content = env_file.read_text()
            for line in content.split('\n'):
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
        except Exception as e:
            errors.append(f"Failed to parse environment file: {e}")
            return errors
        
        # Check required variables
        for var_name, var_info in template.variables.items():
            if var_info.get('required', True) and var_name not in env_vars:
                errors.append(f"Missing required variable: {var_name}")
        
        return errors
    
    def generate_docker_env_file(self, template: EnvTemplate) -> str:
        """Generate Docker-compatible environment file content"""
        lines = []
        
        for var_name, var_info in template.variables.items():
            if var_info.get('default'):
                lines.append(f"{var_name}={var_info['default']}")
            else:
                lines.append(f"# {var_name}=")
        
        return '\n'.join(lines)