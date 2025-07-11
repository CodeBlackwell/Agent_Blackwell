#!/usr/bin/env python3
"""Test that the enhanced TDD workflow is now the default"""

import asyncio
import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from flagship_orchestrator import FlagshipOrchestrator, USE_ENHANCED_ORCHESTRATOR
from models.flagship_models import TDDWorkflowConfig


async def test_default_orchestrator():
    """Test that the default orchestrator is the enhanced version"""
    
    print("🧪 Testing Default Orchestrator")
    print("=" * 80)
    
    # Check flag
    print(f"USE_ENHANCED_ORCHESTRATOR: {USE_ENHANCED_ORCHESTRATOR}")
    
    # Create orchestrator with default config
    config = TDDWorkflowConfig()
    orchestrator = FlagshipOrchestrator(config=config)
    
    # Check if it's the enhanced version
    print(f"Orchestrator type: {type(orchestrator).__name__}")
    print(f"Has enhanced orchestrator: {hasattr(orchestrator, 'enhanced_orchestrator')}")
    
    # Test with calculator requirements
    requirements = "create a calculator app with a front end and back end"
    
    print(f"\nTesting with: {requirements}")
    print("-" * 60)
    
    try:
        # Run workflow
        state = await orchestrator.run_tdd_workflow(requirements)
        
        print(f"\n✅ Workflow completed")
        print(f"Success: {state.all_tests_passing}")
        print(f"Iterations: {state.iteration_count}")
        
        # Check for enhanced features
        if hasattr(state, 'enhanced_result'):
            result = state.enhanced_result
            print(f"\n📊 Enhanced Features Detected:")
            
            if result.expanded_requirements:
                print(f"  - Requirements analyzed: ✅")
                print(f"  - Features identified: {len(result.expanded_requirements.features)}")
            else:
                print(f"  - Requirements analyzed: ❌")
            
            if result.architecture:
                print(f"  - Architecture planned: ✅")
                print(f"  - Project type: {result.architecture.project_type}")
            else:
                print(f"  - Architecture planned: ❌")
            
            if result.generated_files:
                print(f"  - Multi-file generation: ✅")
                print(f"  - Files generated: {len(result.generated_files)}")
            else:
                print(f"  - Multi-file generation: ❌")
        else:
            print("\n⚠️  No enhanced result found - using original orchestrator?")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("✅ Test completed")


if __name__ == "__main__":
    asyncio.run(test_default_orchestrator())