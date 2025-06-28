# Job Pipeline Implementation Plan

## System Architecture

```
User ────────→ Job Planning ─────→ Orchestrator
 ↑                                     │
 │                                     ↓
 │                              Agent Pipeline
 │                 ┌─Spec─→Design→Code→Review→Test─┐
 │                 │                              │
 │                 ↓                              │
 │         [Milestone Complete]                   │
 │                 │                              │
 │          [HUMAN REVIEW By Git Pull Request]    │
 │                 │                              │
 │                 ↓                              │
 │        ┌─Spec─→Design→Code→Review→Test─┐        │
 │        │      (Enhanced Features)      │        │
 │        ↓                              │        │
 │[Feature Set Milestone Complete]       │        │
 │        │                              │        │
 │ [HUMAN REVIEW]                        │        │
 │        │                              │        │
 │        ↓                              ↓        │
 │       Further Phases ─────────────────┘        │
 │                 │                              │
 └─────────────────┴──────────────────────────────┘
```

## Implementation Overview

This document outlines the implementation plan for a modular job pipeline system using Agent Communication Protocol (ACP) with integrated human review checkpoints via Git Pull Requests. The system follows a structured flow with clear separation between planning, orchestration, and execution phases.

## Core Components

### 1. Job Planning Phase

The entry point where user requests are processed and translated into actionable job plans.

- **Component**: Job Planning Agent
- **Files**:
  - `/Users/lechristopherblackwell/Desktop/Ground_up/rebuild/agents/planning/planning_agent.py`
  - `/Users/lechristopherblackwell/Desktop/Ground_up/rebuild/agents/planning/server.py`
  - `/Users/lechristopherblackwell/Desktop/Ground_up/rebuild/agents/planning/prompt_templates.py`

- **Responsibilities**:
  - Parse user requests and define scope
  - Create structured job plans with clear objectives
  - Identify potential feature sets or work units
  - Provide initial guidance for the Orchestrator

### 2. Orchestrator

The central controller that manages the entire workflow and coordinates between phases.

- **Component**: Orchestrator Agent
- **Files**:
  - `/Users/lechristopherblackwell/Desktop/Ground_up/rebuild/agents/orchestrator/orchestrator_agent.py`
  - `/Users/lechristopherblackwell/Desktop/Ground_up/rebuild/agents/orchestrator/server.py`
  - `/Users/lechristopherblackwell/Desktop/Ground_up/rebuild/agents/orchestrator/workflow_manager.py`
  - `/Users/lechristopherblackwell/Desktop/Ground_up/rebuild/agents/orchestrator/pipeline_coordinator.py`
  - `/Users/lechristopherblackwell/Desktop/Ground_up/rebuild/agents/orchestrator/state_manager.py`

- **Responsibilities**:
  - Break down job plans into discrete feature sets
  - Initialize and coordinate multiple agent pipelines (parallel or sequential)
  - Track milestone completion and orchestrate human reviews
  - Manage state throughout the execution lifecycle
  - Handle Git operations via MCP for milestone reviews

### 3. Agent Pipeline

The core execution unit that processes feature sets through a defined development lifecycle.

- **Component**: Pipeline Agents (Spec, Design, Code, Review, Test)
- **Files**:
  - `/Users/lechristopherblackwell/Desktop/Ground_up/rebuild/agents/pipeline/spec_agent.py`
  - `/Users/lechristopherblackwell/Desktop/Ground_up/rebuild/agents/pipeline/design_agent.py`
  - `/Users/lechristopherblackwell/Desktop/Ground_up/rebuild/agents/pipeline/code_agent.py`
  - `/Users/lechristopherblackwell/Desktop/Ground_up/rebuild/agents/pipeline/review_agent.py`
  - `/Users/lechristopherblackwell/Desktop/Ground_up/rebuild/agents/pipeline/test_agent.py`
  - `/Users/lechristopherblackwell/Desktop/Ground_up/rebuild/agents/pipeline/server.py`

- **Agent Pipeline Stages**:
  - **Spec**: Define requirements and functionality specifications
  - **Design**: Create technical architecture and component designs
  - **Code**: Implement the design according to specifications
  - **Review**: Perform automated code review and quality checks
  - **Test**: Write and execute tests to validate functionality

### 4. Milestone & Human Review Integration

The critical checkpoints where human oversight ensures quality and alignment with goals.

- **Component**: Human Review Interface & Git Integration
- **Files**:
  - `/Users/lechristopherblackwell/Desktop/Ground_up/rebuild/services/review/app.py`
  - `/Users/lechristopherblackwell/Desktop/Ground_up/rebuild/services/review/api.py`
  - `/Users/lechristopherblackwell/Desktop/Ground_up/rebuild/services/mcp/git_tools.py`
  - `/Users/lechristopherblackwell/Desktop/Ground_up/rebuild/services/mcp/pr_generator.py`

- **Responsibilities**:
  - Format milestone outputs for review
  - Create Git Pull Requests with structured information
  - Provide interfaces for human review and feedback
  - Process review decisions and relay to Orchestrator
  - Manage the Git workflow for iterative improvements

### 5. Multiple Pipeline Coordination

Support for parallel or sequential agent pipelines to handle complex jobs.

- **Component**: Pipeline Coordinator
- **Files**:
  - `/Users/lechristopherblackwell/Desktop/Ground_up/rebuild/agents/orchestrator/pipeline_coordinator.py`
  - `/Users/lechristopherblackwell/Desktop/Ground_up/rebuild/agents/orchestrator/parallel_execution.py`

- **Responsibilities**:
  - Manage multiple pipeline instances
  - Coordinate dependencies between pipelines
  - Handle resource allocation for parallel execution
  - Synchronize milestones and reviews across pipelines

## Reference Examples

For each component of our implementation, we'll leverage patterns from existing ACP examples:

### Orchestrator Implementation References

- **Agent Orchestration Pattern**: See `/Users/lechristopherblackwell/Desktop/Ground_up/acp_examples/examples/python/beeai-orchestrator/agent.py` - Demonstrates coordinating multiple agents with specific responsibilities, similar to our pipeline coordination.
- **Tool-based Agent Communication**: See `/Users/lechristopherblackwell/Desktop/Ground_up/acp_examples/examples/python/beeai-orchestrator/translation_tool.py` - Pattern for defining structured agent-to-agent communication, applicable to our pipeline stages.
- **ACPCallingAgent Pattern**: See `/Users/lechristopherblackwell/Desktop/Ground_up/ACPWalkthrough/6. ACPCallingAgent.py` - Demonstrates how to build an agent that calls other agents, which is essential for our Orchestrator.

### State Management References

- **TokenMemory Pattern**: See `beeai_framework.memory.TokenMemory` used in `/Users/lechristopherblackwell/Desktop/Ground_up/acp_examples/examples/python/beeai-orchestrator/agent.py` - Model for implementing state persistence.
- **Session Management**: See `/Users/lechristopherblackwell/Desktop/Ground_up/acp_examples/examples/python/basic/clients/session.py` - Pattern for maintaining session state across interactions.

### MCP Integration References

- **MCP Tool Collection**: See `/Users/lechristopherblackwell/Desktop/Ground_up/ACPWalkthrough/7. ACPxMCP.py` - Example of exposing external tools (like Git operations) to ACP agents through MCP.
- **MCP Server Setup**: See `/Users/lechristopherblackwell/Desktop/Ground_up/ACPWalkthrough/mcpserver.py` - Pattern for defining MCP tools that will be adapted for Git operations.

### Pipeline Agent References

- **Chained Agents**: See `/Users/lechristopherblackwell/Desktop/Ground_up/ACPWalkthrough/5. Chained Agents.py` - Pattern for sequencing agents in a pipeline flow.
- **Tool Definition Pattern**: See `TranslateToolInput`/`TranslateToolResult` in `/Users/lechristopherblackwell/Desktop/Ground_up/acp_examples/examples/python/beeai-orchestrator/translation_tool.py` - Example of structured data exchange between agents.
- **RAG Implementation**: See `/Users/lechristopherblackwell/Desktop/Ground_up/acp_examples/examples/python/llama-index-rag/agent.py` - Pattern for implementing context-aware agents (useful for our code and review agents).

### Human Review Interface References

- **BeeAI Chat**: See `/Users/lechristopherblackwell/Desktop/Ground_up/acp_examples/examples/python/beeai-chat` - UI pattern adaptable for our Streamlit-based human review interface.
- **Client Implementation**: See `/Users/lechristopherblackwell/Desktop/Ground_up/ACPWalkthrough/8. ACPxMCP Client.py` - Pattern for client interaction with MCP-integrated ACP agents.

### Parallelization Pattern References

- **Parallel Agent Execution**: See `/Users/lechristopherblackwell/Desktop/Ground_up/acp_examples/examples/python/beeai-parallelization/agent.py` - Demonstrates running multiple agents concurrently using asyncio, which will be critical for our multi-pipeline execution strategy.
- **Task Coordination**: See `asyncio.gather` pattern in the parallelization example - This approach will be adapted for coordinating concurrent feature set pipelines while maintaining proper synchronization at milestone points.

### MCP Git Integration Example Pattern

For integrating Git operations via MCP, we'll implement a pattern similar to the MCP server in ACPWalkthrough, but adapted for Git operations:

```python
# Example MCP Git tool integration (will be implemented in /Users/lechristopherblackwell/Desktop/Ground_up/rebuild/mcp/git_tools.py)

from mcp.server.fastmcp import FastMCP
import git
import os
from dotenv import load_dotenv

# Load environment variables using dotenv (following user rules)
load_dotenv()

# Create an MCP server for Git operations
mcp = FastMCP("git_operations")

# Repository path configuration
repo_path = os.getenv("GIT_REPO_PATH")
repo = git.Repo(repo_path)

@mcp.tool()
def create_branch(branch_name: str, from_branch: str = "main"):
    """Create a new Git branch from the specified base branch."""
    try:
        # Checkout the base branch first
        repo.git.checkout(from_branch)
        # Create and checkout the new branch
        repo.git.checkout("-b", branch_name)
        return {"success": True, "branch": branch_name}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def commit_changes(message: str, files: list[str] = None):
    """Commit changes to the current branch with the specified message.
    If files is None, commit all changes."""
    try:
        if files:
            for file in files:
                repo.git.add(file)
        else:
            repo.git.add(".")
        
        # Create the commit
        repo.git.commit("-m", message)
        return {"success": True, "message": message}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def create_pull_request(title: str, description: str, base_branch: str = "main"):
    """Create a pull request from the current branch to the base branch."""
    try:
        from github import Github
        
        # Get GitHub token from env vars
        github_token = os.getenv("GIT_TOKEN")
        github_repo_name = os.getenv("GIT_REPO_NAME")
        
        # Initialize GitHub client
        g = Github(github_token)
        github_repo = g.get_repo(github_repo_name)
        
        # Get the current branch name
        current_branch = repo.active_branch.name
        
        # Create the pull request
        pr = github_repo.create_pull(
            title=title,
            body=description,
            base=base_branch,
            head=current_branch
        )
        
        return {
            "success": True, 
            "pr_number": pr.number,
            "pr_url": pr.html_url
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    # Run the MCP server, which will expose these Git operations as tools
    # for ACP agents to call
    mcp.run()
```

## Implementation Details

### Workflow Engine

The core workflow logic will be implemented as a state machine that tracks:

1. **Pipeline States**:
   - `initializing`: Pipeline is being set up
   - `spec_phase`: Requirements specification in progress
   - `design_phase`: Design in progress
   - `code_phase`: Implementation in progress
   - `review_phase`: Code review in progress
   - `test_phase`: Testing in progress
   - `milestone_ready`: Ready for human review
   - `human_review`: Under human review
   - `revision_needed`: Changes required after review
   - `milestone_approved`: Review passed, ready for next phase
   - `complete`: Pipeline fully completed

2. **Feature Set Tracking**:
   - Basic features (initial milestone)
   - Enhanced features (second milestone)
   - Additional feature sets as needed

3. **Git Integration Points**:
   - Branch creation (`git_create_branch`)
   - Milestone commits (`git_commit`)
   - Pull Request creation (`git_create_pr`)
   - Merge operations (`git_merge`)

### State Schema (Enhanced)

Project state will be stored as JSON files with support for multiple pipelines:

```json
{
  "project_id": "unique-id",
  "name": "Project Name",
  "requirements": "Original user requirements",
  "job_plan": {
    "objectives": ["..."],
    "feature_sets": [
      {"id": "fs-1", "name": "Basic Features", "description": "..."},
      {"id": "fs-2", "name": "Enhanced Features", "description": "..."}
    ]
  },
  "pipelines": [
    {
      "id": "pipeline-1",
      "feature_set_id": "fs-1",
      "status": "milestone_approved",
      "current_stage": null,
      "stages_completed": ["spec", "design", "code", "review", "test"],
      "artifacts": {
        "spec": { "content": "...", "status": "approved" },
        "design": { "content": "...", "status": "approved" },
        "code": { "files": [...], "status": "approved" },
        "review": { "comments": [...], "status": "passed" },
        "test": { "results": [...], "status": "passed" }
      },
      "git": {
        "branch": "feature/basic-implementation",
        "pr_url": "https://github.com/username/repo/pull/1",
        "merge_status": "merged"
      },
      "human_review": {
        "requested_at": "timestamp",
        "completed_at": "timestamp",
        "comments": "Human feedback",
        "decision": "approve"
      }
    },
    {
      "id": "pipeline-2",
      "feature_set_id": "fs-2",
      "status": "code_phase",
      "current_stage": "code",
      "stages_completed": ["spec", "design"],
      "artifacts": {
        "spec": { "content": "...", "status": "approved" },
        "design": { "content": "...", "status": "approved" },
        "code": { "files": [], "status": "in_progress" }
      },
      "git": {
        "branch": "feature/enhanced-implementation",
        "pr_url": null,
        "merge_status": null
      },
      "human_review": null
    }
  ]
}
```

### MCP Git Integration (Enhanced)

The MCP server will expose Git operations specifically tailored for the pipeline workflow:

1. **Pipeline Branch Management**:
   - `git_init_pipeline`: Set up initial repository structure for a pipeline
   - `git_create_feature_branch`: Create a branch for a specific feature set

2. **Milestone Operations**:
   - `git_prepare_milestone`: Stage files and prepare milestone commit
   - `git_create_milestone_pr`: Create a formatted PR with milestone details
   - `git_update_pr_with_review_feedback`: Update PR with human review feedback

3. **Workflow Operations**:
   - `git_merge_approved_milestone`: Merge approved milestone into main branch
   - `git_prepare_next_phase`: Set up branches for the next development phase

### Agent Communication Flow

```
│                                                │
▼                                                │
Job Planning ─→ generates job plan ──────────────┼───────────→ Orchestrator
                                                │              │
                                                │              ▼
                                                │       Analyze & Decompose
                                                │              │
                                                │              ▼
                            ┌───────────────────┼─────── Create Feature Sets
                            │                   │              │
┌──────────────┬────────────┴────┬─────────────┬┘              │
│              │                 │             │               │
▼              ▼                 ▼             ▼               │
Pipeline 1     Pipeline 2        Pipeline 3    Pipeline N ◄────┘
│              │                 │             │
▼              ▼                 ▼             ▼
Spec           Spec              Spec          Spec
│              │                 │             │
▼              ▼                 ▼             ▼
Design         Design            Design        Design
│              │                 │             │
▼              ▼                 ▼             ▼
Code           Code              Code          Code
│              │                 │             │
▼              ▼                 ▼             ▼
Review         Review            Review        Review
│              │                 │             │
▼              ▼                 ▼             ▼
Test           Test              Test          Test
│              │                 │             │
▼              ▼                 ▼             ▼
PR Creation    PR Creation       PR Creation   PR Creation
│              │                 │             │
▼              ▼                 ▼             ▼
Human Review   Human Review      Human Review  Human Review
│              │                 │             │
└──────────────┴─────────────────┴─────────────┘
                          │
                          ▼
                   Orchestrator (Next Phase)
```

## Implementation Phases

### Phase 1: Core Infrastructure (1-2 days)

1. Set up virtual environment and dependencies with uv
2. Create directory structure and base configurations
3. Implement centralized LLM configuration
4. Set up basic ACP server templates

### Phase 2: Job Planning & Orchestration (2-3 days)

1. Implement Job Planning Agent and server
2. Implement Orchestrator Agent and state management
3. Create feature set decomposition logic
4. Set up pipeline initiation mechanisms

### Phase 3: Agent Pipeline Components (3-4 days)

1. Implement each pipeline stage agent
   - Spec Agent
   - Design Agent
   - Code Agent
   - Review Agent
   - Test Agent
2. Create server interfaces for each agent
3. Implement state tracking for pipeline stages

### Phase 4: MCP Git Integration (2 days)

1. Implement MCP server with Git operations
2. Create PR formatting and template generation
3. Implement branch management for feature sets
4. Set up milestone tracking and Git workflow

### Phase 5: Human Review Interface (2 days)

1. Create Streamlit interface for milestone reviews
2. Implement API for review submission
3. Set up notification mechanism for review requests
4. Create dashboard for project status monitoring

### Phase 6: Parallel Pipeline Support (1-2 days)

1. Enhance Orchestrator for multi-pipeline management
2. Implement synchronization for dependent pipelines
3. Create resource allocation for parallel execution
4. Add conflict resolution mechanisms

### Phase 7: Integration & Testing (2-3 days)

1. End-to-end testing with simple projects
2. System validation across multiple pipelines
3. Performance testing and optimization
4. Documentation and usage examples

## Technical Stack

- **Language**: Python 3.13.5
- **Dependency Management**: uv + requirements.txt
- **Environment Management**: dotenv for configuration
- **LLM Integration**: Centralized in config.py
- **State Storage**: JSON files for MVP
- **Human Review Interface**: Streamlit
- **Git Integration**: Through MCP tools
- **Agent Communication**: ACP SDK

## Configuration Details

### Environment Setup (.env)

```
# LLM Configuration
LLM_PROVIDER=ollama
LLM_MODEL=qwen2.5:14b
LLM_API_BASE=http://localhost:11434

# Agent Endpoints
PLANNING_AGENT_PORT=8001
ORCHESTRATOR_AGENT_PORT=8002
PIPELINE_SPEC_PORT=8003
PIPELINE_DESIGN_PORT=8004
PIPELINE_CODE_PORT=8005
PIPELINE_REVIEW_PORT=8006
PIPELINE_TEST_PORT=8007
MCP_SERVER_PORT=8008

# Review Interface
REVIEW_INTERFACE_PORT=8080

# Git Configuration
GIT_USERNAME=your-username
GIT_TOKEN=your-token
GIT_REPO_URL=https://github.com/username/repo
```

### Starting the System

1. Start all agent servers:
```bash
./start_agents.sh
```

2. Start the MCP server:
```bash
./start_mcp.sh
```

3. Start the review interface:
```bash
./start_review.sh
```

4. Run the client:
```bash
python client.py "Create a to-do list application with user authentication"
```

## Benefits of This Implementation

1. **Modularity**: Each agent focuses on one specific task
2. **Scalability**: Multiple pipelines can work in parallel
3. **Auditability**: All steps are tracked and reviewable
4. **Human-AI Collaboration**: Strategic human oversight points
5. **Flexibility**: Can handle different project types and sizes
6. **Iterative Improvement**: Multiple review cycles for quality

---

This implementation leverages ACP for agent communication and MCP for system operations like Git, creating a powerful, modular system that follows best practices for AI agent orchestration while maintaining human oversight at critical milestones.
