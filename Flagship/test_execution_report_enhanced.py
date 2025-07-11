#!/usr/bin/env python3
"""Test script to verify enhanced execution report generation"""

import asyncio
import json
from pathlib import Path
from datetime import datetime

# Import the orchestrator
from flagship_orchestrator_enhanced import FlagshipOrchestratorEnhanced
from models.flagship_models import TDDWorkflowConfig

async def test_enhanced_execution_report():
    """Test that execution report captures all required information"""
    
    # Create config
    config = TDDWorkflowConfig()
    config.test_framework = "pytest"
    
    # Create original command info
    original_command = {
        "endpoint": "/test/execution_report",
        "method": "POST",
        "requirements": "create a simple add function that adds two numbers",
        "config_type": "test",
        "timestamp": datetime.now().isoformat(),
        "user": "test_script"
    }
    
    # Create orchestrator with original command
    session_id = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    orchestrator = FlagshipOrchestratorEnhanced(
        config=config,
        session_id=session_id,
        original_command=original_command
    )
    
    print(f"🧪 Testing enhanced execution report generation")
    print(f"📁 Session ID: {session_id}")
    print(f"📂 Output directory: {orchestrator.file_manager.session_dir}")
    
    try:
        # Run workflow
        print("\n🚀 Running workflow...")
        state = await orchestrator.run_tdd_workflow("create a simple add function that adds two numbers")
        
        # Save workflow state (which includes execution report)
        print("\n💾 Saving workflow state and execution report...")
        orchestrator.save_workflow_state()
        
        # Check execution report
        report_path = orchestrator.file_manager.session_dir / "execution_report.json"
        report_with_id_path = orchestrator.file_manager.session_dir / f"execution_report_{session_id}.json"
        
        print(f"\n📊 Checking execution reports:")
        print(f"  - Plain report: {report_path.exists()}")
        print(f"  - Report with ID: {report_with_id_path.exists()}")
        
        if report_path.exists():
            # Load and analyze report
            with open(report_path, 'r') as f:
                report = json.load(f)
            
            print(f"\n📈 Execution Report Analysis:")
            print(f"  - Session ID: {report.get('session_id', 'N/A')}")
            print(f"  - Original Command: {json.dumps(report.get('original_command', {}), indent=2)}")
            print(f"  - Duration: {report.get('duration_ms', 0):.2f}ms")
            print(f"  - Total Events: {report['summary'].get('total_events', 0)}")
            print(f"  - Agent Exchanges: {report['summary'].get('agent_exchanges', 0)}")
            print(f"  - Command Executions: {report['summary'].get('command_executions', 0)}")
            print(f"  - Test Executions: {report['summary'].get('test_executions', 0)}")
            
            # Show metrics
            print(f"\n📊 Metrics:")
            metrics = report.get('metrics', {})
            for key, value in metrics.items():
                print(f"  - {key}: {value}")
            
            # Show agent exchanges
            if report.get('agent_exchanges'):
                print(f"\n🤖 Agent Exchanges:")
                for exchange in report['agent_exchanges'][:3]:  # Show first 3
                    print(f"  - {exchange['agent_name']} ({exchange['phase']}): "
                          f"{exchange['duration_ms']:.2f}ms - "
                          f"{'✅' if exchange['success'] else '❌'}")
            
            # Show timeline
            if report.get('timeline'):
                print(f"\n📅 Timeline (first 5 events):")
                for event in report['timeline'][:5]:
                    print(f"  - {event['timestamp']}: {event['description']}")
            
            print(f"\n✅ Execution report generated successfully!")
            print(f"📁 Full report saved at: {report_path}")
            
        else:
            print(f"\n❌ Execution report not found!")
            
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_enhanced_execution_report())