"""
Unit tests for EnvTemplater
"""

import pytest
import json
from pathlib import Path
import tempfile
import shutil
from workflows.mvp_incremental.env_templater import EnvTemplater, EnvTemplate


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def node_project(temp_project_dir):
    """Create a Node.js project"""
    package_json = {
        "name": "test-app",
        "dependencies": {
            "express": "^4.18.0",
            "mongodb": "^4.5.0",
            "redis": "^4.0.0"
        },
        "devDependencies": {
            "@angular/core": "^15.0.0"
        }
    }
    (temp_project_dir / "package.json").write_text(json.dumps(package_json))
    return temp_project_dir


@pytest.fixture
def python_project(temp_project_dir):
    """Create a Python project"""
    requirements = """
fastapi==0.95.0
redis==4.5.0
psycopg2-binary==2.9.5
pymongo==4.3.0
"""
    (temp_project_dir / "requirements.txt").write_text(requirements)
    return temp_project_dir


@pytest.fixture
def docker_project(temp_project_dir):
    """Create a project with Docker files"""
    dockerfile = """
FROM node:18
WORKDIR /app
COPY . .
CMD ["npm", "start"]
"""
    (temp_project_dir / "Dockerfile").write_text(dockerfile)
    
    docker_compose = """
version: '3.8'
services:
  app:
    build: .
"""
    (temp_project_dir / "docker-compose.yml").write_text(docker_compose)
    return temp_project_dir


class TestEnvTemplater:
    
    def test_initialization(self, temp_project_dir):
        """Test EnvTemplater initialization"""
        templater = EnvTemplater(temp_project_dir)
        assert templater.project_path == temp_project_dir
        assert templater.templates == {}
        assert templater.detected_frameworks == set()
    
    def test_detect_node_frameworks(self, node_project):
        """Test Node.js framework detection"""
        templater = EnvTemplater(node_project)
        frameworks = templater.detect_frameworks()
        
        assert 'express' in frameworks
        assert 'angular' in frameworks
        assert 'mongodb' in frameworks
        assert 'redis' not in frameworks  # Redis package doesn't mean Redis framework
    
    def test_detect_python_frameworks(self, python_project):
        """Test Python framework detection"""
        templater = EnvTemplater(python_project)
        frameworks = templater.detect_frameworks()
        
        assert 'fastapi' in frameworks
        assert 'redis' in frameworks
        assert 'postgresql' in frameworks
        assert 'mongodb' in frameworks
    
    def test_detect_docker(self, docker_project):
        """Test Docker detection"""
        templater = EnvTemplater(docker_project)
        frameworks = templater.detect_frameworks()
        
        assert 'docker' in frameworks
    
    def test_extract_variables(self, temp_project_dir):
        """Test variable extraction from template"""
        templater = EnvTemplater(temp_project_dir)
        
        template_string = """
PORT=${PORT:-3000}
DATABASE_URL=${DATABASE_URL}
API_KEY=${API_KEY:-default-key}
"""
        
        variables = templater._extract_variables(template_string)
        
        assert len(variables) == 3
        assert variables['PORT']['default'] == '3000'
        assert variables['PORT']['required'] is False
        assert variables['DATABASE_URL']['default'] is None
        assert variables['DATABASE_URL']['required'] is True
        assert variables['API_KEY']['default'] == 'default-key'
    
    def test_generate_templates(self, node_project):
        """Test template generation"""
        templater = EnvTemplater(node_project)
        templates = templater.generate_templates()
        
        # Should have templates for detected frameworks
        assert 'express_server' in templates
        assert 'express_database' in templates
        assert 'mongodb_connection' in templates
        assert 'angular_api' in templates
        
        # Check express server template
        express_template = templates['express_server']
        assert 'PORT' in express_template.variables
        assert 'NODE_ENV' in express_template.variables
        assert 'DATABASE_URL' in express_template.variables
    
    def test_merge_templates(self, node_project):
        """Test merging multiple templates"""
        templater = EnvTemplater(node_project)
        templater.generate_templates()
        
        # Merge express and mongodb templates
        merged = templater.merge_templates('express_server', 'mongodb_connection')
        
        # Check merged content
        assert 'PORT=' in merged.template_string
        assert 'MONGODB_URI=' in merged.template_string
        
        # Check merged variables
        assert 'PORT' in merged.variables
        assert 'MONGODB_URI' in merged.variables
    
    def test_generate_env_file(self, temp_project_dir):
        """Test environment file generation"""
        templater = EnvTemplater(temp_project_dir)
        
        template = EnvTemplate(
            template_string="PORT=${PORT:-3000}\nAPI_KEY=${API_KEY}",
            variables={
                'PORT': {'name': 'PORT', 'default': '3000', 'required': False},
                'API_KEY': {'name': 'API_KEY', 'default': None, 'required': True}
            }
        )
        
        output_path = temp_project_dir / '.env.test'
        values = {'API_KEY': 'test-key-123'}
        
        templater.generate_env_file(template, output_path, values)
        
        assert output_path.exists()
        content = output_path.read_text()
        assert 'PORT=${PORT:-3000}' in content
        assert 'API_KEY=test-key-123' in content
    
    def test_validate_template(self, temp_project_dir):
        """Test template validation"""
        templater = EnvTemplater(temp_project_dir)
        
        template = EnvTemplate(
            template_string="",
            variables={
                'PORT': {'name': 'PORT', 'default': None, 'required': True},
                'API_KEY': {'name': 'API_KEY', 'default': None, 'required': True}
            }
        )
        
        # Create an env file missing required variable
        env_file = temp_project_dir / '.env'
        env_file.write_text("PORT=3000")
        
        errors = templater.validate_template(template, env_file)
        
        assert len(errors) == 1
        assert 'Missing required variable: API_KEY' in errors[0]
    
    def test_generate_docker_env_file(self, temp_project_dir):
        """Test Docker environment file generation"""
        templater = EnvTemplater(temp_project_dir)
        
        template = EnvTemplate(
            template_string="",
            variables={
                'PORT': {'name': 'PORT', 'default': '3000', 'required': False},
                'API_KEY': {'name': 'API_KEY', 'default': None, 'required': True}
            }
        )
        
        docker_env = templater.generate_docker_env_file(template)
        
        assert 'PORT=3000' in docker_env
        assert '# API_KEY=' in docker_env
    
    def test_custom_pattern_analysis(self, temp_project_dir):
        """Test custom environment pattern analysis"""
        # Create files with custom env vars
        (temp_project_dir / "app.js").write_text("""
const config = {
    customVar: process.env.CUSTOM_VAR,
    featureFlag: process.env.FEATURE_FLAG,
    authEndpoint: process.env.AUTH_ENDPOINT
};
""")
        
        templater = EnvTemplater(temp_project_dir)
        custom_templates = templater._analyze_custom_patterns()
        
        # Should create custom templates
        assert len(custom_templates) > 0
        
        # Check that custom variables are captured
        all_vars = set()
        for template in custom_templates.values():
            all_vars.update(template.variables.keys())
        
        assert 'CUSTOM_VAR' in all_vars
        assert 'FEATURE_FLAG' in all_vars
        assert 'AUTH_ENDPOINT' in all_vars
    
    def test_group_env_vars(self, temp_project_dir):
        """Test environment variable grouping"""
        templater = EnvTemplater(temp_project_dir)
        
        env_vars = {
            'JWT_SECRET', 'AUTH_TOKEN', 'DATABASE_URL', 'DB_HOST',
            'SMTP_HOST', 'EMAIL_API_KEY', 'S3_BUCKET', 'CACHE_TTL',
            'SENTRY_DSN', 'RANDOM_VAR'
        }
        
        groups = templater._group_env_vars(env_vars)
        
        assert 'auth' in groups
        assert 'JWT_SECRET' in groups['auth']
        assert 'AUTH_TOKEN' in groups['auth']
        assert 'database' in groups
        assert 'DATABASE_URL' in groups['database']
        assert 'DB_HOST' in groups['database']
        assert 'email' in groups
        assert 'SMTP_HOST' in groups['email']
        assert 'EMAIL_API_KEY' in groups['email']
        assert 'storage' in groups
        assert 'S3_BUCKET' in groups['storage']
        assert 'cache' in groups
        assert 'CACHE_TTL' in groups['cache']
        assert 'monitoring' in groups
        assert 'SENTRY_DSN' in groups['monitoring']
        assert 'general' in groups
        assert 'RANDOM_VAR' in groups['general']