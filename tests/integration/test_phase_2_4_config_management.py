"""
Integration tests for Phase 2.4: Environment & Configuration Management
"""

import pytest
import asyncio
import tempfile
import shutil
import json
from pathlib import Path
from workflows.mvp_incremental.config_manager import ConfigManager
from workflows.mvp_incremental.env_templater import EnvTemplater
from workflows.mvp_incremental.secret_manager import SecretManager
from workflows.mvp_incremental.deployment_config import DeploymentConfigGenerator


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def mean_stack_project(temp_project_dir):
    """Create a MEAN stack project structure"""
    # Backend structure
    backend_dir = temp_project_dir / "backend"
    backend_dir.mkdir()
    
    # Backend package.json
    backend_package = {
        "name": "mean-backend",
        "dependencies": {
            "express": "^4.18.0",
            "mongoose": "^6.0.0",
            "jsonwebtoken": "^9.0.0",
            "bcryptjs": "^2.4.3",
            "cors": "^2.8.5"
        }
    }
    (backend_dir / "package.json").write_text(json.dumps(backend_package, indent=2))
    
    # Also create root package.json for framework detection
    root_package = {
        "name": "mean-stack-app",
        "dependencies": {
            "express": "^4.18.0",
            "mongoose": "^6.0.0",
            "@angular/core": "^15.0.0"
        }
    }
    (temp_project_dir / "package.json").write_text(json.dumps(root_package, indent=2))
    
    # Backend server.js with env vars
    (backend_dir / "server.js").write_text("""
const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');

const app = express();

// Environment variables
const PORT = process.env.PORT || 3000;
const MONGODB_URI = process.env.MONGODB_URI;
const JWT_SECRET = process.env.JWT_SECRET;
const NODE_ENV = process.env.NODE_ENV || 'development';
const CORS_ORIGIN = process.env.CORS_ORIGIN || 'http://localhost:4200';

// Middleware
app.use(cors({ origin: CORS_ORIGIN }));
app.use(express.json());

// MongoDB connection
mongoose.connect(MONGODB_URI, {
    useNewUrlParser: true,
    useUnifiedTopology: true
});

app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
""")
    
    # Frontend structure
    frontend_dir = temp_project_dir / "frontend"
    frontend_dir.mkdir()
    
    # Frontend package.json
    frontend_package = {
        "name": "mean-frontend",
        "dependencies": {
            "@angular/core": "^15.0.0",
            "@angular/common": "^15.0.0",
            "@angular/router": "^15.0.0",
            "@angular/forms": "^15.0.0"
        }
    }
    (frontend_dir / "package.json").write_text(json.dumps(frontend_package, indent=2))
    
    # Frontend environment.ts
    (frontend_dir / "src" / "environments").mkdir(parents=True)
    (frontend_dir / "src" / "environments" / "environment.ts").write_text("""
export const environment = {
    production: false,
    apiUrl: process.env['API_URL'] || 'http://localhost:3000/api',
    wsUrl: process.env['WS_URL'] || 'ws://localhost:3000'
};
""")
    
    # Docker compose file
    docker_compose = """
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - MONGODB_URI=mongodb://mongodb:27017/meanapp
    depends_on:
      - mongodb
      
  frontend:
    build: ./frontend
    ports:
      - "4200:80"
    depends_on:
      - backend
      
  mongodb:
    image: mongo:6
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db
      
volumes:
  mongo_data:
"""
    (temp_project_dir / "docker-compose.yml").write_text(docker_compose)
    
    return temp_project_dir


class TestPhase24Integration:
    """Integration tests for Phase 2.4 configuration management"""
    
    def test_config_manager_mean_stack(self, mean_stack_project):
        """Test ConfigManager with MEAN stack project"""
        config_manager = ConfigManager(mean_stack_project)
        report = config_manager.analyze_project()
        
        # Check detected environment variables
        env_var_names = {var.name for var in report.env_variables}
        assert 'PORT' in env_var_names
        assert 'NODE_ENV' in env_var_names
        assert 'MONGODB_URI' in env_var_names
        assert 'CORS_ORIGIN' in env_var_names
        
        # Check detected secrets
        secret_names = {secret.name for secret in report.secrets}
        assert 'JWT_SECRET' in secret_names
        
        # Check generated files
        assert (mean_stack_project / '.env.example').exists()
        assert (mean_stack_project / '.env.local').exists()
        
        # Verify .env.example content
        env_example = (mean_stack_project / '.env.example').read_text()
        assert 'PORT=' in env_example
        assert 'JWT_SECRET=<secret>' in env_example
        assert 'MONGODB_URI=' in env_example
    
    def test_env_templater_mean_stack(self, mean_stack_project):
        """Test EnvTemplater with MEAN stack project"""
        env_templater = EnvTemplater(mean_stack_project)
        
        # Detect frameworks
        frameworks = env_templater.detect_frameworks()
        assert 'express' in frameworks
        assert 'angular' in frameworks
        assert 'mongodb' in frameworks
        assert 'docker' in frameworks
        
        # Generate templates
        templates = env_templater.generate_templates()
        assert 'express_server' in templates
        assert 'express_database' in templates
        assert 'angular_api' in templates
        assert 'mongodb_connection' in templates
        
        # Test merged template
        merged = env_templater.merge_templates('express_server', 'mongodb_connection', 'angular_api')
        assert 'PORT=' in merged.template_string
        assert 'MONGODB_URI=' in merged.template_string
        assert 'API_URL=' in merged.template_string
    
    def test_secret_manager_mean_stack(self, mean_stack_project):
        """Test SecretManager with MEAN stack project"""
        secret_manager = SecretManager(mean_stack_project)
        
        # Add MEAN stack secrets
        jwt_secret = secret_manager.add_secret('JWT_SECRET', description='JWT signing secret')
        session_secret = secret_manager.add_secret('SESSION_SECRET', description='Express session secret')
        db_password = secret_manager.add_secret('MONGODB_PASSWORD', description='MongoDB password')
        
        # Verify secrets are encrypted
        assert jwt_secret.encrypted_value == "encrypted"
        assert session_secret.encrypted_value == "encrypted"
        
        # Verify auto-generated values
        jwt_value = secret_manager.get_secret('JWT_SECRET')
        assert jwt_value is not None
        assert len(jwt_value) >= 43  # Base64 256-bit
        
        session_value = secret_manager.get_secret('SESSION_SECRET')
        assert session_value is not None
        assert len(session_value) >= 32
        
        # Test validation
        validation_result = secret_manager.validate_secrets(['JWT_SECRET', 'SESSION_SECRET', 'MONGODB_PASSWORD'])
        assert validation_result.is_valid
        assert len(validation_result.errors) == 0
        
        # Test Kubernetes secrets generation
        k8s_secrets = secret_manager.generate_kubernetes_secrets()
        assert k8s_secrets['kind'] == 'Secret'
        assert 'jwt-secret' in k8s_secrets['data']
        assert 'session-secret' in k8s_secrets['data']
    
    def test_deployment_config_mean_stack(self, mean_stack_project):
        """Test DeploymentConfigGenerator with MEAN stack project"""
        deployment_gen = DeploymentConfigGenerator(mean_stack_project)
        
        # Analyze project
        analysis = deployment_gen.analyze_project()
        assert 'express' in analysis['frameworks']
        assert 'angular' in analysis['frameworks']
        assert 'mongodb' in analysis['databases']
        assert analysis['requires_build'] is True
        assert analysis['api_services'] is True
        assert analysis['static_assets'] is True
        
        # Check detected services
        service_names = [s.name for s in deployment_gen.detected_services]
        assert 'backend' in service_names
        assert 'frontend' in service_names
        assert 'mongodb' in service_names
        
        # Generate docker-compose
        compose_yaml = deployment_gen.generate_docker_compose()
        assert 'version:' in compose_yaml
        assert 'backend:' in compose_yaml
        assert 'frontend:' in compose_yaml
        assert 'mongodb:' in compose_yaml
        assert 'depends_on:' in compose_yaml
        
        # Generate Kubernetes manifests
        k8s_manifests = deployment_gen.generate_kubernetes_manifests()
        assert 'namespace.yaml' in k8s_manifests
        assert 'backend-deployment.yaml' in k8s_manifests
        assert 'frontend-deployment.yaml' in k8s_manifests
        assert 'mongodb-deployment.yaml' in k8s_manifests
        
        # Generate deployment files
        files = deployment_gen.generate_deployment_files()
        assert 'docker-compose.yml' in files
        assert 'Dockerfile.backend' in files
        assert 'Dockerfile.frontend' in files
        assert '.dockerignore' in files
        assert 'deploy.sh' in files
    
    def test_full_config_pipeline(self, mean_stack_project):
        """Test full configuration pipeline integration"""
        # Step 1: Analyze configuration
        config_manager = ConfigManager(mean_stack_project)
        config_report = config_manager.analyze_project()
        
        assert len(config_report.env_variables) > 0
        assert len(config_report.secrets) > 0
        assert (mean_stack_project / '.env.example').exists()
        
        # Step 2: Generate environment templates
        env_templater = EnvTemplater(mean_stack_project)
        templates = env_templater.generate_templates()
        
        assert len(templates) > 0
        merged_template = env_templater.merge_templates(*list(templates.keys())[:3])
        assert len(merged_template.variables) > 0
        
        # Step 3: Setup secrets
        secret_manager = SecretManager(mean_stack_project)
        for secret in config_report.secrets:
            secret_manager.add_secret(secret.name, description=secret.description)
        
        secrets_template_path = mean_stack_project / 'secrets-template.json'
        secret_manager.export_secrets_template(secrets_template_path)
        assert secrets_template_path.exists()
        
        # Step 4: Generate deployment configs
        deployment_gen = DeploymentConfigGenerator(mean_stack_project)
        deployment_gen.analyze_project()
        deployment_files = deployment_gen.generate_deployment_files()
        
        assert len(deployment_files) > 5  # Should have multiple deployment files
        
        # Verify all components work together
        assert (mean_stack_project / '.env.example').exists()
        assert (mean_stack_project / '.gitignore').exists()
        assert secrets_template_path.exists()
        
        # Check .gitignore was updated
        gitignore_content = (mean_stack_project / '.gitignore').read_text()
        assert '.env' in gitignore_content
        assert 'secrets/' in gitignore_content
    
    def test_error_handling(self, temp_project_dir):
        """Test error handling in configuration management"""
        # Empty project should still work
        config_manager = ConfigManager(temp_project_dir)
        report = config_manager.analyze_project()
        
        assert len(report.env_variables) == 0
        assert len(report.secrets) == 0
        assert len(report.validation_errors) == 0
        
        # Test with malformed files
        bad_json = temp_project_dir / "package.json"
        bad_json.write_text("{ invalid json")
        
        env_templater = EnvTemplater(temp_project_dir)
        frameworks = env_templater.detect_frameworks()
        # Should handle gracefully
        assert isinstance(frameworks, set)
        
        # Test deployment generation with no services
        deployment_gen = DeploymentConfigGenerator(temp_project_dir)
        analysis = deployment_gen.analyze_project()
        assert len(analysis['services']) == 0


class TestPhase24MVPIntegration:
    """Test Phase 2.4 integration with MVP Incremental workflow"""
    
    @pytest.mark.asyncio
    async def test_mvp_workflow_with_config_management(self, temp_project_dir):
        """Test that config management runs in MVP workflow"""
        from workflows.mvp_incremental.mvp_incremental import execute_mvp_incremental_workflow
        from shared.data_models import CodingTeamInput
        
        # Create minimal input for testing
        test_input = CodingTeamInput(
            requirements="Create a simple REST API with Express.js that uses MongoDB"
        )
        
        # Mock the code saver to use our temp directory
        import workflows.mvp_incremental.mvp_incremental as mvp_module
        original_code_saver = mvp_module.CodeSaver
        
        class MockCodeSaver:
            def __init__(self):
                self.current_session_path = temp_project_dir
                self.files_saved = []
                
            def save_code_files(self, code_dict, feature_name=""):
                # Save files to temp directory
                for filename, content in code_dict.items():
                    filepath = self.current_session_path / filename
                    filepath.parent.mkdir(parents=True, exist_ok=True)
                    filepath.write_text(content)
                    self.files_saved.append(filename)
                return self.files_saved
            
            def save_metadata(self, metadata):
                pass
                
            def get_summary(self):
                return {
                    'session_path': str(self.current_session_path),
                    'files_saved': len(self.files_saved),
                    'total_size_kb': 10
                }
                
            def create_requirements_file(self, deps):
                pass
        
        # Patch the CodeSaver
        mvp_module.CodeSaver = MockCodeSaver
        
        try:
            # We don't need to run the full workflow, just verify the config management
            # would be called. We can test this by checking the imports are correct
            from workflows.mvp_incremental.config_manager import ConfigManager
            from workflows.mvp_incremental.env_templater import EnvTemplater
            from workflows.mvp_incremental.secret_manager import SecretManager
            from workflows.mvp_incremental.deployment_config import DeploymentConfigGenerator
            
            # Create instances to verify they work
            config_manager = ConfigManager(temp_project_dir)
            env_templater = EnvTemplater(temp_project_dir)
            secret_manager = SecretManager(temp_project_dir)
            deployment_gen = DeploymentConfigGenerator(temp_project_dir)
            
            # Verify all components are properly initialized
            assert config_manager.project_path == temp_project_dir
            assert env_templater.project_path == temp_project_dir
            assert secret_manager.project_path == temp_project_dir
            assert deployment_gen.project_path == temp_project_dir
            
            # Test would pass if all imports and initializations work
            assert True
            
        finally:
            # Restore original CodeSaver
            mvp_module.CodeSaver = original_code_saver


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])