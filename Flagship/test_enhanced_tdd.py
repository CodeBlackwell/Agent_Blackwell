#!/usr/bin/env python3
"""Test script for Enhanced TDD Workflow"""

import asyncio
import sys
from pathlib import Path

# Add paths
flagship_path = Path(__file__).parent
sys.path.insert(0, str(flagship_path))
sys.path.insert(0, str(flagship_path.parent))

from workflows.tdd_orchestrator.enhanced_orchestrator import EnhancedTDDOrchestrator
from workflows.tdd_orchestrator.enhanced_models import EnhancedTDDOrchestratorConfig


async def test_enhanced_tdd():
    """Test the enhanced TDD workflow"""
    
    print("🧪 Testing Enhanced TDD Workflow")
    print("=" * 80)
    
    # Test requirements
    test_cases = [
        "create a calculator app with a front end and back end",
        # "create a REST API for user management",
        # "build a todo list application",
    ]
    
    for requirements in test_cases:
        print(f"\n📝 Testing with: {requirements}")
        print("-" * 60)
        
        # Configure
        config = EnhancedTDDOrchestratorConfig(
            enable_requirements_analysis=True,
            enable_architecture_planning=True,
            enable_feature_validation=False,  # Skip validation for now
            multi_file_support=True,
            feature_based_implementation=True,
            verbose_output=True,
            max_phase_retries=1,  # Reduce retries for testing
            max_total_retries=3
        )
        
        # Create orchestrator
        orchestrator = EnhancedTDDOrchestrator(config)
        
        try:
            # Execute
            result = await orchestrator.execute_feature(requirements)
            
            # Check results
            print(f"\n✅ Workflow completed")
            print(f"   Success: {result.success}")
            print(f"   Duration: {result.total_duration_seconds:.2f}s")
            
            if result.expanded_requirements:
                print(f"   Features: {len(result.expanded_requirements.features)}")
                
            if result.architecture:
                print(f"   Architecture: {result.architecture.project_type}")
                print(f"   Components: {len(result.architecture.components)}")
                
            if result.generated_files:
                print(f"   Files: {len(result.generated_files)}")
                
            if result.errors:
                print(f"   ⚠️ Errors: {len(result.errors)}")
                for error in result.errors:
                    print(f"      - {error}")
                    
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("✅ Test completed")


async def test_individual_components():
    """Test individual components of the enhanced workflow"""
    
    print("\n🧪 Testing Individual Components")
    print("=" * 80)
    
    # Test Planner Agent
    print("\n1️⃣ Testing Planner Agent")
    from agents.planner_flagship import PlannerFlagship
    
    planner = PlannerFlagship()
    output = []
    async for chunk in planner.analyze_requirements("create a calculator app with a front end and back end"):
        output.append(chunk)
    
    expanded = planner.get_expanded_requirements()
    print(f"   ✅ Planner produced {len(expanded.get('features', []))} features")
    
    # Test Designer Agent
    print("\n2️⃣ Testing Designer Agent")
    from agents.designer_flagship import DesignerFlagship
    
    designer = DesignerFlagship()
    output = []
    async for chunk in designer.design_architecture(
        "create a calculator app with a front end and back end",
        expanded
    ):
        output.append(chunk)
    
    architecture = designer.get_architecture()
    print(f"   ✅ Designer created {len(architecture.get('components', []))} components")
    
    # Test Feature-based Test Generator
    print("\n3️⃣ Testing Feature-based Test Generator")
    from workflows.tdd_orchestrator.feature_based_test_generator import FeatureBasedTestGenerator
    from workflows.tdd_orchestrator.enhanced_models import TestableFeature, EnhancedAgentContext, EnhancedTDDPhase
    
    test_gen = FeatureBasedTestGenerator()
    test_feature = TestableFeature(
        id="test_1",
        title="Calculator Operations",
        description="Basic calculator operations",
        components=["add function", "subtract function", "multiply function"],
        test_criteria=[],
        complexity="Medium"
    )
    
    context = EnhancedAgentContext(
        phase=EnhancedTDDPhase.RED,
        feature_id="test_1",
        feature_description="Calculator operations",
        attempt_number=1,
        previous_attempts=[],
        phase_context={},
        global_context={}
    )
    
    test_code = await test_gen.generate_tests_for_feature(test_feature, context)
    print(f"   ✅ Test generator created {len(test_code.splitlines())} lines of test code")
    
    # Test Project Structure Manager
    print("\n4️⃣ Testing Project Structure Manager")
    from workflows.tdd_orchestrator.project_structure_manager import ProjectStructureManager
    from workflows.tdd_orchestrator.enhanced_models import ProjectArchitecture
    
    manager = ProjectStructureManager(base_output_dir="./test_generated")
    
    # Clean up test directory if it exists
    test_dir = Path("./test_generated")
    if test_dir.exists():
        import shutil
        shutil.rmtree(test_dir)
    
    # Create test architecture
    from workflows.tdd_orchestrator.enhanced_models import ArchitectureComponent
    test_arch = ProjectArchitecture(
        project_type="test_app",
        structure={"src": ["main.py"], "tests": ["test_main.py"]},
        technology_stack={"backend": "Python"},
        components=[
            ArchitectureComponent(
                name="Test Component",
                type="backend",
                description="Test",
                files=["main.py"]
            )
        ]
    )
    
    project_path = manager.setup_project_structure(test_arch)
    print(f"   ✅ Project structure created at: {project_path}")
    
    # Clean up
    if test_dir.exists():
        shutil.rmtree(test_dir)
    
    print("\n✅ All component tests passed")


async def main():
    """Run all tests"""
    
    # Test components first
    await test_individual_components()
    
    # Then test full workflow
    await test_enhanced_tdd()


if __name__ == "__main__":
    asyncio.run(main())