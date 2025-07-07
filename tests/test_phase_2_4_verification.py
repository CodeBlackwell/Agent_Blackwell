"""
Verification test for Phase 2.4: Environment & Configuration Management
This test verifies that all Phase 2.4 components are working correctly.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tempfile
import shutil
import json
from pathlib import Path
from workflows.mvp_incremental.config_manager import ConfigManager
from workflows.mvp_incremental.env_templater import EnvTemplater
from workflows.mvp_incremental.secret_manager import SecretManager
from workflows.mvp_incremental.deployment_config import DeploymentConfigGenerator


def create_test_project(project_dir):
    """Create a test MEAN stack project"""
    # Create package.json
    package_json = {
        "name": "test-mean-app",
        "dependencies": {
            "express": "^4.18.0",
            "mongoose": "^6.0.0",
            "jsonwebtoken": "^9.0.0",
            "@angular/core": "^15.0.0"
        }
    }
    (project_dir / "package.json").write_text(json.dumps(package_json, indent=2))
    
    # Create server.js with environment variables
    (project_dir / "server.js").write_text("""
const express = require('express');
const mongoose = require('mongoose');

const PORT = process.env.PORT || 3000;
const MONGODB_URI = process.env.MONGODB_URI;
const JWT_SECRET = process.env.JWT_SECRET;
const API_KEY = process.env.API_KEY;
const SESSION_SECRET = process.env.SESSION_SECRET;

const app = express();

mongoose.connect(MONGODB_URI);

app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
""")
    
    # Create a Python file too
    (project_dir / "config.py").write_text("""
import os

DATABASE_URL = os.getenv('DATABASE_URL')
SECRET_KEY = os.environ.get('SECRET_KEY')
DEBUG = os.getenv('DEBUG', 'False') == 'True'
""")


def test_config_manager():
    """Test ConfigManager functionality"""
    print("\n🧪 Testing ConfigManager...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        project_dir = Path(temp_dir)
        create_test_project(project_dir)
        
        # Test configuration analysis
        config_manager = ConfigManager(project_dir)
        report = config_manager.analyze_project()
        
        print(f"  ✓ Found {len(report.env_variables)} environment variables")
        print(f"  ✓ Found {len(report.secrets)} secrets")
        print(f"  ✓ Generated {len(report.generated_files)} configuration files")
        
        # Verify specific variables were detected
        env_names = {var.name for var in report.env_variables}
        secret_names = {var.name for var in report.secrets}
        
        assert 'PORT' in env_names
        assert 'MONGODB_URI' in env_names
        assert 'JWT_SECRET' in secret_names
        assert 'API_KEY' in secret_names
        assert 'SECRET_KEY' in secret_names
        
        # Verify files were created
        assert (project_dir / '.env.example').exists()
        assert (project_dir / '.env.local').exists()
        
        print("  ✅ ConfigManager tests passed!")
        return True


def test_env_templater():
    """Test EnvTemplater functionality"""
    print("\n🧪 Testing EnvTemplater...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        project_dir = Path(temp_dir)
        create_test_project(project_dir)
        
        # Test framework detection and template generation
        env_templater = EnvTemplater(project_dir)
        frameworks = env_templater.detect_frameworks()
        
        print(f"  ✓ Detected frameworks: {', '.join(frameworks)}")
        
        assert 'express' in frameworks
        assert 'angular' in frameworks
        assert 'mongodb' in frameworks
        
        # Generate templates
        templates = env_templater.generate_templates()
        print(f"  ✓ Generated {len(templates)} templates")
        
        # Test template merging
        if len(templates) >= 2:
            template_names = list(templates.keys())[:2]
            merged = env_templater.merge_templates(*template_names)
            print(f"  ✓ Merged templates with {len(merged.variables)} variables")
        
        print("  ✅ EnvTemplater tests passed!")
        return True


def test_secret_manager():
    """Test SecretManager functionality"""
    print("\n🧪 Testing SecretManager...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        project_dir = Path(temp_dir)
        
        # Test secret management
        secret_manager = SecretManager(project_dir)
        
        # Add and retrieve secrets
        secret_manager.add_secret('JWT_SECRET', description='JWT signing key')
        secret_manager.add_secret('API_KEY', description='API authentication key')
        
        jwt_value = secret_manager.get_secret('JWT_SECRET')
        api_value = secret_manager.get_secret('API_KEY')
        
        assert jwt_value is not None
        assert len(jwt_value) >= 43  # Base64 256-bit
        assert api_value is not None
        assert api_value.startswith('sk_')
        
        print(f"  ✓ Generated JWT secret: {jwt_value[:10]}...")
        print(f"  ✓ Generated API key: {api_value[:15]}...")
        
        # Test validation
        validation = secret_manager.validate_secrets(['JWT_SECRET', 'API_KEY'])
        print(f"  ✓ Validation passed: {validation.is_valid}")
        
        # Test export
        template_path = project_dir / 'secrets.json'
        secret_manager.export_secrets_template(template_path)
        assert template_path.exists()
        print("  ✓ Exported secrets template")
        
        print("  ✅ SecretManager tests passed!")
        return True


def test_deployment_config():
    """Test DeploymentConfigGenerator functionality"""
    print("\n🧪 Testing DeploymentConfigGenerator...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        project_dir = Path(temp_dir)
        create_test_project(project_dir)
        
        # Test deployment configuration generation
        deployment_gen = DeploymentConfigGenerator(project_dir)
        analysis = deployment_gen.analyze_project()
        
        print(f"  ✓ Detected services: {', '.join(analysis['services'])}")
        print(f"  ✓ Detected frameworks: {', '.join(analysis['frameworks'])}")
        print(f"  ✓ Detected databases: {', '.join(analysis['databases'])}")
        
        # Generate docker-compose
        compose_yaml = deployment_gen.generate_docker_compose()
        assert 'version:' in compose_yaml
        assert 'services:' in compose_yaml
        print("  ✓ Generated docker-compose.yml")
        
        # Generate deployment files
        files = deployment_gen.generate_deployment_files()
        print(f"  ✓ Generated {len(files)} deployment files")
        
        assert 'docker-compose.yml' in files
        assert '.dockerignore' in files
        assert 'deploy.sh' in files
        
        print("  ✅ DeploymentConfigGenerator tests passed!")
        return True


def test_integration():
    """Test full integration of all Phase 2.4 components"""
    print("\n🧪 Testing Full Integration...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        project_dir = Path(temp_dir)
        create_test_project(project_dir)
        
        # Step 1: Analyze configuration
        config_manager = ConfigManager(project_dir)
        config_report = config_manager.analyze_project()
        print(f"  ✓ Configuration analysis complete")
        
        # Step 2: Generate environment templates
        env_templater = EnvTemplater(project_dir)
        templates = env_templater.generate_templates()
        print(f"  ✓ Environment templates generated")
        
        # Step 3: Setup secrets
        secret_manager = SecretManager(project_dir)
        for secret in config_report.secrets:
            secret_manager.add_secret(secret.name)
        print(f"  ✓ Secrets configured")
        
        # Step 4: Generate deployment configs
        deployment_gen = DeploymentConfigGenerator(project_dir)
        deployment_gen.analyze_project()
        files = deployment_gen.generate_deployment_files()
        print(f"  ✓ Deployment files generated")
        
        # Verify all files exist
        assert (project_dir / '.env.example').exists()
        assert (project_dir / '.env.local').exists()
        assert (project_dir / '.gitignore').exists()
        
        print("  ✅ Integration test passed!")
        return True


def main():
    """Run all Phase 2.4 verification tests"""
    print("=" * 60)
    print("🚀 Phase 2.4 Verification Tests")
    print("=" * 60)
    
    tests = [
        test_config_manager,
        test_env_templater,
        test_secret_manager,
        test_deployment_config,
        test_integration
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  ❌ {test.__name__} failed: {str(e)}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("\n✅ All Phase 2.4 components are working correctly!")
        return 0
    else:
        print(f"\n❌ {failed} tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())