#!/usr/bin/env python3
"""
Example: Data Pipeline with Feature Dependencies
Demonstrates feature dependency ordering and complex workflows
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from shared.data_models import CodingTeamInput
from workflows.workflow_manager import execute_workflow


async def run_data_pipeline_example():
    """Run data pipeline example showing feature dependencies."""
    
    print("🔄 Data Pipeline with Feature Dependencies Example")
    print("=" * 60)
    print("This example demonstrates:")
    print("- Complex feature dependencies")
    print("- Automatic dependency ordering")
    print("- Multi-stage pipeline implementation")
    print("- Progress tracking across phases")
    print()
    
    # Requirements with clear dependencies between features
    requirements = """
Create a data processing pipeline for analyzing sales data:

1. Data Ingestion Layer:
   - Load data from multiple CSV files
   - Support for different date formats
   - Handle missing and corrupted files
   - Create unified dataset

2. Data Cleaning Module (depends on ingestion):
   - Remove duplicate records
   - Fix inconsistent product names
   - Handle missing values
   - Standardize currency formats

3. Data Transformation (depends on cleaning):
   - Calculate derived metrics (revenue, profit margin)
   - Convert currencies to USD
   - Aggregate by time periods (daily, weekly, monthly)
   - Create product categories

4. Analytics Engine (depends on transformation):
   - Calculate top selling products
   - Identify sales trends
   - Customer segmentation analysis
   - Seasonal pattern detection

5. Reporting Module (depends on analytics):
   - Generate executive summary
   - Create visualizations (using matplotlib)
   - Export reports to PDF
   - Email report distribution

6. Monitoring System (depends on all above):
   - Track pipeline execution time
   - Log data quality metrics
   - Alert on anomalies
   - Generate performance reports

Each module should be implemented as a separate class with clear interfaces.
Include error handling and logging throughout the pipeline.
"""
    
    # Create input with full validation
    input_data = CodingTeamInput(
        requirements=requirements,
        run_tests=True,
        run_integration_verification=True
    )
    
    print("📋 Configuration:")
    print("   All phases enabled for comprehensive validation")
    print("   Feature dependencies will be automatically detected")
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
        print("   - Complete data pipeline implementation")
        print("   - Features implemented in dependency order")
        print("   - All modules properly integrated")
        print("   - Comprehensive error handling")
        print()
        print("💡 Dependency Management:")
        print("   - Ingestion implemented first (no dependencies)")
        print("   - Cleaning implemented after ingestion")
        print("   - Transformation after cleaning")
        print("   - Analytics after transformation")
        print("   - Reporting and monitoring last")
        print()
        print("🔗 Pipeline Architecture:")
        print("   CSV Files → Ingestion → Cleaning → Transform →")
        print("   Analytics → Reporting → Monitoring")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
        
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(run_data_pipeline_example())
    sys.exit(exit_code)