#!/usr/bin/env python3
"""Test the execution report functionality"""

import asyncio
import json
from pathlib import Path

from flagship_orchestrator import FlagshipOrchestrator
from models.flagship_models import TDDWorkflowConfig


async def test_execution_report():
    """Test that execution report is generated correctly"""
    print("Testing Execution Report Generation")
    print("=" * 80)
    
    # Create orchestrator with custom session ID
    session_id = "test_execution_report"
    config = TDDWorkflowConfig(
        max_iterations=3,
        phase_timeout=60,
        enable_refactoring=False
    )
    
    orchestrator = FlagshipOrchestrator(config=config, session_id=session_id)
    
    # Simple requirements for testing
    requirements = "Create a greeting function that takes a name and returns 'Hello, {name}!'"
    
    try:
        # Run the workflow
        print(f"\nRunning TDD workflow for: {requirements}")
        state = await orchestrator.run_tdd_workflow(requirements)
        
        # Save the state (which includes execution report)
        orchestrator.save_workflow_state()
        
        # Load and display the execution report
        report_path = Path("generated") / f"session_{session_id}" / f"execution_report_{session_id}.json"
        
        if report_path.exists():
            print(f"\n{'='*80}")
            print("EXECUTION REPORT PREVIEW")
            print(f"{'='*80}\n")
            
            with open(report_path, 'r') as f:
                report = json.load(f)
            
            # Display summary
            print(f"Session ID: {report['session_id']}")
            print(f"Duration: {report['duration_ms']:.2f} ms")
            print(f"Total Events: {report['metrics']['total_events']}")
            print(f"Agent Interactions: {report['metrics']['agent_interactions']}")
            print(f"Commands Executed: {report['metrics']['commands_executed']}")
            print(f"Tests Run: {report['metrics']['tests_run']}")
            
            # Display agent exchanges
            print(f"\n{'='*60}")
            print("AGENT EXCHANGES")
            print(f"{'='*60}")
            for exchange in report['agent_exchanges']:
                print(f"\n{exchange['agent_name']} (Phase: {exchange['phase']}, Iteration: {exchange['iteration']})")
                print(f"  Duration: {exchange['duration_ms']:.2f} ms")
                print(f"  Success: {exchange['success']}")
                if exchange.get('error'):
                    print(f"  Error: {exchange['error']}")
            
            # Display command executions
            if report['command_executions']:
                print(f"\n{'='*60}")
                print("COMMAND EXECUTIONS")
                print(f"{'='*60}")
                for cmd in report['command_executions']:
                    print(f"\nCommand: {cmd['command']}")
                    print(f"  Exit Code: {cmd['exit_code']}")
                    print(f"  Duration: {cmd['duration_ms']:.2f} ms")
                    print(f"  Success: {cmd['success']}")
            
            # Display test executions
            if report['test_executions']:
                print(f"\n{'='*60}")
                print("TEST EXECUTIONS")
                print(f"{'='*60}")
                for test in report['test_executions']:
                    print(f"\nTest File: {test['test_file']}")
                    print(f"  Total Tests: {test['total_tests']}")
                    print(f"  Passed: {test['passed_tests']}")
                    print(f"  Failed: {test['failed_tests']}")
                    print(f"  Duration: {test['duration_ms']:.2f} ms")
            
            # Display timeline
            print(f"\n{'='*60}")
            print("EXECUTION TIMELINE")
            print(f"{'='*60}")
            for event in report['timeline'][:10]:  # Show first 10 events
                print(f"{event['timestamp']}: {event['description']}")
            
            print(f"\nFull execution report saved to: {report_path}")
            
        else:
            print(f"ERROR: Execution report not found at {report_path}")
            
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_execution_report())