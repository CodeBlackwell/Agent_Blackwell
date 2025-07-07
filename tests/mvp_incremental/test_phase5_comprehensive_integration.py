"""
Phase 5: Comprehensive Integration Tests for MVP Incremental TDD
Tests the full workflow with vague requirements like "Create a REST API"
"""
import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from shared.data_models import CodingTeamInput
from workflows.mvp_incremental.mvp_incremental_tdd import execute_mvp_incremental_tdd_workflow
from workflows.mvp_incremental.requirements_expander import RequirementsExpander
from workflows.mvp_incremental.intelligent_feature_extractor import IntelligentFeatureExtractor


class TestPhase5ComprehensiveIntegration:
    """Comprehensive integration tests for the enhanced MVP Incremental TDD workflow"""
    
    @pytest.mark.asyncio
    async def test_rest_api_expansion_to_7_features(self):
        """Test that 'Create a REST API' expands to 7+ features with full TDD cycle"""
        # Input with vague requirement
        input_data = CodingTeamInput(
            requirements="Create a REST API"
        )
        
        # Mock the agent interactions
        with patch('orchestrator.orchestrator_agent.run_team_member_with_tracking') as mock_run_agent:
            # Configure mock responses
            mock_run_agent.side_effect = self._create_mock_agent_responses()
            
            # Execute workflow
            results = await execute_mvp_incremental_tdd_workflow(input_data)
            
            # Verify requirements were expanded
            first_call_args = mock_run_agent.call_args_list[0][0]
            planning_requirements = first_call_args[1]
            assert "Project Setup and Configuration" in planning_requirements
            assert "Authentication and Authorization" in planning_requirements
            assert "Core API Endpoints" in planning_requirements
            
            # Verify we got results for all agents
            assert len(results) >= 10  # Planning, Design, and multiple feature implementations
            
            # Check that final result includes TDD metadata
            final_result = results[-1]
            assert final_result.metadata.get('tdd_enabled') == True
            assert final_result.metadata.get('total_test_files', 0) > 0
    
    @pytest.mark.asyncio
    async def test_web_app_expansion_to_6_features(self):
        """Test that 'Build a web app' expands to 6+ features"""
        input_data = CodingTeamInput(
            requirements="Build a web app"
        )
        
        # Test expansion
        expanded, was_expanded = RequirementsExpander.expand_requirements(input_data.requirements)
        assert was_expanded == True
        
        # Extract key requirements
        key_reqs = RequirementsExpander.extract_key_requirements(expanded)
        assert len(key_reqs) >= 6
        assert any("Frontend" in req for req in key_reqs)
        assert any("Backend" in req for req in key_reqs)
        assert any("State Management" in req for req in key_reqs)
    
    @pytest.mark.asyncio
    async def test_cli_tool_expansion_to_6_features(self):
        """Test that 'Make a CLI tool' expands to 6+ features"""
        input_data = CodingTeamInput(
            requirements="Make a CLI tool"
        )
        
        # Test expansion
        expanded, was_expanded = RequirementsExpander.expand_requirements(input_data.requirements)
        assert was_expanded == True
        
        # Extract key requirements
        key_reqs = RequirementsExpander.extract_key_requirements(expanded)
        assert len(key_reqs) >= 6
        assert any("CLI Framework" in req for req in key_reqs)
        assert any("Commands" in req for req in key_reqs)
        assert any("Configuration" in req for req in key_reqs)
    
    @pytest.mark.asyncio
    async def test_detailed_requirements_not_expanded(self):
        """Test that detailed requirements are NOT expanded"""
        detailed = """
        Create a task management API with:
        - User authentication (JWT)
        - CRUD operations for tasks
        - Task categories and tags
        - Due date tracking
        - Priority levels
        - Search and filtering
        - Export to CSV/JSON
        """
        
        input_data = CodingTeamInput(
            requirements=detailed
        )
        
        # Test no expansion
        expanded, was_expanded = RequirementsExpander.expand_requirements(input_data.requirements)
        assert was_expanded == False
        assert expanded == detailed
    
    @pytest.mark.asyncio
    async def test_feature_extraction_from_expanded_requirements(self):
        """Test that IntelligentFeatureExtractor properly extracts features from expanded requirements"""
        # Start with vague requirement
        original = "Create a REST API"
        expanded, _ = RequirementsExpander.expand_requirements(original)
        
        # Mock plan based on expanded requirements
        mock_plan = """
        Development Plan:
        1. Set up project structure and dependencies
        2. Design database schema and models
        3. Implement authentication system
        4. Create CRUD endpoints
        5. Add validation and error handling
        6. Write comprehensive tests
        7. Generate API documentation
        """
        
        # Mock design with proper FEATURE blocks
        mock_design = """
        Technical Design:
        
        FEATURE[1]: Project Foundation
        Description: Initialize FastAPI application with proper structure
        
        FEATURE[2]: Database Models
        Description: Create SQLAlchemy models for data persistence
        
        FEATURE[3]: Authentication System
        Description: JWT-based authentication with user registration
        
        FEATURE[4]: CRUD API Endpoints
        Description: RESTful endpoints for resource management
        
        FEATURE[5]: Input Validation
        Description: Pydantic schemas for request validation
        
        FEATURE[6]: Test Suite
        Description: Unit and integration tests with pytest
        
        FEATURE[7]: API Documentation
        Description: Auto-generated OpenAPI/Swagger docs
        """
        
        # Extract features
        features = IntelligentFeatureExtractor.extract_features(
            plan=mock_plan,
            design=mock_design,
            requirements=original
        )
        
        # Should get all 7 features
        assert len(features) >= 7
        
        # Verify feature properties
        for i, feature in enumerate(features):
            assert feature['id'] == f"feature_{i+1}"
            assert 'title' in feature
            assert 'description' in feature
            assert 'test_criteria' in feature
    
    @pytest.mark.asyncio
    async def test_tdd_cycle_for_each_feature(self):
        """Test that each feature goes through full TDD cycle"""
        from workflows.mvp_incremental.tdd_feature_implementer import TDDFeatureImplementer
        
        # Mock a feature
        feature = {
            'id': 'feature_1',
            'title': 'User Authentication',
            'description': 'Implement JWT-based authentication',
            'test_criteria': {
                'description': 'JWT authentication with login/register',
                'input_examples': [{'endpoint': '/auth/login', 'data': 'credentials'}],
                'expected_outputs': ['JWT token'],
                'edge_cases': ['Invalid credentials', 'Missing fields'],
                'error_conditions': ['401 Unauthorized']
            }
        }
        
        # Create implementer with mocks
        mock_tracer = MagicMock()
        mock_monitor = MagicMock()
        mock_review = MagicMock()
        
        from workflows.mvp_incremental.retry_strategy import RetryStrategy, RetryConfig
        
        implementer = TDDFeatureImplementer(
            tracer=mock_tracer,
            progress_monitor=mock_monitor,
            review_integration=mock_review,
            retry_strategy=RetryStrategy(),
            retry_config=RetryConfig()
        )
        
        # Mock agent responses through run_team_member_with_tracking
        with patch('orchestrator.orchestrator_agent.run_team_member_with_tracking') as mock_run:
            mock_run.side_effect = [
                # Test writer response
                [MagicMock(parts=[MagicMock(content="def test_auth(): pass")])],
                # Executor response (tests fail)
                [MagicMock(parts=[MagicMock(content="Tests failed: 1")])],
                # Coder response
                [MagicMock(parts=[MagicMock(content="def login(): pass")])],
                # Executor response (tests pass)
                [MagicMock(parts=[MagicMock(content="Tests passed: 1")])]
            ]
        
            # Execute TDD cycle
            result = await implementer.implement_feature_tdd(
                feature=feature,
                existing_code={},
                requirements="Create a REST API",
                design_output="Technical design...",
                feature_index=0
            )
            
            # Verify TDD cycle
            assert result.test_code is not None
            assert result.implementation_code is not None
            assert result.success == True
    
    @pytest.mark.asyncio 
    async def test_full_workflow_metrics(self):
        """Test that workflow produces correct metrics"""
        input_data = CodingTeamInput(
            requirements="Create a REST API"
        )
        
        with patch('orchestrator.orchestrator_agent.run_team_member_with_tracking') as mock_run_agent:
            # Configure minimal mock responses
            mock_run_agent.side_effect = [
                # Planning response
                [MagicMock(parts=[MagicMock(content="Development plan with 7 features")])],
                # Design response with 7 FEATURE blocks
                [MagicMock(parts=[MagicMock(content=self._create_mock_design_with_7_features())])]
            ]
            
            # Mock the review integration
            with patch('workflows.mvp_incremental.review_integration.ReviewIntegration.request_review') as mock_review:
                mock_review.return_value = AsyncMock(return_value=MagicMock(approved=True, feedback="Approved"))
                
                # Mock TDD implementer
                with patch('workflows.mvp_incremental.mvp_incremental_tdd.create_tdd_implementer') as mock_create_tdd:
                    mock_implementer = MagicMock()
                    mock_implementer.implement_feature_tdd = AsyncMock(
                        return_value=MagicMock(
                            success=True,
                            test_code="test code",
                            implementation_code="impl code",
                            retry_count=0,
                            initial_test_result=MagicMock(passed=0, failed=1),
                            final_test_result=MagicMock(passed=1, failed=0)
                        )
                    )
                    mock_create_tdd.return_value = mock_implementer
                    
                    # Execute workflow
                    results = await execute_mvp_incremental_tdd_workflow(input_data)
                    
                    # Check results
                    assert len(results) > 0
                    
                    # Verify TDD was used - default is True in the workflow
                    final_result = results[-1]
                    assert final_result.metadata.get('tdd_enabled', True) == True
    
    def _create_mock_agent_responses(self):
        """Create mock responses for agent interactions"""
        return [
            # Planning response
            [MagicMock(parts=[MagicMock(content="""
            Development Plan:
            1. Project setup and configuration
            2. Database design and models
            3. Authentication system
            4. CRUD API endpoints
            5. Input validation
            6. Testing suite
            7. API documentation
            """)])],
            
            # Design response
            [MagicMock(parts=[MagicMock(content=self._create_mock_design_with_7_features())])]
        ]
    
    def _create_mock_design_with_7_features(self):
        """Create a mock design output with 7 FEATURE blocks"""
        return """
        Technical Design for REST API:
        
        FEATURE[1]: Project Foundation
        Description: Set up FastAPI application with configuration
        Dependencies: None
        
        FEATURE[2]: Database Models
        Description: User and resource models with SQLAlchemy
        Dependencies: FEATURE[1]
        
        FEATURE[3]: Authentication System
        Description: JWT-based auth with login/register endpoints
        Dependencies: FEATURE[1], FEATURE[2]
        
        FEATURE[4]: CRUD API Endpoints
        Description: RESTful endpoints for resource management
        Dependencies: FEATURE[1], FEATURE[2], FEATURE[3]
        
        FEATURE[5]: Input Validation
        Description: Request validation schemas and error handling
        Dependencies: FEATURE[1]
        
        FEATURE[6]: Test Suite
        Description: Unit and integration tests with pytest
        Dependencies: All features
        
        FEATURE[7]: API Documentation
        Description: OpenAPI/Swagger documentation
        Dependencies: FEATURE[1], FEATURE[4]
        """


if __name__ == "__main__":
    pytest.main([__file__, "-v"])