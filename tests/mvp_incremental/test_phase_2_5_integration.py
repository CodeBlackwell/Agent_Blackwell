"""
Integration tests for Phase 2.5: Full integration of all Phase 2 features.

This test suite validates that all Phase 2 components (project structure, build pipeline,
multi-container support, and configuration management) work together seamlessly.
"""

import pytest
import asyncio
import tempfile
import shutil
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional
import subprocess
import time

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from workflows.mvp_incremental.build_manager import BuildManager
from workflows.mvp_incremental.config_manager import ConfigManager
from workflows.mvp_incremental.env_templater import EnvTemplater
from workflows.mvp_incremental.secret_manager import SecretManager
from workflows.mvp_incremental.deployment_config import DeploymentConfigGenerator
from workflows.validator.docker_compose_manager import DockerComposeManager
from workflows.validator.enhanced_validator import EnhancedValidator


class TestPhase25Integration:
    """Integration tests for all Phase 2 features working together."""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory."""
        temp_dir = tempfile.mkdtemp(prefix="phase_2_5_test_")
        yield Path(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def create_mean_project(self, temp_project_dir):
        """Create a minimal MEAN stack project structure for testing."""
        # Backend structure
        backend_dir = temp_project_dir / "backend"
        backend_src = backend_dir / "src"
        backend_src.mkdir(parents=True)
        
        # Backend package.json
        backend_package = {
            "name": "mean-backend",
            "version": "1.0.0",
            "scripts": {
                "build": "tsc",
                "start": "node dist/server.js",
                "dev": "nodemon src/server.ts",
                "test": "jest"
            },
            "dependencies": {
                "express": "^4.18.0",
                "mongoose": "^6.0.0",
                "jsonwebtoken": "^9.0.0",
                "dotenv": "^16.0.0",
                "cors": "^2.8.5"
            },
            "devDependencies": {
                "typescript": "^4.9.0",
                "@types/express": "^4.17.0",
                "jest": "^29.0.0",
                "nodemon": "^2.0.0"
            }
        }
        (backend_dir / "package.json").write_text(json.dumps(backend_package, indent=2))
        
        # Backend tsconfig.json
        tsconfig = {
            "compilerOptions": {
                "target": "ES2020",
                "module": "commonjs",
                "outDir": "./dist",
                "rootDir": "./src",
                "strict": true,
                "esModuleInterop": true
            }
        }
        (backend_dir / "tsconfig.json").write_text(json.dumps(tsconfig, indent=2))
        
        # Backend server.ts
        server_code = """
import express from 'express';
import mongoose from 'mongoose';
import cors from 'cors';
import dotenv from 'dotenv';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3000;
const MONGODB_URI = process.env.MONGODB_URI || 'mongodb://localhost:27017/meanapp';

app.use(cors());
app.use(express.json());

app.get('/api/health', (req, res) => {
    res.json({ status: 'ok' });
});

mongoose.connect(MONGODB_URI)
    .then(() => {
        console.log('Connected to MongoDB');
        app.listen(PORT, () => {
            console.log(`Server running on port ${PORT}`);
        });
    })
    .catch(err => console.error('MongoDB connection error:', err));
"""
        (backend_src / "server.ts").write_text(server_code)
        
        # Backend Dockerfile
        backend_dockerfile = """FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["node", "dist/server.js"]
"""
        (backend_dir / "Dockerfile").write_text(backend_dockerfile)
        
        # Frontend structure
        frontend_dir = temp_project_dir / "frontend"
        frontend_src = frontend_dir / "src"
        frontend_app = frontend_src / "app"
        frontend_app.mkdir(parents=True)
        
        # Frontend package.json
        frontend_package = {
            "name": "mean-frontend",
            "version": "1.0.0",
            "scripts": {
                "ng": "ng",
                "start": "ng serve",
                "build": "ng build",
                "test": "ng test"
            },
            "dependencies": {
                "@angular/animations": "^15.0.0",
                "@angular/common": "^15.0.0",
                "@angular/core": "^15.0.0",
                "@angular/forms": "^15.0.0",
                "@angular/material": "^15.0.0",
                "@angular/platform-browser": "^15.0.0",
                "@angular/router": "^15.0.0",
                "rxjs": "^7.5.0",
                "tslib": "^2.3.0",
                "zone.js": "^0.11.4"
            },
            "devDependencies": {
                "@angular-devkit/build-angular": "^15.0.0",
                "@angular/cli": "^15.0.0",
                "@angular/compiler-cli": "^15.0.0",
                "typescript": "~4.8.0"
            }
        }
        (frontend_dir / "package.json").write_text(json.dumps(frontend_package, indent=2))
        
        # Frontend angular.json
        angular_json = {
            "$schema": "./node_modules/@angular/cli/lib/config/schema.json",
            "version": 1,
            "newProjectRoot": "projects",
            "projects": {
                "mean-frontend": {
                    "projectType": "application",
                    "root": "",
                    "sourceRoot": "src",
                    "architect": {
                        "build": {
                            "builder": "@angular-devkit/build-angular:browser",
                            "options": {
                                "outputPath": "dist/mean-frontend",
                                "index": "src/index.html",
                                "main": "src/main.ts"
                            }
                        }
                    }
                }
            }
        }
        (frontend_dir / "angular.json").write_text(json.dumps(angular_json, indent=2))
        
        # Frontend Dockerfile
        frontend_dockerfile = """FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist/mean-frontend /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
"""
        (frontend_dir / "Dockerfile").write_text(frontend_dockerfile)
        
        # Docker Compose
        docker_compose = {
            "version": "3.8",
            "services": {
                "backend": {
                    "build": "./backend",
                    "ports": ["3000:3000"],
                    "environment": {
                        "NODE_ENV": "production",
                        "MONGODB_URI": "mongodb://mongodb:27017/meanapp"
                    },
                    "depends_on": ["mongodb"]
                },
                "frontend": {
                    "build": "./frontend",
                    "ports": ["4200:80"],
                    "depends_on": ["backend"]
                },
                "mongodb": {
                    "image": "mongo:6",
                    "ports": ["27017:27017"],
                    "volumes": ["mongo_data:/data/db"]
                }
            },
            "volumes": {
                "mongo_data": {}
            }
        }
        docker_compose_path = temp_project_dir / "docker-compose.yml"
        with open(docker_compose_path, "w") as f:
            yaml.dump(docker_compose, f)
        
        return temp_project_dir
    
    def test_all_phase_2_components_exist(self):
        """Test that all Phase 2 components are properly imported and available."""
        # Phase 2.1: Project Structure (handled by workflow)
        
        # Phase 2.2: Build Pipeline
        assert BuildManager is not None, "BuildManager should be available"
        
        # Phase 2.3: Multi-Container Support
        assert DockerComposeManager is not None, "DockerComposeManager should be available"
        assert EnhancedValidator is not None, "EnhancedValidator should be available"
        
        # Phase 2.4: Configuration Management
        assert ConfigManager is not None, "ConfigManager should be available"
        assert EnvTemplater is not None, "EnvTemplater should be available"
        assert SecretManager is not None, "SecretManager should be available"
        assert DeploymentConfigGenerator is not None, "DeploymentConfigGenerator should be available"
        
        print("✅ All Phase 2 components are available")
    
    def test_build_manager_integration(self, create_mean_project):
        """Test BuildManager integration with MEAN project."""
        project_path = create_mean_project
        
        # Initialize BuildManager
        build_manager = BuildManager(project_path)
        
        # Detect build requirements
        build_reqs = build_manager.detect_build_requirements()
        
        assert len(build_reqs) > 0, "Should detect build requirements"
        
        # Check for TypeScript build in backend
        backend_builds = [b for b in build_reqs if b.project_dir == "backend" and b.build_type == "typescript"]
        assert len(backend_builds) > 0, "Should detect TypeScript build for backend"
        
        # Check for Angular build in frontend
        frontend_builds = [b for b in build_reqs if b.project_dir == "frontend" and b.build_type == "angular"]
        assert len(frontend_builds) > 0, "Should detect Angular build for frontend"
        
        print(f"✅ BuildManager detected {len(build_reqs)} build requirements")
    
    def test_config_manager_integration(self, create_mean_project):
        """Test ConfigManager integration with MEAN project."""
        project_path = create_mean_project
        
        # Initialize ConfigManager
        config_manager = ConfigManager(project_path)
        
        # Analyze project
        report = config_manager.analyze_project()
        
        # Check detected environment variables
        env_var_names = [var.name for var in report.env_variables]
        assert "PORT" in env_var_names, "Should detect PORT environment variable"
        assert "MONGODB_URI" in env_var_names, "Should detect MONGODB_URI environment variable"
        
        # Check generated files
        assert (project_path / ".env.example").exists(), ".env.example should be created"
        assert (project_path / ".gitignore").exists(), ".gitignore should be created"
        
        print(f"✅ ConfigManager detected {len(report.env_variables)} environment variables")
    
    def test_env_templater_integration(self, create_mean_project):
        """Test EnvTemplater integration with MEAN project."""
        project_path = create_mean_project
        
        # Initialize EnvTemplater
        env_templater = EnvTemplater(project_path)
        
        # Detect frameworks
        frameworks = env_templater.detect_frameworks()
        assert "express" in frameworks, "Should detect Express framework"
        assert "angular" in frameworks, "Should detect Angular framework"
        assert "mongodb" in frameworks, "Should detect MongoDB"
        assert "docker" in frameworks, "Should detect Docker"
        
        # Generate templates
        templates = env_templater.generate_templates()
        assert len(templates) > 0, "Should generate environment templates"
        
        print(f"✅ EnvTemplater detected frameworks: {frameworks}")
    
    def test_deployment_config_integration(self, create_mean_project):
        """Test DeploymentConfigGenerator integration with MEAN project."""
        project_path = create_mean_project
        
        # Initialize DeploymentConfigGenerator
        deployment_gen = DeploymentConfigGenerator(project_path)
        
        # Analyze project
        analysis = deployment_gen.analyze_project()
        
        assert "express" in analysis["frameworks"], "Should detect Express framework"
        assert "angular" in analysis["frameworks"], "Should detect Angular framework"
        assert "mongodb" in analysis["databases"], "Should detect MongoDB database"
        assert analysis["requires_build"] is True, "Should require build"
        assert analysis["api_services"] is True, "Should have API services"
        assert analysis["static_assets"] is True, "Should have static assets"
        
        # Check detected services
        service_names = [s.name for s in deployment_gen.detected_services]
        assert "backend" in service_names, "Should detect backend service"
        assert "frontend" in service_names, "Should detect frontend service"
        assert "mongodb" in service_names, "Should detect MongoDB service"
        
        print(f"✅ DeploymentConfigGenerator detected services: {service_names}")
    
    def test_docker_compose_manager_integration(self, create_mean_project):
        """Test DockerComposeManager integration with MEAN project."""
        project_path = create_mean_project
        compose_file = project_path / "docker-compose.yml"
        
        # Initialize DockerComposeManager
        compose_manager = DockerComposeManager(str(compose_file))
        
        # Parse compose file
        success = compose_manager.parse_compose_file()
        assert success, "Should successfully parse docker-compose.yml"
        
        # Check services
        services = compose_manager.get_services()
        assert "backend" in services, "Should have backend service"
        assert "frontend" in services, "Should have frontend service"
        assert "mongodb" in services, "Should have MongoDB service"
        
        # Check dependencies
        deps = compose_manager.get_service_dependencies()
        assert "mongodb" in deps.get("backend", []), "Backend should depend on MongoDB"
        assert "backend" in deps.get("frontend", []), "Frontend should depend on backend"
        
        print(f"✅ DockerComposeManager parsed {len(services)} services")
    
    def test_secret_manager_integration(self, create_mean_project):
        """Test SecretManager integration with configuration."""
        project_path = create_mean_project
        
        # Initialize SecretManager
        secret_manager = SecretManager(project_path)
        
        # Add secrets based on detected needs
        jwt_secret = secret_manager.add_secret("JWT_SECRET", description="JWT signing secret")
        mongo_password = secret_manager.add_secret("MONGODB_PASSWORD", description="MongoDB password")
        
        # Verify secrets are created
        assert jwt_secret is not None, "JWT secret should be created"
        assert mongo_password is not None, "MongoDB password should be created"
        
        # Verify auto-generation
        jwt_value = secret_manager.get_secret("JWT_SECRET")
        assert jwt_value is not None, "JWT secret should have auto-generated value"
        assert len(jwt_value) >= 32, "JWT secret should be sufficiently long"
        
        print("✅ SecretManager created and encrypted secrets")
    
    def test_full_phase_2_pipeline(self, create_mean_project):
        """Test the complete Phase 2 pipeline working together."""
        project_path = create_mean_project
        
        print("\n🔄 Testing Full Phase 2 Pipeline Integration")
        
        # Step 1: Configuration Analysis
        print("\n📋 Step 1: Analyzing configuration...")
        config_manager = ConfigManager(project_path)
        config_report = config_manager.analyze_project()
        assert len(config_report.env_variables) > 0, "Should detect environment variables"
        print(f"  ✅ Detected {len(config_report.env_variables)} environment variables")
        
        # Step 2: Environment Templating
        print("\n📋 Step 2: Generating environment templates...")
        env_templater = EnvTemplater(project_path)
        templates = env_templater.generate_templates()
        assert len(templates) > 0, "Should generate templates"
        print(f"  ✅ Generated {len(templates)} environment templates")
        
        # Step 3: Secret Management
        print("\n📋 Step 3: Setting up secrets...")
        secret_manager = SecretManager(project_path)
        for secret in config_report.secrets:
            secret_manager.add_secret(secret.name, description=secret.description)
        print(f"  ✅ Created {len(config_report.secrets)} secrets")
        
        # Step 4: Build Detection
        print("\n📋 Step 4: Detecting build requirements...")
        build_manager = BuildManager(project_path)
        build_reqs = build_manager.detect_build_requirements()
        assert len(build_reqs) >= 2, "Should detect at least 2 build requirements (backend & frontend)"
        print(f"  ✅ Detected {len(build_reqs)} build requirements")
        
        # Step 5: Deployment Configuration
        print("\n📋 Step 5: Generating deployment configurations...")
        deployment_gen = DeploymentConfigGenerator(project_path)
        deployment_gen.analyze_project()
        deployment_files = deployment_gen.generate_deployment_files()
        assert len(deployment_files) > 5, "Should generate multiple deployment files"
        print(f"  ✅ Generated {len(deployment_files)} deployment files")
        
        # Step 6: Docker Compose Validation
        print("\n📋 Step 6: Validating Docker Compose...")
        compose_manager = DockerComposeManager(str(project_path / "docker-compose.yml"))
        assert compose_manager.parse_compose_file(), "Should parse docker-compose.yml"
        assert compose_manager.validate_compose_file(), "Docker Compose should be valid"
        print("  ✅ Docker Compose configuration is valid")
        
        # Step 7: Enhanced Validation
        print("\n📋 Step 7: Testing enhanced validation...")
        validator = EnhancedValidator(container_cleanup=True)
        # Note: We won't actually run containers in unit tests
        print("  ✅ Enhanced validator initialized successfully")
        
        print("\n✅ Full Phase 2 Pipeline Integration Test Passed!")
    
    def test_phase_2_performance_metrics(self, create_mean_project):
        """Test performance metrics for Phase 2 operations."""
        project_path = create_mean_project
        
        print("\n⏱️  Testing Phase 2 Performance Metrics")
        
        metrics = {}
        
        # Measure configuration analysis time
        start_time = time.time()
        config_manager = ConfigManager(project_path)
        config_manager.analyze_project()
        metrics["config_analysis"] = time.time() - start_time
        
        # Measure build detection time
        start_time = time.time()
        build_manager = BuildManager(project_path)
        build_manager.detect_build_requirements()
        metrics["build_detection"] = time.time() - start_time
        
        # Measure deployment generation time
        start_time = time.time()
        deployment_gen = DeploymentConfigGenerator(project_path)
        deployment_gen.analyze_project()
        deployment_gen.generate_deployment_files()
        metrics["deployment_generation"] = time.time() - start_time
        
        print("\nPerformance Metrics:")
        for operation, duration in metrics.items():
            print(f"  • {operation}: {duration:.3f}s")
        
        # Assert performance targets
        assert metrics["config_analysis"] < 5.0, "Config analysis should complete in < 5 seconds"
        assert metrics["build_detection"] < 2.0, "Build detection should complete in < 2 seconds"
        assert metrics["deployment_generation"] < 5.0, "Deployment generation should complete in < 5 seconds"
        
        print("\n✅ All performance targets met!")
    
    def test_phase_2_error_handling(self, temp_project_dir):
        """Test error handling across Phase 2 components."""
        print("\n🛡️  Testing Phase 2 Error Handling")
        
        # Test with empty project
        config_manager = ConfigManager(temp_project_dir)
        report = config_manager.analyze_project()
        assert report is not None, "Should handle empty project gracefully"
        assert len(report.env_variables) == 0, "Should return empty list for no env vars"
        
        # Test with malformed files
        bad_package = temp_project_dir / "package.json"
        bad_package.write_text("{ invalid json")
        
        env_templater = EnvTemplater(temp_project_dir)
        frameworks = env_templater.detect_frameworks()
        assert isinstance(frameworks, set), "Should handle malformed JSON gracefully"
        
        # Test with missing docker-compose
        compose_manager = DockerComposeManager(str(temp_project_dir / "docker-compose.yml"))
        assert not compose_manager.parse_compose_file(), "Should handle missing file"
        
        print("✅ Error handling working correctly across all components")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])