#!/usr/bin/env python3
"""
Combined test suite for the executor agent with proof of execution functionality.
This file combines and refactors the original test_executor_proof.py and test_proof_of_execution.py files.
"""

import asyncio
import json
from pathlib import Path
import sys
from datetime import datetime
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from acp_sdk import Message
from acp_sdk.models import MessagePart
from agents.executor.executor_agent import executor_agent
from workflows.workflow_manager import execute_workflow
from workflows.workflow_config import GENERATED_CODE_PATH


class ProofOfExecutionTester:
    """Handles testing and verification of proof of execution functionality"""
    
    def __init__(self):
        self.status_icons = {
            'started': '🔵',
            'completed': '✅',
            'failed': '❌'
        }
        self.test_code = """
    Create a simple Python calculator with tests.
    
    FILENAME: calculator.py
    ```python
    class Calculator:
        def add(self, a, b):
            return a + b
        
        def subtract(self, a, b):
            return a - b
        
        def multiply(self, a, b):
            return a * b
        
        def divide(self, a, b):
            if b == 0:
                raise ValueError("Cannot divide by zero")
            return a / b
    ```
    
    FILENAME: test_calculator.py
    ```python
    import pytest
    from calculator import Calculator

    def test_calculator():
        calc = Calculator()
        assert calc.add(2, 3) == 5
        assert calc.subtract(5, 3) == 2
        assert calc.multiply(3, 4) == 12
        assert calc.divide(10, 2) == 5
        
        with pytest.raises(ValueError):
            calc.divide(10, 0)
        
        print("All tests passed!")
    ```
    
    Please execute these files and run the tests with pytest.
    """
    
    def find_proof_documents(self) -> List[Path]:
        """Find all proof of execution documents"""
        generated_path = Path(GENERATED_CODE_PATH)
        return list(generated_path.rglob("proof_of_execution.json"))
    
    def display_proof_entry(self, entry: Dict[str, Any], index: int) -> None:
        """Display a single proof entry with formatting"""
        timestamp = entry.get('timestamp', 'N/A')
        stage = entry.get('stage', 'unknown')
        status = entry.get('status', 'unknown')
        details = entry.get('details', {})
        
        status_icon = self.status_icons.get(status, '⚪')
        
        print(f"\n{index}. {status_icon} {stage} ({status})")
        print(f"   Time: {timestamp}")
        
        # Display stage-specific details
        if stage == 'executor_initialization':
            print(f"   Input length: {details.get('input_length', 'N/A')} chars")
            
        elif stage == 'environment_analysis' and status == 'completed':
            print(f"   Language: {details.get('language', 'N/A')}:{details.get('version', 'N/A')}")
            print(f"   Dependencies: {details.get('dependencies_count', 0)}")
            commands = details.get('execution_commands', [])
            if commands:
                print(f"   Commands: {', '.join(commands)}")
                
        elif stage == 'docker_setup' and status == 'completed':
            print(f"   Container: {details.get('container_name', 'N/A')}")
            print(f"   Container ID: {details.get('container_id', 'N/A')}")
            print(f"   Reused: {details.get('reused_existing', False)}")
            
        elif stage == 'code_execution' and status == 'completed':
            print(f"   Overall success: {details.get('overall_success', False)}")
            executions = details.get('executions', [])
            for exec_detail in executions:
                cmd = exec_detail.get('command', 'N/A')
                success = exec_detail.get('success', False)
                exit_code = exec_detail.get('exit_code', 'N/A')
                cmd_icon = "✅" if success else "❌"
                print(f"   {cmd_icon} Command: {cmd} (exit: {exit_code})")
                if exec_detail.get('stdout_preview'):
                    print(f"      Output preview: {exec_detail['stdout_preview'][:100]}...")
                    
        elif stage == 'result_analysis' and status == 'completed':
            preview = details.get('analysis_preview', '')[:150]
            if preview:
                print(f"   Analysis preview: {preview}...")
                
        elif stage == 'executor_error':
            print(f"   Error type: {details.get('error_type', 'Unknown')}")
            print(f"   Error: {details.get('error_message', 'No message')}")
    
    def display_proof_document(self, proof_file: Path) -> None:
        """Display the contents of a proof document"""
        print(f"\n📍 Proof document: {proof_file}")
        print("-" * 60)
        
        try:
            with open(proof_file, 'r') as f:
                entries = json.load(f)
            
            print(f"Total entries: {len(entries)}")
            print("\n📊 Execution Timeline:")
            
            for i, entry in enumerate(entries, 1):
                self.display_proof_entry(entry, i)
                
        except Exception as e:
            print(f"Error reading proof file: {e}")
    
    async def test_direct_executor(self) -> None:
        """Test executor agent directly with proof of execution"""
        print("🧪 Testing Executor Agent Directly with Proof of Execution")
        print("=" * 60)
        
        # Create message
        message = Message(
            role="user",
            parts=[MessagePart(content=self.test_code)]
        )
        
        print("📤 Sending code to executor agent...")
        
        # Call executor agent
        result_parts = []
        async for part in executor_agent([message]):
            result_parts.append(part)
            print("\n📥 Executor Response:")
            print(part.content)
        
        # Look for proof documents
        print("\n\n📄 Searching for proof of execution documents...")
        proof_files = self.find_proof_documents()
        
        if proof_files:
            print(f"\n✅ Found {len(proof_files)} proof of execution document(s)!")
            
            # Display the most recent one
            most_recent = max(proof_files, key=lambda p: p.stat().st_mtime)
            self.display_proof_document(most_recent)
        else:
            print("❌ No proof of execution documents found!")
    
    async def test_workflow_execution(self) -> None:
        """Test proof of execution through workflow manager"""
        print("🧪 Testing Proof of Execution via Workflow Manager")
        print("=" * 60)
        
        print("\n📋 Running TDD workflow with executor agent...")
        
        try:
            # Execute workflow
            result = await execute_workflow(
                requirements=self.test_code,
                workflow_type="tdd",
                session_id=f"proof_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            
            print("\n✅ Workflow completed!")
            
            # Find and display proof documents
            print("\n📄 Looking for proof of execution documents...")
            proof_files = self.find_proof_documents()
            
            if proof_files:
                print(f"\nFound {len(proof_files)} proof of execution document(s):")
                
                # Show all proof files found
                for proof_file in sorted(proof_files, key=lambda p: p.stat().st_mtime, reverse=True):
                    self.display_proof_document(proof_file)
            else:
                print("⚠️ No proof of execution documents found!")
                
        except Exception as e:
            print(f"\n❌ Error during test: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """Main test function"""
    tester = ProofOfExecutionTester()
    
    print("🚀 Executor Proof of Execution Test Suite")
    print("=" * 80)
    print("\nThis test suite verifies the proof of execution functionality")
    print("in the executor agent through both direct and workflow-based tests.\n")
    
    # Run both test scenarios
    print("\n" + "=" * 80)
    print("TEST 1: Direct Executor Agent Test")
    print("=" * 80)
    await tester.test_direct_executor()
    
    print("\n" + "=" * 80)
    print("TEST 2: Workflow Manager Test")
    print("=" * 80)
    await tester.test_workflow_execution()
    
    print("\n" + "=" * 80)
    print("✅ All tests completed!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())