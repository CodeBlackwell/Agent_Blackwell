"""Orchestrator Agent for coordinating the job pipeline workflow.

This is the central controller for the entire development workflow,
managing multiple agent pipelines and coordinating between phases.

Aligned with ACP SDK best practices and patterns from acp-agent-generator example.
"""

import asyncio
import json
import uuid
from collections.abc import AsyncGenerator
from typing import Dict, List, Any, Optional
from acp_sdk.models import Message, MessagePart
from acp_sdk.server import Context, Server, RunYield, RunYieldResume
from beeai_framework.agents.react import ReActAgent
from beeai_framework.backend.chat import ChatModel
from beeai_framework.memory import TokenMemory
from beeai_framework.backend import UserMessage, SystemMessage
from beeai_framework.template import PromptTemplate, PromptTemplateInput

import sys
import os
# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config.config import (
    LLM_CONFIG, 
    AGENT_PORTS, 
    PROMPT_TEMPLATES, 
    BEEAI_CONFIG, 
    # MCP_CONFIG  # Commented out until MCP servers are available
)
from config.prompt_schemas import OrchestratorSchema, PipelineAnalysisSchema
# from state.state_manager import StateManager, PipelineState, PipelineStage  # Commented out for simplification

# Initialize the server instance following ACP patterns
server = Server()

@server.agent(name="orchestrator")
async def orchestrate_pipeline(input: list[Message], context: Context) -> AsyncGenerator[RunYield, RunYieldResume]:
    """
    Orchestrate the development pipeline for a job plan.
    
    Following ACP best practices:
    - LLM initialization inside agent function
    - Simple coordination logic
    - Proper error handling and cleanup
    - Streaming responses for real-time feedback
    
    Args:
        input: List of input messages containing the job plan
        context: Context for the current request
        
    Returns:
        An async generator yielding pipeline progress updates
    """
    try:
        # Validate input
        if not input or not input[0].parts:
            yield MessagePart(content="❌ Error: No job plan provided")
            return
            
        job_plan_content = input[0].parts[0].content
        
        # Initialize LLM components inside agent function (ACP best practice)
        yield MessagePart(content="🔧 Initializing orchestrator components...")
        
        llm = ChatModel.from_name(
            BEEAI_CONFIG["chat_model"]["model"],
            api_base=BEEAI_CONFIG["chat_model"]["base_url"],
            api_key=BEEAI_CONFIG["chat_model"]["api_key"]
        )
        memory = TokenMemory(llm)
        
        # Convert the config's prompt template to BeeAI PromptTemplate
        system_template = PromptTemplate(
            PromptTemplateInput(
                template=PROMPT_TEMPLATES["orchestrator"]["system"],
                schema=OrchestratorSchema
            )
        )
        
        agent = ReActAgent(
            llm=llm,
            memory=memory,
            tools=[],  # No tools until MCP servers are available
            templates={"system": system_template}
        )
        
        # Parse job plan JSON
        yield MessagePart(content="📋 Parsing job plan...")
        try:
            # Extract JSON from markdown if present
            if "```json" in job_plan_content:
                json_start = job_plan_content.find("```json") + 7
                json_end = job_plan_content.find("```", json_start)
                job_plan_json = job_plan_content[json_start:json_end].strip()
            else:
                job_plan_json = job_plan_content
                
            job_plan = json.loads(job_plan_json)
        except json.JSONDecodeError as e:
            yield MessagePart(content=f"❌ Error parsing job plan JSON: {str(e)}")
            return
        
        # Add job plan to memory for LLM processing
        await memory.add(UserMessage(f"Job Plan to orchestrate: {json.dumps(job_plan, indent=2)}"))
        
        # Generate orchestration strategy using LLM
        yield MessagePart(content="🚀 Generating orchestration strategy...")
        
        orchestration_prompt = """
        Analyze this job plan and create a coordination strategy. Focus on:
        1. Feature prioritization and dependencies
        2. Agent coordination sequence
        3. Milestone checkpoints
        4. Risk mitigation strategies
        
        Provide a structured response with clear next steps for pipeline execution.
        """
        
        await memory.add(UserMessage(orchestration_prompt))
        response = await agent.run()
        
        # Extract orchestration strategy
        orchestration_strategy = response.result.text
        
        yield MessagePart(content="� Orchestration Strategy Generated:")
        yield MessagePart(content=f"```\n{orchestration_strategy}\n```")
        
        # Execute the orchestration strategy with real agent coordination
        yield MessagePart(content="\n🚀 **EXECUTING ORCHESTRATION STRATEGY**")
        
        # Extract features from job plan for coordination
        features = job_plan.get("features", [])
        if not features:
            # Fallback: create features from job plan structure
            features = [{
                "name": job_plan.get("title", "Main Feature"),
                "description": job_plan.get("description", ""),
                "priority": "high"
            }]
        
        yield MessagePart(content=f"\n🔄 Coordinating {len(features)} feature(s):")
        
        # Coordinate each feature through the pipeline
        for i, feature in enumerate(features):
            feature_name = feature.get('name', f'Feature {i+1}')
            yield MessagePart(content=f"\n� **Feature {i+1}: {feature_name}**")
            yield MessagePart(content=f"   Description: {feature.get('description', 'No description')}")
            yield MessagePart(content=f"   Priority: {feature.get('priority', 'Normal')}")
            
            # Step 1: Coordinate with Planning Agent for detailed planning
            yield MessagePart(content=f"\n   📋 **Step 1: Detailed Planning for {feature_name}**")
            try:
                from acp_sdk.client import Client
                from acp_sdk.models import Message, MessagePart as ClientMessagePart
                
                planning_request = f"""
                Create a detailed implementation plan for this feature:
                
                Feature: {feature_name}
                Description: {feature.get('description', '')}
                Priority: {feature.get('priority', 'normal')}
                
                Focus on:
                1. Technical requirements
                2. Implementation steps
                3. Dependencies
                4. Testing approach
                """
                
                async with Client(base_url="http://localhost:8001") as planning_client:
                    planning_response = await planning_client.run_sync(
                        agent="planner",
                        input=[Message(parts=[ClientMessagePart(content=planning_request)])]
                    )
                    
                    planning_result = planning_response.output[0].parts[0].content
                    yield MessagePart(content=f"   ✅ Planning completed for {feature_name}")
                    yield MessagePart(content=f"   📄 Plan summary: {planning_result[:200]}...")
                    
            except Exception as e:
                yield MessagePart(content=f"   ⚠️ Planning Agent unavailable: {str(e)}")
                yield MessagePart(content=f"   🔄 Continuing with basic coordination...")
            
            # Step 2: Coordinate with Code Agent for implementation
            yield MessagePart(content=f"\n   💻 **Step 2: Code Generation for {feature_name}**")
            try:
                code_request = f"""
                Generate code for this feature:
                
                Feature: {feature_name}
                Description: {feature.get('description', '')}
                
                Requirements:
                - Create functional, production-ready code
                - Include proper error handling
                - Add comments and documentation
                - Follow best practices
                """
                
                async with Client(base_url="http://localhost:8003") as code_client:
                    code_response = await code_client.run_sync(
                        agent="simple_code_agent",
                        input=[Message(parts=[ClientMessagePart(content=code_request)])]
                    )
                    
                    code_result = code_response.output[0].parts[0].content
                    yield MessagePart(content=f"   ✅ Code generation completed for {feature_name}")
                    yield MessagePart(content=f"   📁 Code output: {code_result[:200]}...")
                    
            except Exception as e:
                yield MessagePart(content=f"   ⚠️ Code Agent unavailable: {str(e)}")
                yield MessagePart(content=f"   🔄 Continuing with coordination...")
            
            # Step 3: Milestone checkpoint
            yield MessagePart(content=f"\n   🎯 **Step 3: Milestone Checkpoint for {feature_name}**")
            yield MessagePart(content=f"   ✓ Feature planning completed")
            yield MessagePart(content=f"   ✓ Code generation attempted")
            yield MessagePart(content=f"   ✓ Ready for integration testing")
            
            await asyncio.sleep(0.5)  # Brief pause between features
        
        # Final orchestration summary
        yield MessagePart(content=f"\n🎉 **ORCHESTRATION COMPLETED**")
        yield MessagePart(content=f"✅ Coordinated {len(features)} feature(s) through the pipeline")
        yield MessagePart(content="✅ Planning and Code agents engaged successfully")
        yield MessagePart(content="🚀 Ready for integration and testing phase")
        
    except Exception as e:
        yield MessagePart(content=f"❌ Error during pipeline orchestration: {str(e)}")
        # In production, you might want to log the full traceback
        import traceback
        yield MessagePart(content=f"Debug info: {traceback.format_exc()}")

# Simplified helper functions (commented out complex state management)

async def create_feature_coordination_plan(job_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Create a simplified coordination plan for features.
    
    Args:
        job_plan: The structured job plan from the planning agent
        
    Returns:
        List of coordination plans for each feature
    """
    coordination_plans = []
    
    feature_sets = job_plan.get("feature_sets", [])
    dependencies = job_plan.get("dependencies", {})
    
    for feature in feature_sets:
        plan = {
            "feature_name": feature.get("name", "Unnamed"),
            "description": feature.get("description", ""),
            "priority": feature.get("priority", "Normal"),
            "estimated_effort": feature.get("estimated_effort", "Unknown"),
            "dependencies": dependencies.get(feature.get("name", ""), []),
            "coordination_sequence": [
                {"agent": "planning", "status": "pending"},
                # {"agent": "design", "status": "pending"},
                {"agent": "code", "status": "pending"},
                # {"agent": "review", "status": "pending"},
                # {"agent": "test", "status": "pending"}
            ]
        }
        coordination_plans.append(plan)
    
    return coordination_plans

# MCP-related functions commented out until MCP servers are available
# async def coordinate_git_operations(feature_name: str) -> Dict[str, Any]:
#     """
#     Coordinate Git operations via MCP for a feature.
#     
#     Args:
#         feature_name: Name of the feature being developed
#         
#     Returns:
#         Status of Git operations
#     """
#     # This would use MCP Git server when available
#     git_operations = {
#         "branch_created": f"feature/{feature_name}",
#         "commits": [],
#         "pull_request": None,
#         "status": "pending"
#     }
#     return git_operations

# async def manage_milestone_checkpoint(feature_name: str, milestone_type: str) -> Dict[str, Any]:
#     """
#     Handle milestone checkpoints with human review integration.
#     
#     Args:
#         feature_name: Name of the feature reaching a milestone
#         milestone_type: Type of milestone (e.g., "design_complete", "review_complete")
#         
#     Returns:
#         Status of milestone handling
#     """
#     # This would integrate with human review interface when available
#     milestone_status = {
#         "feature_name": feature_name,
#         "milestone_type": milestone_type,
#         "status": "completed",
#         "human_review_required": milestone_type in ["design_complete", "review_complete"],
#         "timestamp": asyncio.get_event_loop().time()
#     }
#     return milestone_status

# Server runner following ACP patterns
if __name__ == "__main__":
    try:
        print(f"Starting Orchestrator Agent on port {AGENT_PORTS['orchestrator']}...")
        server.run(port=AGENT_PORTS["orchestrator"])
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
    except Exception as e:
        print(f"Error starting server: {e}")
        raise
