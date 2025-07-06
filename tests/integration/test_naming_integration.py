#!/usr/bin/env python3
"""Integration test for new naming convention in workflows"""

import asyncio
from workflows.workflow_manager import execute_workflow
from shared.data_models import CodingTeamInput, TeamMember
import re

async def test_naming_in_workflow():
    """Test that the new naming convention works in actual workflows"""
    
    print("Testing Dynamic Naming in Workflow Integration")
    print("=" * 80)
    
    # Test with a specific requirement
    test_input = CodingTeamInput(
        requirements="Create a temperature converter tool that converts between Celsius and Fahrenheit",
        workflow_type="full",
        team_members=[TeamMember.planner, TeamMember.coder, TeamMember.executor]
    )
    
    print(f"Requirements: {test_input.requirements}")
    print(f"Expected name pattern: YYYYMMDD_HHMMSS_temperature_converter_tool_<hash>")
    print()
    
    try:
        # Execute workflow
        results, execution_report = await execute_workflow(test_input)
        
        print("Workflow completed!")
        print()
        
        # Look for session ID in executor output
        for result in results:
            if result.name == "executor":
                output = result.output
                
                # Extract session ID from output
                session_match = re.search(r'Session ID:\s*(\S+)', output)
                if session_match:
                    session_id = session_match.group(1)
                    print(f"✅ Found Session ID: {session_id}")
                    
                    # Verify format
                    parts = session_id.split('_')
                    if len(parts) >= 4:
                        date_part = parts[0]
                        time_part = parts[1]
                        name_parts = parts[2:-1]  # Everything except date, time, and hash
                        hash_part = parts[-1]
                        
                        print(f"   Date: {date_part}")
                        print(f"   Time: {time_part}")
                        print(f"   Dynamic Name: {'_'.join(name_parts)}")
                        print(f"   Hash: {hash_part}")
                        
                        # Check if dynamic name matches expectations
                        dynamic_name = '_'.join(name_parts)
                        if "temperature" in dynamic_name or "converter" in dynamic_name:
                            print(f"   ✅ Dynamic name correctly derived from requirements!")
                        else:
                            print(f"   ⚠️  Dynamic name doesn't match expected pattern")
                    else:
                        print(f"   ⚠️  Session ID format unexpected: {session_id}")
                else:
                    print("❌ Could not find Session ID in executor output")
                
                # Also look for directory path
                dir_match = re.search(r'generated/([^/\s]+)/', output)
                if dir_match:
                    dir_name = dir_match.group(1)
                    print(f"\n✅ Generated directory: generated/{dir_name}/")
                
                break
        else:
            print("⚠️  Executor not found in results")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_naming_in_workflow())