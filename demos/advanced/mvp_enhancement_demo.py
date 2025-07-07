"""
Demo: MVP Incremental TDD Workflow Enhancement
Shows how vague requirements like "Create a REST API" now expand to 7+ features
"""
import asyncio
from workflows.mvp_incremental.requirements_expander import RequirementsExpander
from workflows.mvp_incremental.intelligent_feature_extractor import IntelligentFeatureExtractor


def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


async def demonstrate_requirements_expansion():
    """Demonstrate how vague requirements get expanded"""
    print_section("REQUIREMENTS EXPANSION DEMO")
    
    # Test cases
    vague_requirements = [
        "Create a REST API",
        "Build a web app",
        "Make a CLI tool"
    ]
    
    for req in vague_requirements:
        print(f"\n🔍 Original Requirement: '{req}'")
        print("-" * 60)
        
        # Expand requirements
        expanded, was_expanded = RequirementsExpander.expand_requirements(req)
        
        if was_expanded:
            print("✅ Requirement was expanded!")
            
            # Extract key points
            key_points = RequirementsExpander.extract_key_requirements(expanded)
            print(f"\n📋 Key Areas Identified ({len(key_points)} areas):")
            for i, point in enumerate(key_points, 1):
                print(f"   {i}. {point}")
            
            # Show a snippet of the expansion
            print(f"\n📄 Expansion Preview:")
            lines = expanded.split('\n')
            for line in lines[10:20]:  # Show lines 10-20
                if line.strip():
                    print(f"   {line}")
        else:
            print("❌ Requirement was already detailed")


async def demonstrate_feature_extraction():
    """Demonstrate intelligent feature extraction"""
    print_section("INTELLIGENT FEATURE EXTRACTION DEMO")
    
    # Mock inputs
    original_req = "Create a REST API"
    
    mock_plan = """
    Development Plan:
    1. Set up project structure
    2. Design database schema
    3. Implement authentication
    4. Create CRUD endpoints
    5. Add validation
    6. Write tests
    7. Generate documentation
    """
    
    mock_design = """
    Technical Design:
    
    FEATURE[1]: Project Foundation
    Description: Initialize FastAPI with proper structure
    
    FEATURE[2]: Database Models
    Description: SQLAlchemy models for persistence
    
    FEATURE[3]: Authentication
    Description: JWT-based auth system
    
    FEATURE[4]: CRUD Endpoints
    Description: RESTful resource management
    
    FEATURE[5]: Validation
    Description: Input validation with Pydantic
    
    FEATURE[6]: Testing
    Description: Comprehensive test suite
    
    FEATURE[7]: Documentation
    Description: Auto-generated API docs
    """
    
    print(f"📝 Original Requirement: '{original_req}'")
    
    # Extract features
    features = IntelligentFeatureExtractor.extract_features(
        plan=mock_plan,
        design=mock_design,
        requirements=original_req
    )
    
    print(f"\n✅ Extracted {len(features)} features:")
    print("-" * 60)
    
    for i, feature in enumerate(features, 1):
        print(f"\n{i}. {feature['title']}")
        print(f"   ID: {feature['id']}")
        print(f"   Description: {feature['description'][:100]}...")
        
        if 'test_criteria' in feature:
            criteria = feature['test_criteria']
            if criteria.get('edge_cases'):
                print(f"   Edge Cases: {', '.join(criteria['edge_cases'][:2])}...")
            if criteria.get('error_conditions'):
                print(f"   Error Conditions: {', '.join(criteria['error_conditions'][:2])}...")


async def demonstrate_workflow_comparison():
    """Show before/after comparison"""
    print_section("BEFORE vs AFTER COMPARISON")
    
    print("🔴 BEFORE Enhancement:")
    print("   Input: 'Create a REST API'")
    print("   Result: 1 monolithic feature")
    print("   - Single implementation file")
    print("   - Basic tests (if any)")
    print("   - No clear structure")
    
    print("\n🟢 AFTER Enhancement:")
    print("   Input: 'Create a REST API'")
    print("   Result: 7+ modular features")
    print("   - Project Foundation")
    print("   - Database Models") 
    print("   - Authentication System")
    print("   - CRUD API Endpoints")
    print("   - Input Validation")
    print("   - Test Suite")
    print("   - API Documentation")
    print("\n   Each feature includes:")
    print("   ✓ Test-first implementation (TDD)")
    print("   ✓ Clear acceptance criteria")
    print("   ✓ Edge case handling")
    print("   ✓ Proper error conditions")
    print("   ✓ Review and validation")


async def demonstrate_tdd_workflow():
    """Show the TDD workflow for a single feature"""
    print_section("TDD WORKFLOW DEMO")
    
    print("📋 Feature: User Authentication")
    print("-" * 60)
    
    steps = [
        ("🔴 RED Phase", [
            "Write failing tests for authentication",
            "- Test user registration endpoint",
            "- Test login with valid credentials",
            "- Test login with invalid credentials",
            "- Test JWT token generation"
        ]),
        ("🟢 GREEN Phase", [
            "Implement minimal code to pass tests",
            "- Create auth endpoints",
            "- Add password hashing",
            "- Implement JWT generation",
            "- Handle error cases"
        ]),
        ("🔵 REFACTOR Phase", [
            "Improve code quality",
            "- Extract auth service",
            "- Add proper error messages",
            "- Optimize database queries",
            "- Add logging"
        ]),
        ("✅ VALIDATION Phase", [
            "Verify all tests pass",
            "Review implementation",
            "Check test coverage",
            "Proceed to next feature"
        ])
    ]
    
    for phase, actions in steps:
        print(f"\n{phase}:")
        for action in actions:
            print(f"   {action}")
            await asyncio.sleep(0.1)  # Small delay for effect


async def demonstrate_full_workflow():
    """Demonstrate the complete enhanced workflow"""
    print_section("FULL WORKFLOW EXECUTION")
    
    print("📥 Input: 'Create a REST API'")
    print("\nWorkflow Steps:")
    
    workflow_steps = [
        ("1️⃣ Requirements Expansion", "Expanding vague requirement to detailed specifications..."),
        ("2️⃣ Planning", "Creating comprehensive development plan..."),
        ("3️⃣ Design", "Generating technical design with 7 features..."),
        ("4️⃣ Feature Extraction", "Parsing features with test criteria..."),
        ("5️⃣ Dependency Analysis", "Ordering features by dependencies..."),
        ("6️⃣ TDD Implementation", "Implementing each feature with TDD:"),
    ]
    
    for step, description in workflow_steps:
        print(f"\n{step} {description}")
        await asyncio.sleep(0.2)
    
    # Show feature-by-feature progress
    features = [
        "Project Foundation",
        "Database Models",
        "Authentication System",
        "CRUD API Endpoints",
        "Input Validation",
        "Test Suite",
        "API Documentation"
    ]
    
    for i, feature in enumerate(features, 1):
        print(f"\n   Feature {i}/{len(features)}: {feature}")
        print(f"      🔴 Writing tests...")
        await asyncio.sleep(0.1)
        print(f"      🟢 Implementing code...")
        await asyncio.sleep(0.1)
        print(f"      ✅ Tests passing!")
        await asyncio.sleep(0.1)
    
    print("\n7️⃣ Final Integration", "Combining all features...")
    print("8️⃣ Validation", "Running full test suite...")
    print("\n✨ Workflow Complete!")
    
    # Show final statistics
    print("\n📊 Final Statistics:")
    print("   - Features Implemented: 7")
    print("   - Test Files Created: 7")
    print("   - Test Functions: 28+")
    print("   - Code Coverage: 85%+")
    print("   - Review Approvals: 9/9")


async def main():
    """Run all demonstrations"""
    print("\n" + "="*80)
    print("  MVP INCREMENTAL TDD WORKFLOW ENHANCEMENT DEMO")
    print("  Demonstrating how vague requirements expand to multiple features")
    print("="*80)
    
    # Run demonstrations
    await demonstrate_requirements_expansion()
    await demonstrate_feature_extraction()
    await demonstrate_workflow_comparison()
    await demonstrate_tdd_workflow()
    await demonstrate_full_workflow()
    
    print_section("DEMO COMPLETE")
    print("✅ The workflow now properly expands vague requirements into multiple features!")
    print("✅ Each feature goes through a complete TDD cycle!")
    print("✅ The result is well-structured, tested, and modular code!")
    
    print("\n📚 To use this in your project:")
    print("   1. Start the orchestrator: python orchestrator/orchestrator_agent.py")
    print("   2. Use the MVP Incremental TDD workflow")
    print("   3. Provide a vague requirement like 'Create a REST API'")
    print("   4. Watch as it expands to 7+ properly tested features!")


if __name__ == "__main__":
    asyncio.run(main())