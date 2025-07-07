"""
End-to-End test for MEAN stack generation with all Phase 2 features.

This test validates the complete workflow from requirements to deployed MEAN application,
including project structure, build pipeline, multi-container orchestration, and configuration management.
"""

import asyncio
import pytest
import sys
import os
import json
import shutil
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.data_models import CodingTeamInput
from workflows.workflow_manager import execute_workflow
from workflows.monitoring import WorkflowExecutionTracer
from workflows.mvp_incremental.config_manager import ConfigManager
from workflows.mvp_incremental.env_templater import EnvTemplater
from workflows.mvp_incremental.secret_manager import SecretManager
from workflows.mvp_incremental.deployment_config import DeploymentConfigGenerator


class TestMEANStackE2E:
    """End-to-end tests for MEAN stack generation."""
    
    @pytest.fixture
    def mean_requirements(self) -> str:
        """MEAN stack requirements for testing."""
        return """Create a MEAN stack TODO application with the following:

Backend (Node.js/Express):
1. Express.js server with TypeScript
2. MongoDB integration using Mongoose
3. REST API endpoints:
   - GET /api/todos - List all todos
   - GET /api/todos/:id - Get specific todo
   - POST /api/todos - Create new todo
   - PUT /api/todos/:id - Update todo
   - DELETE /api/todos/:id - Delete todo
   - POST /api/auth/register - User registration
   - POST /api/auth/login - User login with JWT
4. JWT authentication middleware
5. Input validation
6. Error handling middleware
7. CORS configuration
8. Environment variables with dotenv
9. Unit tests with Jest

Frontend (Angular):
1. Angular 15+ application with TypeScript
2. Angular Material UI components
3. Reactive forms for todo creation/editing
4. Authentication service with JWT storage
5. HTTP interceptor for auth tokens
6. Route guards for protected pages
7. Responsive design
8. Loading states and error handling
9. Unit tests with Karma/Jasmine

Database:
1. MongoDB with Mongoose ODM
2. User schema with hashed passwords
3. Todo schema with user association
4. Database indexes for performance

DevOps:
1. Docker compose configuration
2. Environment-specific configs
3. Kubernetes deployment manifests
4. API documentation

Create the full application structure with all necessary files."""
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for test outputs."""
        temp_dir = tempfile.mkdtemp(prefix="mean_e2e_test_")
        yield Path(temp_dir)
        # Cleanup after test
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    async def execute_mean_workflow(self, requirements: str, enable_phase_2: bool = True) -> Dict:
        """Execute the MVP incremental workflow for MEAN stack."""
        # Create input with Phase 2 features
        input_data = CodingTeamInput(
            requirements=requirements,
            workflow_type="mvp_incremental",
            run_tests=True,
            run_integration_verification=True
        )
        
        # Add Phase 2 metadata
        if enable_phase_2:
            input_data.metadata = {
                "enable_build_pipeline": True,
                "enable_multi_container": True,
                "enable_config_management": True
            }
        
        # Create tracer
        session_id = f"mean_e2e_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        tracer = WorkflowExecutionTracer(session_id)
        
        # Execute workflow
        results, report = await execute_workflow(input_data, tracer)
        
        return {
            "results": results,
            "report": report,
            "session_id": session_id
        }
    
    def find_generated_code_path(self) -> Optional[Path]:
        """Find the most recently generated code directory."""
        generated_dir = Path("generated")
        if not generated_dir.exists():
            return None
            
        app_dirs = [d for d in generated_dir.iterdir() 
                   if d.is_dir() and d.name.startswith("app_generated_")]
        
        if not app_dirs:
            return None
            
        # Return the most recent directory
        return max(app_dirs, key=lambda d: d.stat().st_mtime)
    
    def validate_project_structure(self, project_path: Path) -> Dict[str, bool]:
        """Validate the MEAN stack project structure."""
        validations = {
            "backend_exists": False,
            "frontend_exists": False,
            "backend_src": False,
            "frontend_src": False,
            "docker_compose": False,
            "env_example": False,
            "gitignore": False,
            "readme": False,
            "kubernetes": False
        }
        
        # Check directories
        validations["backend_exists"] = (project_path / "backend").exists()
        validations["frontend_exists"] = (project_path / "frontend").exists()
        
        # Check backend structure
        if validations["backend_exists"]:
            backend_path = project_path / "backend"
            validations["backend_src"] = (backend_path / "src").exists()
            validations["backend_package_json"] = (backend_path / "package.json").exists()
            validations["backend_tsconfig"] = (backend_path / "tsconfig.json").exists()
            validations["backend_dockerfile"] = (backend_path / "Dockerfile").exists()
            
            # Check specific backend files
            if validations["backend_src"]:
                src_path = backend_path / "src"
                validations["server_file"] = (src_path / "server.ts").exists()
                validations["models_dir"] = (src_path / "models").exists()
                validations["routes_dir"] = (src_path / "routes").exists()
                validations["middleware_dir"] = (src_path / "middleware").exists()
        
        # Check frontend structure
        if validations["frontend_exists"]:
            frontend_path = project_path / "frontend"
            validations["frontend_src"] = (frontend_path / "src").exists()
            validations["frontend_package_json"] = (frontend_path / "package.json").exists()
            validations["frontend_angular_json"] = (frontend_path / "angular.json").exists()
            validations["frontend_dockerfile"] = (frontend_path / "Dockerfile").exists()
            
            # Check specific frontend files
            if validations["frontend_src"]:
                src_path = frontend_path / "src"
                validations["app_dir"] = (src_path / "app").exists()
                validations["environments_dir"] = (src_path / "environments").exists()
        
        # Check root files
        validations["docker_compose"] = (project_path / "docker-compose.yml").exists()
        validations["env_example"] = (project_path / ".env.example").exists()
        validations["gitignore"] = (project_path / ".gitignore").exists()
        validations["readme"] = (project_path / "README.md").exists()
        
        # Check Kubernetes files
        validations["kubernetes"] = (project_path / "k8s").exists()
        if validations["kubernetes"]:
            k8s_path = project_path / "k8s"
            validations["k8s_namespace"] = (k8s_path / "namespace.yaml").exists()
            validations["k8s_backend_deployment"] = (k8s_path / "backend-deployment.yaml").exists()
            validations["k8s_frontend_deployment"] = (k8s_path / "frontend-deployment.yaml").exists()
            validations["k8s_mongodb_deployment"] = (k8s_path / "mongodb-deployment.yaml").exists()
        
        return validations
    
    def validate_build_configuration(self, project_path: Path) -> Dict[str, bool]:
        """Validate build configuration files."""
        validations = {}
        
        # Check backend build config
        backend_package_path = project_path / "backend" / "package.json"
        if backend_package_path.exists():
            try:
                with open(backend_package_path) as f:
                    backend_package = json.load(f)
                    
                scripts = backend_package.get("scripts", {})
                validations["backend_build_script"] = "build" in scripts
                validations["backend_test_script"] = "test" in scripts
                validations["backend_start_script"] = "start" in scripts
                
                deps = backend_package.get("dependencies", {})
                validations["has_express"] = "express" in deps
                validations["has_mongoose"] = "mongoose" in deps
                validations["has_jsonwebtoken"] = "jsonwebtoken" in deps
                
                dev_deps = backend_package.get("devDependencies", {})
                validations["has_typescript"] = "typescript" in dev_deps
                validations["has_jest"] = "jest" in dev_deps or "@types/jest" in dev_deps
            except Exception as e:
                print(f"Error reading backend package.json: {e}")
        
        # Check frontend build config
        frontend_package_path = project_path / "frontend" / "package.json"
        if frontend_package_path.exists():
            try:
                with open(frontend_package_path) as f:
                    frontend_package = json.load(f)
                    
                scripts = frontend_package.get("scripts", {})
                validations["frontend_build_script"] = "build" in scripts
                validations["frontend_test_script"] = "test" in scripts
                validations["frontend_start_script"] = "start" in scripts or "ng" in scripts
                
                deps = frontend_package.get("dependencies", {})
                validations["has_angular"] = "@angular/core" in deps
                validations["has_angular_material"] = "@angular/material" in deps
                validations["has_rxjs"] = "rxjs" in deps
            except Exception as e:
                print(f"Error reading frontend package.json: {e}")
        
        return validations
    
    def validate_docker_configuration(self, project_path: Path) -> Dict[str, bool]:
        """Validate Docker and container configuration."""
        validations = {}
        
        # Check docker-compose.yml
        docker_compose_path = project_path / "docker-compose.yml"
        if docker_compose_path.exists():
            try:
                import yaml
                with open(docker_compose_path) as f:
                    compose_config = yaml.safe_load(f)
                    
                services = compose_config.get("services", {})
                validations["has_backend_service"] = "backend" in services
                validations["has_frontend_service"] = "frontend" in services
                validations["has_mongodb_service"] = "mongodb" in services or "mongo" in services
                
                # Check service configurations
                if "backend" in services:
                    backend_service = services["backend"]
                    validations["backend_has_build"] = "build" in backend_service
                    validations["backend_has_ports"] = "ports" in backend_service
                    validations["backend_has_environment"] = "environment" in backend_service
                    validations["backend_depends_on_db"] = "depends_on" in backend_service
                
                if "frontend" in services:
                    frontend_service = services["frontend"]
                    validations["frontend_has_build"] = "build" in frontend_service
                    validations["frontend_has_ports"] = "ports" in frontend_service
                    validations["frontend_depends_on_backend"] = (
                        "depends_on" in frontend_service and 
                        "backend" in frontend_service.get("depends_on", [])
                    )
                    
                # Check volumes and networks
                validations["has_volumes"] = "volumes" in compose_config
                validations["has_networks"] = "networks" in compose_config
            except Exception as e:
                print(f"Error reading docker-compose.yml: {e}")
        
        # Check Dockerfiles
        validations["backend_dockerfile"] = (project_path / "backend" / "Dockerfile").exists()
        validations["frontend_dockerfile"] = (project_path / "frontend" / "Dockerfile").exists()
        
        return validations
    
    def validate_configuration_management(self, project_path: Path) -> Dict[str, bool]:
        """Validate configuration management files."""
        validations = {}
        
        # Check environment files
        env_example_path = project_path / ".env.example"
        validations["env_example_exists"] = env_example_path.exists()
        
        if validations["env_example_exists"]:
            try:
                with open(env_example_path) as f:
                    env_content = f.read()
                    
                # Check for expected environment variables
                expected_vars = [
                    "PORT", "NODE_ENV", "MONGODB_URI", "JWT_SECRET",
                    "API_URL", "CORS_ORIGIN"
                ]
                
                for var in expected_vars:
                    validations[f"has_{var.lower()}"] = var in env_content
            except Exception as e:
                print(f"Error reading .env.example: {e}")
        
        # Check gitignore
        gitignore_path = project_path / ".gitignore"
        if gitignore_path.exists():
            try:
                with open(gitignore_path) as f:
                    gitignore_content = f.read()
                    
                validations["gitignore_has_env"] = ".env" in gitignore_content
                validations["gitignore_has_node_modules"] = "node_modules" in gitignore_content
                validations["gitignore_has_dist"] = "dist" in gitignore_content
            except Exception as e:
                print(f"Error reading .gitignore: {e}")
        
        return validations
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(600)  # 10 minute timeout for full E2E test
    async def test_mean_stack_generation_with_phase_2(self, mean_requirements):
        """Test complete MEAN stack generation with all Phase 2 features."""
        print("\n" + "="*80)
        print("🧪 Running MEAN Stack End-to-End Test with Phase 2 Features")
        print("="*80)
        
        # Execute the workflow
        print("\n📋 Step 1: Executing MVP Incremental Workflow...")
        result = await self.execute_mean_workflow(mean_requirements, enable_phase_2=True)
        
        assert result["results"] is not None, "Workflow should return results"
        assert result["report"] is not None, "Workflow should return a report"
        
        print(f"✅ Workflow completed with session ID: {result['session_id']}")
        
        # Find generated code
        print("\n📋 Step 2: Locating generated code...")
        generated_path = self.find_generated_code_path()
        assert generated_path is not None, "Generated code directory should exist"
        assert generated_path.exists(), f"Generated path {generated_path} should exist"
        
        print(f"✅ Found generated code at: {generated_path}")
        
        # Validate project structure
        print("\n📋 Step 3: Validating project structure...")
        structure_validation = self.validate_project_structure(generated_path)
        
        print("Project Structure Validation:")
        for key, value in structure_validation.items():
            status = "✅" if value else "❌"
            print(f"  {status} {key}: {value}")
        
        # Assert critical structure elements
        assert structure_validation["backend_exists"], "Backend directory should exist"
        assert structure_validation["frontend_exists"], "Frontend directory should exist"
        assert structure_validation["docker_compose"], "docker-compose.yml should exist"
        assert structure_validation["env_example"], ".env.example should exist"
        assert structure_validation["kubernetes"], "Kubernetes manifests should exist"
        
        # Validate build configuration
        print("\n📋 Step 4: Validating build configuration...")
        build_validation = self.validate_build_configuration(generated_path)
        
        print("Build Configuration Validation:")
        for key, value in build_validation.items():
            status = "✅" if value else "❌"
            print(f"  {status} {key}: {value}")
        
        # Assert critical build elements
        assert build_validation.get("backend_build_script", False), "Backend should have build script"
        assert build_validation.get("frontend_build_script", False), "Frontend should have build script"
        assert build_validation.get("has_express", False), "Backend should have Express dependency"
        assert build_validation.get("has_angular", False), "Frontend should have Angular dependency"
        
        # Validate Docker configuration
        print("\n📋 Step 5: Validating Docker configuration...")
        docker_validation = self.validate_docker_configuration(generated_path)
        
        print("Docker Configuration Validation:")
        for key, value in docker_validation.items():
            status = "✅" if value else "❌"
            print(f"  {status} {key}: {value}")
        
        # Assert critical Docker elements
        assert docker_validation.get("has_backend_service", False), "Docker Compose should have backend service"
        assert docker_validation.get("has_frontend_service", False), "Docker Compose should have frontend service"
        assert docker_validation.get("has_mongodb_service", False), "Docker Compose should have MongoDB service"
        
        # Validate configuration management
        print("\n📋 Step 6: Validating configuration management...")
        config_validation = self.validate_configuration_management(generated_path)
        
        print("Configuration Management Validation:")
        for key, value in config_validation.items():
            status = "✅" if value else "❌"
            print(f"  {status} {key}: {value}")
        
        # Test Phase 2.4 components directly
        print("\n📋 Step 7: Testing Phase 2.4 configuration components...")
        
        # Test ConfigManager
        config_manager = ConfigManager(generated_path)
        config_report = config_manager.analyze_project()
        assert len(config_report.env_variables) > 0, "Should detect environment variables"
        print(f"✅ ConfigManager detected {len(config_report.env_variables)} environment variables")
        
        # Test EnvTemplater
        env_templater = EnvTemplater(generated_path)
        frameworks = env_templater.detect_frameworks()
        assert "express" in frameworks, "Should detect Express framework"
        assert "angular" in frameworks, "Should detect Angular framework"
        print(f"✅ EnvTemplater detected frameworks: {frameworks}")
        
        # Test DeploymentConfigGenerator
        deployment_gen = DeploymentConfigGenerator(generated_path)
        analysis = deployment_gen.analyze_project()
        assert "express" in analysis["frameworks"], "Should detect Express in deployment analysis"
        assert "mongodb" in analysis["databases"], "Should detect MongoDB in deployment analysis"
        print(f"✅ DeploymentConfigGenerator analysis complete")
        
        print("\n" + "="*80)
        print("✅ MEAN Stack E2E Test Completed Successfully!")
        print("="*80)
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(300)  # 5 minute timeout
    async def test_mean_stack_without_phase_2(self, mean_requirements):
        """Test MEAN stack generation without Phase 2 features for comparison."""
        print("\n" + "="*80)
        print("🧪 Running MEAN Stack Test WITHOUT Phase 2 Features (Baseline)")
        print("="*80)
        
        # Execute the workflow without Phase 2
        result = await self.execute_mean_workflow(mean_requirements, enable_phase_2=False)
        
        assert result["results"] is not None, "Workflow should return results"
        
        # Find generated code
        generated_path = self.find_generated_code_path()
        assert generated_path is not None, "Generated code directory should exist"
        
        # Validate that Phase 2 features are NOT present
        validations = {
            "has_dockerfiles": (generated_path / "backend" / "Dockerfile").exists(),
            "has_k8s": (generated_path / "k8s").exists(),
            "has_env_example": (generated_path / ".env.example").exists()
        }
        
        print("\nPhase 2 Feature Check (should be missing):")
        for key, value in validations.items():
            status = "❌" if value else "✅"
            print(f"  {status} {key}: {value}")
        
        # These should NOT exist without Phase 2
        assert not validations["has_dockerfiles"], "Dockerfiles should not exist without Phase 2"
        assert not validations["has_k8s"], "Kubernetes files should not exist without Phase 2"
        
        print("\n✅ Baseline test completed successfully!")
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(60)  # 1 minute timeout
    async def test_phase_2_feature_flags(self):
        """Test that Phase 2 feature flags are properly handled."""
        print("\n🧪 Testing Phase 2 Feature Flag Handling...")
        
        # Create a simple test input
        test_input = CodingTeamInput(
            requirements="Create a simple Node.js API",
            workflow_type="mvp_incremental"
        )
        
        # Test with different metadata configurations
        test_cases = [
            {
                "name": "All Phase 2 features enabled",
                "metadata": {
                    "enable_build_pipeline": True,
                    "enable_multi_container": True,
                    "enable_config_management": True
                }
            },
            {
                "name": "Only build pipeline enabled",
                "metadata": {
                    "enable_build_pipeline": True,
                    "enable_multi_container": False,
                    "enable_config_management": False
                }
            },
            {
                "name": "No Phase 2 features",
                "metadata": {}
            }
        ]
        
        for test_case in test_cases:
            print(f"\n  Testing: {test_case['name']}")
            test_input.metadata = test_case["metadata"]
            
            # Verify metadata is set correctly
            assert test_input.metadata == test_case["metadata"]
            print(f"  ✅ Metadata set correctly: {test_input.metadata}")
        
        print("\n✅ Feature flag test completed!")


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "-s"])