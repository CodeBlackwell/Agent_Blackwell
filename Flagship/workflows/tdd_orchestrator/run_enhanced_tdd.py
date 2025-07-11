#!/usr/bin/env python3
"""Main entry point for Enhanced TDD Workflow"""

import asyncio
import sys
from pathlib import Path

# Add Flagship to path
flagship_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(flagship_path))

from enhanced_orchestrator import EnhancedTDDOrchestrator
from enhanced_models import EnhancedTDDOrchestratorConfig


async def main():
    """Run the enhanced TDD workflow with example requirements"""
    
    # Example requirements
    if len(sys.argv) > 1:
        requirements = " ".join(sys.argv[1:])
    else:
        # Default example
        requirements = "create a calculator app with a front end and back end"
    
    print("🚀 Enhanced TDD Workflow")
    print("=" * 80)
    print(f"Requirements: {requirements}")
    print("=" * 80)
    print()
    
    # Configure the orchestrator
    config = EnhancedTDDOrchestratorConfig(
        enable_requirements_analysis=True,
        enable_architecture_planning=True,
        enable_feature_validation=True,
        multi_file_support=True,
        feature_based_implementation=True,
        verbose_output=True
    )
    
    # Create orchestrator
    orchestrator = EnhancedTDDOrchestrator(config)
    
    try:
        # Execute the workflow
        result = await orchestrator.execute_feature(requirements)
        
        # Print results
        print("\n" + "=" * 80)
        print("📊 WORKFLOW RESULTS")
        print("=" * 80)
        
        print(f"\n✅ Success: {result.success}")
        print(f"⏱️ Duration: {result.total_duration_seconds:.2f} seconds")
        print(f"🔄 Total Cycles: {len(result.cycles)}")
        
        if result.expanded_requirements:
            print(f"\n📋 Features Identified: {len(result.expanded_requirements.features)}")
            for feature in result.expanded_requirements.features:
                print(f"  - {feature.title} ({feature.complexity})")
        
        if result.architecture:
            print(f"\n🏗️ Architecture:")
            print(f"  - Type: {result.architecture.project_type}")
            print(f"  - Components: {len(result.architecture.components)}")
            print(f"  - Tech Stack: {', '.join(result.architecture.technology_stack.values())}")
        
        if result.generated_files:
            print(f"\n📁 Generated Files: {len(result.generated_files)}")
            for filepath in sorted(result.generated_files.keys()):
                print(f"  - {filepath}")
        
        if result.validation_report:
            print(f"\n✅ Validation Report:")
            print(f"  - All Requirements Met: {result.validation_report.all_requirements_met}")
            print(f"  - Implemented Features: {len(result.validation_report.implemented_features)}")
            if result.validation_report.missing_features:
                print(f"  - Missing Features: {len(result.validation_report.missing_features)}")
                for feature in result.validation_report.missing_features:
                    print(f"    - {feature}")
        
        # Save execution report
        import json
        from datetime import datetime
        
        report_path = Path(f"execution_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        report_data = {
            "requirements": requirements,
            "success": result.success,
            "duration_seconds": result.total_duration_seconds,
            "features_count": len(result.expanded_requirements.features) if result.expanded_requirements else 0,
            "files_generated": len(result.generated_files),
            "errors": result.errors
        }
        
        report_path.write_text(json.dumps(report_data, indent=2))
        print(f"\n💾 Execution report saved to: {report_path}")
        
        # Show project structure if successful
        if result.success and hasattr(orchestrator, 'project_manager'):
            summary = orchestrator.project_manager.create_project_summary()
            if summary.get("structure"):
                print(f"\n📂 Project Structure:")
                for line in summary["structure"]:
                    print(f"  {line}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())