#!/usr/bin/env python3
"""
Test script for orchestrator workflow with Planning and Code agents.

This script demonstrates the complete workflow:
1. User Request → Planning Agent (creates job plan)
2. Job Plan → Orchestrator Agent (creates coordination strategy)
3. Coding Tasks → Code Agent (generates and saves code)

Usage:
    python test_orchestrator_workflow.py
"""

import asyncio
import json
import sys
import os
from typing import Dict, Any

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from acp_sdk.client import Client
from acp_sdk.models import Message, MessagePart
from config.config import AGENT_PORTS

class OrchestrationWorkflowTester:
    """Test harness for the orchestration workflow."""
    
    def __init__(self):
        self.planning_url = f"http://localhost:{AGENT_PORTS['planning']}"
        self.orchestrator_url = f"http://localhost:{AGENT_PORTS['orchestrator']}"
        self.code_url = f"http://localhost:{AGENT_PORTS['code']}"
        
    async def test_complete_workflow(self, user_request: str):
        """
        Test the complete workflow from user request to code generation.
        
        Args:
            user_request: The initial user request to process
        """
        print("🚀 Starting Orchestration Workflow Test")
        print("=" * 60)
        
        try:
            # Step 1: Planning Agent - Create Job Plan
            print("\n📋 Step 1: Creating Job Plan with Planning Agent")
            print("-" * 50)
            job_plan = await self._call_planning_agent(user_request)
            
            if not job_plan:
                print("❌ Failed to get job plan from Planning Agent")
                return
                
            # Step 2: Orchestrator Agent - Create Coordination Strategy
            print("\n🎯 Step 2: Creating Coordination Strategy with Orchestrator")
            print("-" * 50)
            orchestration_result = await self._call_orchestrator_agent(job_plan)
            
            if not orchestration_result:
                print("❌ Failed to get orchestration strategy")
                return
                
            # Step 3: Code Agent - Generate Code for Features
            print("\n💻 Step 3: Generating Code with Code Agent")
            print("-" * 50)
            await self._call_code_agent_for_features(job_plan, orchestration_result)
            
            print("\n✅ Complete Workflow Test Finished!")
            print("=" * 60)
            
        except Exception as e:
            print(f"❌ Workflow test failed: {str(e)}")
            import traceback
            traceback.print_exc()
    
    async def _call_planning_agent(self, user_request: str) -> Dict[str, Any]:
        """Call the planning agent and return the job plan."""
        try:
            async with Client(base_url=self.planning_url) as client:
                print(f"📞 Calling Planning Agent at {self.planning_url}")
                print(f"📝 User Request: {user_request}")
                
                message = Message(parts=[MessagePart(content=user_request)])
                
                print("\n🔄 Planning Agent Response:")
                response_parts = []
                
                async for event in client.run_stream(agent="planner", input=[message]):
                    if hasattr(event, 'output') and event.output:
                        for part in event.output:
                            content = part.content
                            print(content)
                            response_parts.append(content)
                
                # Extract JSON from the response
                full_response = "\n".join(response_parts)
                job_plan = self._extract_json_from_response(full_response)
                
                if job_plan:
                    print(f"\n✅ Job Plan Created: {len(job_plan.get('feature_sets', []))} features identified")
                    return job_plan
                else:
                    print("⚠️ No valid JSON job plan found in response")
                    return None
                    
        except Exception as e:
            print(f"❌ Error calling Planning Agent: {str(e)}")
            return None
    
    async def _call_orchestrator_agent(self, job_plan: Dict[str, Any]) -> str:
        """Call the orchestrator agent with the job plan."""
        try:
            async with Client(base_url=self.orchestrator_url) as client:
                print(f"📞 Calling Orchestrator Agent at {self.orchestrator_url}")
                
                # Convert job plan to JSON string for the orchestrator
                job_plan_json = json.dumps(job_plan, indent=2)
                message = Message(parts=[MessagePart(content=job_plan_json)])
                
                print("\n🔄 Orchestrator Agent Response:")
                response_parts = []
                
                async for event in client.run_stream(agent="orchestrate_pipeline", input=[message]):
                    if hasattr(event, 'output') and event.output:
                        for part in event.output:
                            content = part.content
                            print(content)
                            response_parts.append(content)
                
                full_response = "\n".join(response_parts)
                print(f"\n✅ Orchestration Strategy Created")
                return full_response
                
        except Exception as e:
            print(f"❌ Error calling Orchestrator Agent: {str(e)}")
            return None
    
    async def _call_code_agent_for_features(self, job_plan: Dict[str, Any], orchestration_result: str):
        """Generate code for each feature in the job plan."""
        try:
            feature_sets = job_plan.get("feature_sets", [])
            
            if not feature_sets:
                print("⚠️ No feature sets found in job plan")
                return
            
            async with Client(base_url=self.code_url) as client:
                print(f"📞 Calling Code Agent at {self.code_url}")
                
                for i, feature in enumerate(feature_sets):
                    feature_name = feature.get("name", f"Feature_{i+1}")
                    feature_description = feature.get("description", "No description")
                    
                    print(f"\n🔧 Generating code for: {feature_name}")
                    print(f"📄 Description: {feature_description}")
                    
                    # Create a coding request based on the feature
                    coding_request = f"""
Generate code for the following feature:

Feature Name: {feature_name}
Description: {feature_description}
Priority: {feature.get('priority', 'Normal')}
Estimated Effort: {feature.get('estimated_effort', 'Unknown')}

Please create a well-structured implementation with:
1. Appropriate file structure
2. Clean, documented code
3. Error handling
4. Basic functionality for this feature

Focus on creating a foundational implementation that can be extended.
"""
                    
                    message = Message(parts=[MessagePart(content=coding_request)])
                    
                    print(f"\n🔄 Code Agent Response for {feature_name}:")
                    
                    async for event in client.run_stream(agent="simple_code_agent", input=[message]):
                        if hasattr(event, 'output') and event.output:
                            for part in event.output:
                                content = part.content
                                print(content)
                    
                    print(f"\n✅ Code generation completed for {feature_name}")
                    
        except Exception as e:
            print(f"❌ Error calling Code Agent: {str(e)}")
    
    def _extract_json_from_response(self, response: str) -> Dict[str, Any]:
        """Extract JSON from a response that may contain markdown formatting."""
        try:
            # Look for JSON in markdown code blocks
            import re
            json_match = re.search(r'```json\s*([\s\S]+?)\s*```', response)
            if json_match:
                json_str = json_match.group(1)
                return json.loads(json_str)
            
            # Try to find JSON without markdown
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
                
            return None
        except json.JSONDecodeError:
            return None

async def main():
    """Main test function."""
    print("🧪 Orchestrator Workflow Test Suite")
    print("This test requires all three agents to be running:")
    print(f"  - Planning Agent on port {AGENT_PORTS['planning']}")
    print(f"  - Orchestrator Agent on port {AGENT_PORTS['orchestrator']}")
    print(f"  - Code Agent on port {AGENT_PORTS['code']}")
    print()
    
    # Test with a sample user request
    user_request = """
Create a simple task management web application with the following features:
1. User authentication (login/register)
2. Task creation and editing
3. Task categorization with tags
4. Basic dashboard with task overview
5. Simple REST API for mobile app integration

The application should be built with Python/Flask for the backend and include basic HTML templates for the frontend. Focus on clean, maintainable code with proper error handling.
"""
    
    tester = OrchestrationWorkflowTester()
    await tester.test_complete_workflow(user_request)

if __name__ == "__main__":
    asyncio.run(main())
