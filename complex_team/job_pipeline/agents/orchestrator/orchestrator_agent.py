"""Orchestrator Agent for coordinating the job pipeline workflow.

This is the central controller for the entire development workflow,
managing multiple agent pipelines and coordinating between phases.

Based on reference pattern from beeai-orchestrator agent.py and ACPCallingAgent pattern.
"""

import asyncio
import json
import uuid
from collections.abc import AsyncGenerator
from typing import Dict, List, Any, Optional, AsyncGenerator
from acp_sdk.models import Message, MessagePart
from acp_sdk.server import Context, Server, RunYield, RunYieldResume
from beeai_framework.agents.react import ReActAgent
from beeai_framework.backend.chat import ChatModel
from beeai_framework.memory import TokenMemory
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
    MCP_CONFIG
)
from config.prompt_schemas import OrchestratorSchema, PipelineAnalysisSchema
from state.state_manager import StateManager, PipelineState, PipelineStage

# Initialize the server instance directly
server = Server()

# Initialize the state manager for pipeline tracking
state_manager = StateManager()

# Initialize BeeAI Framework components for LLM capabilities
llm = ChatModel.from_name(
    BEEAI_CONFIG["chat_model"]["model"],  # Already contains provider prefix
    api_base=BEEAI_CONFIG["chat_model"]["base_url"],
    api_key=BEEAI_CONFIG["chat_model"]["api_key"]  # Get API key directly from config
)
memory = TokenMemory(llm)

# Convert the config's prompt template dictionary to a BeeAI PromptTemplate
system_template = PromptTemplate(
    PromptTemplateInput(
        template=PROMPT_TEMPLATES["orchestrator"]["system"],
        schema=OrchestratorSchema
    )
)

agent = ReActAgent(
    llm=llm,
    memory=memory,
    tools=[],
    templates={"system": system_template}
)

@server.agent(name="orchestrator")
async def orchestrate_pipeline(input: list[Message], context: Context) -> AsyncGenerator[RunYield, RunYieldResume]:
    """
    Orchestrate the development pipeline for a job plan.
    
    Args:
        input: List of input messages containing the job plan
        context: Context for the current request
        
    Returns:
        An async generator yielding pipeline progress updates
    """
    try:
        # Extract job plan from input
        if not input or not input[0].parts:
            yield MessagePart(content="Error: No job plan provided")
            return
            
        job_plan_content = input[0].parts[0].content
        
        # Parse job plan JSON
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
        
        # Initialize pipeline state
        yield MessagePart(content="🚀 Initializing pipeline orchestration...")
        await asyncio.sleep(0.5)
        
        # Create feature pipelines from job plan
        feature_pipelines = await create_feature_pipelines(job_plan)
        
        yield MessagePart(content=f"📋 Created {len(feature_pipelines)} feature pipeline(s)")
        await asyncio.sleep(0.5)
        
        # Execute pipelines
        for i, pipeline in enumerate(feature_pipelines):
            yield MessagePart(content=f"\n🔄 Executing Pipeline {i+1}: {pipeline['feature_name']}")
            
            # Ask LLM to analyze the pipeline and suggest execution strategy
            pipeline_description = json.dumps(pipeline, indent=2)
            
            analysis_prompt = PromptTemplate(
                PromptTemplateInput(
                    template=f"Analyze this feature pipeline and suggest an execution strategy:\n{pipeline_description}",
                    schema=PipelineAnalysisSchema
                )
            )
            llm_response = await agent.run(analysis_prompt)
            
            yield MessagePart(content=f"🧠 AI Analysis:\n{llm_response}")
            await asyncio.sleep(0.5)
            
            # Execute pipeline stages
            yield MessagePart(content=f"⚙️ Executing pipeline stages sequentially")
            await _execute_pipeline_stages(pipeline)
            
            yield MessagePart(content=f"✅ Pipeline {i+1} execution completed")
        
        # Final summary
        yield MessagePart(content="\n🏁 All pipelines executed successfully!")
        
    except Exception as e:
        yield MessagePart(content=f"❌ Error during pipeline orchestration: {str(e)}")

async def create_feature_pipelines(job_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Break down a job plan into multiple feature pipelines.
    
    Args:
        job_plan: The structured job plan from the planning agent
        
    Returns:
        List of feature pipelines to be executed
    """
    pipelines = []
    
    # Extract feature sets from job plan
    feature_sets = job_plan.get("feature_sets", [])
    dependencies = job_plan.get("dependencies", {})
    
    for feature in feature_sets:
        pipeline_id = str(uuid.uuid4())
        
        # Create pipeline state in state manager
        pipeline_state = await state_manager.create_pipeline(
            feature_name=feature["name"],
            repo_name=job_plan.get("job_id", "unknown")
        )
        
        pipeline = {
            "pipeline_id": pipeline_id,
            "feature_name": feature["name"],
            "description": feature["description"],
            "priority": feature["priority"],
            "estimated_effort": feature["estimated_effort"],
            "parallel_executable": feature["parallel_executable"],
            "dependencies": dependencies.get(feature["name"], []),
            "state": pipeline_state,
            "stages": [
                {"name": "specification", "status": "pending", "agent": "specification"},
                {"name": "design", "status": "pending", "agent": "design"},
                {"name": "coding", "status": "pending", "agent": "code"},
                {"name": "review", "status": "pending", "agent": "review"},
                {"name": "testing", "status": "pending", "agent": "test"}
            ]
        }
        
        pipelines.append(pipeline)
    
    return pipelines
    
async def _execute_pipeline_stages(pipeline: Dict[str, Any]):
    """
    Execute all stages of a pipeline sequentially.
    
    Args:
        pipeline: The pipeline to execute
    """
    for stage in pipeline["stages"]:
        # Update stage status to running
        await state_manager.update_stage_status(
            pipeline["pipeline_id"], 
            PipelineStage(stage["name"].upper()), 
            "running"
        )
        
        # Simulate stage execution
        await asyncio.sleep(1)  # Simulate work being done
        
        # Update stage status to completed
        await state_manager.update_stage_status(
            pipeline["pipeline_id"], 
            PipelineStage(stage["name"].upper()), 
            "completed"
        )
        
        # Check if this stage requires human review
        if stage["name"] in ["design", "review"]:
            await manage_milestone(pipeline["pipeline_id"], f"{stage['name']}_complete")

async def manage_milestone(pipeline_id: str, milestone_type: str) -> Dict[str, Any]:
    """
    Handle a milestone checkpoint in a pipeline.
    
    This includes Git operations via MCP (branch, commit, PR) and 
    coordination with the human review interface.
    
    Args:
        pipeline_id: Identifier for the pipeline reaching a milestone
        milestone_type: Type of milestone (e.g., "spec_complete", "design_complete")
        
    Returns:
        Status of milestone handling
    """
    # Simulate milestone handling
    # In a real implementation, this would:
    # 1. Create Git branch if needed
    # 2. Commit current work
    # 3. Create pull request for human review
    # 4. Wait for human approval
    # 5. Merge and continue pipeline
    
    milestone_status = {
        "pipeline_id": pipeline_id,
        "milestone_type": milestone_type,
        "status": "completed",
        "timestamp": asyncio.get_event_loop().time(),
        "human_review_required": milestone_type in ["design_complete", "review_complete"]
    }
    
    return milestone_status
