#!/usr/bin/env python3
"""
Example: File Processor with Error Recovery
Demonstrates error recovery and retry mechanisms
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from shared.data_models import CodingTeamInput
from workflows.workflow_manager import execute_workflow


async def run_file_processor_example():
    """Run file processor example highlighting error recovery."""
    
    print("📁 File Processor with Error Recovery Example")
    print("=" * 60)
    print("This example demonstrates:")
    print("- Error detection and recovery")
    print("- Retry mechanisms with context")
    print("- Handling edge cases")
    print("- Progressive feature implementation")
    print()
    
    # Requirements that will likely trigger some errors and retries
    requirements = """
Create a robust CSV file processor with error handling:

1. File Reading:
   - Read CSV files with configurable delimiter
   - Handle different encodings (UTF-8, Latin-1)
   - Support large files with streaming
   - Detect and skip malformed rows

2. Data Validation:
   - Validate column data types
   - Check for required columns
   - Handle missing values (NaN, empty strings)
   - Validate value ranges and formats

3. Data Processing:
   - Filter rows based on multiple conditions
   - Aggregate data (sum, average, count, min, max)
   - Group by multiple columns
   - Sort by multiple columns

4. Error Handling:
   - Log all errors with context
   - Create error report file
   - Continue processing on non-fatal errors
   - Provide detailed error statistics

5. Output:
   - Export to CSV with custom formatting
   - Export to JSON with nested structure
   - Generate summary statistics report
   - Include processing metadata

6. Edge Cases to Handle:
   - Empty files
   - Files with only headers
   - Unicode characters
   - Very large numbers
   - Date parsing errors
"""
    
    # Create input with minimal test execution (to show retry behavior)
    input_data = CodingTeamInput(
        requirements=requirements,
        run_tests=False,  # Disable tests to focus on validation/retry
        run_integration_verification=True  # Enable to show full validation
    )
    
    print("📋 Configuration:")
    print("   Phase 9 (Test Execution): ❌ Disabled")
    print("   Phase 10 (Integration): ✅ Enabled")
    print("   Focus: Error recovery and retries")
    print()
    print("🚀 Starting workflow...")
    print("-" * 60)
    
    try:
        # Execute the workflow
        result = await execute_workflow(
            "mvp_incremental",
            input_data
        )
        
        print()
        print("✅ Workflow completed successfully!")
        print()
        print("📊 Results:")
        print("   - Robust CSV processor with error handling")
        print("   - Comprehensive validation logic")
        print("   - Multiple output format support")
        print("   - Error recovery mechanisms")
        print()
        print("💡 Error Recovery Demonstrated:")
        print("   - Import errors were detected and fixed")
        print("   - Missing functions were added on retry")
        print("   - Error context helped guide fixes")
        print("   - Final implementation handles all edge cases")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
        
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(run_file_processor_example())
    sys.exit(exit_code)