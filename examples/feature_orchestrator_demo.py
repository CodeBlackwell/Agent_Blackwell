#!/usr/bin/env python3
"""
Demo showing how to use the Feature Orchestrator directly.
This is the core component of the incremental workflow.
"""

import asyncio
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workflows.incremental.feature_orchestrator import (
    FeatureOrchestrator, 
    execute_features_incrementally,
    prepare_feature_context,
    parse_code_files
)
from workflows.monitoring import WorkflowExecutionTracer
from shared.utils.feature_parser import FeatureParser, Feature, ComplexityLevel

# Example designer output with features
DESIGNER_OUTPUT_WITH_FEATURES = """
Blog Application Technical Design

IMPLEMENTATION PLAN:

FEATURE[1]: Core Models
Description: Create the foundational database models
Files: models.py
Validation: All models should have proper fields defined
Dependencies: []
Complexity: low

FEATURE[2]: Authentication
Description: Implement user authentication with JWT
Files: auth.py
Validation: Login and token generation work correctly  
Dependencies: [FEATURE[1]]
Complexity: medium

FEATURE[3]: Blog API
Description: Create REST API for blog posts
Files: api.py
Validation: CRUD operations work with authorization
Dependencies: [FEATURE[1], FEATURE[2]]
Complexity: medium
"""

async def demo_feature_orchestrator():
    """Demonstrate using the feature orchestrator directly."""
    
    print("🔧 Feature Orchestrator Demo")
    print("=" * 60)
    
    # Create a tracer for monitoring
    tracer = WorkflowExecutionTracer("feature_orchestrator_demo")
    
    # Create the orchestrator
    orchestrator = FeatureOrchestrator(tracer)
    
    # Parse features from designer output
    print("\n1️⃣ Parsing features from designer output...")
    parser = FeatureParser()
    features = parser.parse(DESIGNER_OUTPUT_WITH_FEATURES)
    
    print(f"\n📋 Found {len(features)} features:")
    for feature in features:
        print(f"   • {feature.id}: {feature.title}")
        print(f"     Files: {', '.join(feature.files)}")
        print(f"     Complexity: {feature.complexity.value}")
        if feature.dependencies:
            print(f"     Dependencies: {', '.join(feature.dependencies)}")
    
    # Example of using the helper functions
    print("\n2️⃣ Example: Preparing context for a feature...")
    if features:
        context = prepare_feature_context(
            feature=features[0],
            requirements="Create a blog application",
            design=DESIGNER_OUTPUT_WITH_FEATURES,
            existing_code={},
            tests=None,
            retry_attempt=0
        )
        print(f"\nContext preview (first 500 chars):")
        print(context[:500] + "...")
    
    # Example of parsing code output
    print("\n3️⃣ Example: Parsing code files from output...")
    sample_code_output = """
    Here's the implementation:
    
    FILENAME: models.py
    ```python
    from sqlalchemy import Column, Integer, String
    from sqlalchemy.ext.declarative import declarative_base
    
    Base = declarative_base()
    
    class User(Base):
        __tablename__ = 'users'
        id = Column(Integer, primary_key=True)
        username = Column(String(50), unique=True)
    ```
    
    FILENAME: config.py
    ```python
    DATABASE_URL = "sqlite:///blog.db"
    SECRET_KEY = "your-secret-key"
    ```
    """
    
    parsed_files = parse_code_files(sample_code_output)
    print(f"\nParsed {len(parsed_files)} files:")
    for filename, content in parsed_files.items():
        print(f"   • {filename} ({len(content.split())} words)")
    
    # Show how the orchestrator would be used in a workflow
    print("\n4️⃣ How to use in a workflow:")
    print("""
    # In your workflow:
    async def my_workflow():
        orchestrator = FeatureOrchestrator(tracer)
        
        # Execute incremental development
        team_results, final_codebase, summary = await orchestrator.execute_incremental_development(
            designer_output=designer_output,
            requirements=requirements,
            tests=None,
            max_retries=3
        )
        
        # Process results
        print(f"Completed {summary['completed_features']} features")
        print(f"Generated {len(final_codebase)} files")
    """)
    
    # Alternative: Direct feature execution
    print("\n5️⃣ Alternative: Execute features directly...")
    print("""
    # You can also use execute_features_incrementally directly:
    completed, codebase = await execute_features_incrementally(
        features=features,
        requirements=requirements,
        design=design,
        tests=None,
        tracer=tracer,
        max_retries=3
    )
    """)
    
    print("\n✅ Demo complete!")
    print("\n💡 Key takeaways:")
    print("• FeatureOrchestrator breaks down projects into manageable features")
    print("• Each feature is implemented and validated independently")
    print("• Failed features are retried with smart strategies")
    print("• Progress is tracked throughout execution")
    print("• The orchestrator can be used standalone or within workflows")

def main():
    """Main entry point."""
    print("\n🎯 Understanding the Feature Orchestrator")
    print("="*60)
    print("\nThe Feature Orchestrator is the heart of the incremental workflow.")
    print("It manages feature-by-feature implementation with validation.\n")
    
    # Run the demo
    asyncio.run(demo_feature_orchestrator())
    
    print("\n📚 For full workflow integration, see:")
    print("   workflows/incremental/incremental_workflow.py")
    print("\n🔨 To build a real project, use:")
    print("   python examples/direct_incremental_blog_demo.py")

if __name__ == "__main__":
    main()