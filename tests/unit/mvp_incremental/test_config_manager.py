"""
Unit tests for ConfigManager
"""

import pytest
from pathlib import Path
import tempfile
import shutil
from workflows.mvp_incremental.config_manager import ConfigManager, ConfigType, ConfigVariable


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_project(temp_project_dir):
    """Create a sample project with environment variables"""
    # Create a Node.js file with env vars
    node_file = temp_project_dir / "server.js"
    node_file.write_text("""
const express = require('express');
const port = process.env.PORT || 3000;
const dbUrl = process.env.DATABASE_URL;
const apiKey = process.env.API_KEY;
const jwtSecret = process.env.JWT_SECRET;
const enableDebug = process.env.ENABLE_DEBUG;
""")
    
    # Create a Python file with env vars
    python_file = temp_project_dir / "config.py"
    python_file.write_text("""
import os

DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
SECRET_KEY = os.getenv('SECRET_KEY')
AWS_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY')
""")
    
    return temp_project_dir


class TestConfigManager:
    
    def test_initialization(self, temp_project_dir):
        """Test ConfigManager initialization"""
        config_manager = ConfigManager(temp_project_dir)
        assert config_manager.project_path == temp_project_dir
        assert config_manager.config_vars == {}
        assert config_manager.secrets == set()
    
    def test_scan_for_env_vars(self, sample_project):
        """Test scanning for environment variables"""
        config_manager = ConfigManager(sample_project)
        config_manager._scan_for_env_vars()
        
        # Check Node.js env vars were found
        assert 'PORT' in config_manager.config_vars
        assert 'DATABASE_URL' in config_manager.config_vars
        assert 'API_KEY' in config_manager.config_vars
        assert 'JWT_SECRET' in config_manager.config_vars
        assert 'ENABLE_DEBUG' in config_manager.config_vars
        
        # Check Python env vars were found
        assert 'DB_HOST' in config_manager.config_vars
        assert 'DB_PORT' in config_manager.config_vars
        assert 'SECRET_KEY' in config_manager.config_vars
        assert 'AWS_ACCESS_KEY' in config_manager.config_vars
    
    def test_infer_config_types(self, sample_project):
        """Test inferring configuration types"""
        config_manager = ConfigManager(sample_project)
        config_manager._scan_for_env_vars()
        config_manager._infer_config_types()
        
        # Check type inference
        assert config_manager.config_vars['PORT'].config_type == ConfigType.PORT
        assert config_manager.config_vars['DATABASE_URL'].config_type == ConfigType.URL
        assert config_manager.config_vars['API_KEY'].config_type == ConfigType.SECRET
        assert config_manager.config_vars['JWT_SECRET'].config_type == ConfigType.SECRET
        assert config_manager.config_vars['ENABLE_DEBUG'].config_type == ConfigType.BOOLEAN
        
        # Check secrets are marked
        assert config_manager.config_vars['API_KEY'].is_secret
        assert config_manager.config_vars['JWT_SECRET'].is_secret
        assert config_manager.config_vars['SECRET_KEY'].is_secret
        assert 'API_KEY' in config_manager.secrets
    
    def test_validation_patterns(self, sample_project):
        """Test validation patterns are set correctly"""
        config_manager = ConfigManager(sample_project)
        config_manager._scan_for_env_vars()
        config_manager._infer_config_types()
        
        # Check validation patterns
        port_var = config_manager.config_vars['PORT']
        assert port_var.validation_pattern == r'^\d{1,5}$'
        assert port_var.examples == ['3000', '8080', '5432']
        
        url_var = config_manager.config_vars['DATABASE_URL']
        assert url_var.validation_pattern == r'^https?://'
        assert 'http://localhost:3000' in url_var.examples
        
        bool_var = config_manager.config_vars['ENABLE_DEBUG']
        assert bool_var.validation_pattern == r'^(true|false|1|0|yes|no)$'
        assert bool_var.examples == ['true', 'false']
    
    def test_validate_configuration(self, sample_project):
        """Test configuration validation"""
        config_manager = ConfigManager(sample_project)
        config_manager._scan_for_env_vars()
        config_manager._infer_config_types()
        
        # Add a secret with default value (should trigger error)
        config_manager.config_vars['API_KEY'].default = 'default-key'
        
        errors = config_manager._validate_configuration()
        
        # Should have error about secret with default value
        assert any('API_KEY should not have a default value' in error for error in errors)
        
        # Should have errors about required variables without defaults
        expected_required = ['DATABASE_URL', 'JWT_SECRET', 'SECRET_KEY']
        for var_name in expected_required:
            assert any(f'Required variable {var_name}' in error for error in errors)
    
    def test_generate_env_example(self, sample_project):
        """Test .env.example generation"""
        config_manager = ConfigManager(sample_project)
        config_manager._scan_for_env_vars()
        config_manager._infer_config_types()
        
        # Generate .env.example
        env_example_path = sample_project / '.env.example'
        config_manager._generate_env_example(env_example_path)
        
        assert env_example_path.exists()
        content = env_example_path.read_text()
        
        # Check sections are created
        assert '# PORT Configuration' in content
        assert '# URL Configuration' in content
        assert '# SECRET Configuration' in content
        
        # Check variables are included
        assert 'PORT=' in content
        assert 'DATABASE_URL=' in content
        assert 'API_KEY=<secret>' in content
        assert 'JWT_SECRET=<secret>' in content
    
    def test_generate_deployment_configs(self, sample_project):
        """Test deployment configuration generation"""
        config_manager = ConfigManager(sample_project)
        config_manager._scan_for_env_vars()
        config_manager._infer_config_types()
        
        deployment_configs = config_manager._generate_deployment_configs()
        
        # Check Docker config
        assert 'docker' in deployment_configs
        docker_config = deployment_configs['docker']
        assert docker_config['env_file'] == '.env'
        assert 'PORT' in docker_config['build_args']
        assert 'API_KEY' not in docker_config['build_args']  # Secrets excluded
        
        # Check Kubernetes config
        assert 'kubernetes' in deployment_configs
        k8s_config = deployment_configs['kubernetes']
        assert 'API_KEY' in k8s_config['secrets']
        assert 'JWT_SECRET' in k8s_config['secrets']
        
        # Check Docker Compose config
        assert 'docker-compose' in deployment_configs
        compose_config = deployment_configs['docker-compose']
        assert 'PORT' in compose_config['environment']
        assert 'DATABASE_URL' in compose_config['environment']
    
    def test_generate_warnings(self, sample_project):
        """Test warning generation"""
        config_manager = ConfigManager(sample_project)
        config_manager._scan_for_env_vars()
        config_manager._infer_config_types()
        
        # Add a potential secret not marked as such
        config_manager.config_vars['AUTH_TOKEN'] = ConfigVariable(
            name='AUTH_TOKEN',
            config_type=ConfigType.STRING,
            is_secret=False
        )
        
        warnings = config_manager._generate_warnings()
        
        # Should warn about undocumented variables
        assert any('Variables without descriptions' in warning for warning in warnings)
        
        # Should warn about potential secrets
        assert any('AUTH_TOKEN' in warning for warning in warnings)
    
    def test_analyze_project(self, sample_project):
        """Test full project analysis"""
        config_manager = ConfigManager(sample_project)
        report = config_manager.analyze_project()
        
        # Check report structure
        assert len(report.env_variables) > 0
        assert len(report.secrets) > 0
        assert isinstance(report.deployment_configs, dict)
        assert isinstance(report.validation_errors, list)
        assert isinstance(report.warnings, list)
        assert isinstance(report.generated_files, list)
        
        # Check files were generated
        assert (sample_project / '.env.example').exists()
        assert (sample_project / '.env.local').exists()
        
        # Check secrets are separated
        secret_names = {s.name for s in report.secrets}
        assert 'API_KEY' in secret_names
        assert 'JWT_SECRET' in secret_names
        assert 'SECRET_KEY' in secret_names
        
        # Check non-secrets
        env_names = {e.name for e in report.env_variables}
        assert 'PORT' in env_names
        assert 'DATABASE_URL' in env_names
        assert 'API_KEY' not in env_names  # Should be in secrets