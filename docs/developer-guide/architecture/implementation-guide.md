# ACP Modular Multi-Agent Job Pipeline Implementation Instructions

## OVERVIEW
You are implementing a sophisticated ACP-based modular autonomous multi-agent software development pipeline. All scaffolding, pseudocode, and optimized agent prompts are already complete in `/Users/lechristopherblackwell/Desktop/Ground_up/rebuild/complex_team/job_pipeline/`. Your job is to transform the detailed pseudocode into working ACP agent implementations. Implement Unit, Function, and Integration tests for each agent. A Phase Cannot be Considered Complete Until the Tests are Built, Reviewed for Efficiency (Dont Build Tests which dont offer value), and Approved by the Lead Engineer.

## ARCHITECTURE SUMMARY
- **Planning Agent**: Decomposes user requests into parallel-executable feature sets
- **Orchestrator Agent**: Coordinates multi-agent workflows with dynamic session management
- **Specification Agent**: Creates detailed requirements with RAG-enhanced research
- **Design Agent**: Generates technical architecture and implementation blueprints
- **Code Agent**: Implements production-ready code with MCP Git integration
- **Review Agent**: Performs comprehensive code quality analysis
- **Test Agent**: Generates and executes comprehensive test suites
- **Infrastructure**: StateManager, MCP Git Tools, Streamlit Review UI

## IMPLEMENTATION PHASES

### PHASE 1: Foundation & Base Agent (Context Window 1)
**Objective**: Establish core ACP infrastructure and base agent pattern

**Files to implement**:
- `agents/base_agent.py` - Complete the BaseAgent class following ACP server patterns from `/acp_examples/examples/python/basic/servers/llm.py`
- `config/config.py` - Already optimized, verify environment variable loading with dotenv
- Create `.env.example` file with all required environment variables

**Key Requirements**:
- Use `uv` virtual environment (already specified in user rules)
- Implement ACP Server initialization with proper error handling
- Add logging and telemetry following `/acp_examples/examples/python/basic/servers/telemetry.py`
- Create reusable session management patterns from `acp-agent-generator`
- Test basic ACP server startup on configured ports

**Validation**: BaseAgent should start successfully and respond to basic ACP protocol messages.

### PHASE 2: Planning & Orchestrator Agents (Context Window 2)
**Objective**: Implement the cognitive coordination layer

**Files to implement**:
- `agents/planning/planning_agent.py` - Transform pseudocode into working planner
- `agents/orchestrator/orchestrator_agent.py` - Implement pipeline coordination logic

**Key Requirements**:
- Planning Agent must output structured JSON matching the format specified in PROMPT_TEMPLATES
- Orchestrator must implement dynamic agent session creation following `acp-agent-generator` patterns
- Use SessionManager patterns for agent lifecycle management
- Implement streaming progress updates using AsyncGenerator patterns
- Add proper error handling and graceful degradation

**Integration Points**:
- Planning Agent receives user requests, outputs structured job plans
- Orchestrator consumes job plans, coordinates agent pipeline execution
- Both agents must integrate with StateManager for persistence

**Validation**: Create a simple end-to-end test where Planning Agent creates a job plan and Orchestrator can parse and route it.

### PHASE 3: Specification & Design Agents (Context Window 3)
**Objective**: Implement the analysis and architecture layer

**Files to implement**:
- `agents/specification/specification_agent.py`
- `agents/design/design_agent.py`

**Key Requirements**:
- Specification Agent must integrate RAG capabilities following `/acp_examples/examples/python/llama-index-rag/agent.py`
- Design Agent must generate comprehensive technical designs with clear implementation guidance
- Both agents must stream incremental outputs using AsyncGenerator
- Implement research integration patterns from `gpt-researcher` example
- Add structured output validation to ensure downstream consumption

**Integration Points**:
- Specification Agent consumes feature sets from Planning Agent
- Design Agent consumes specifications and produces technical blueprints
- Both must update StateManager with artifacts and progress

**Validation**: Feed a sample feature description through Planning → Specification → Design pipeline.

### PHASE 4: Code & Review Agents (Context Window 4)
**Objective**: Implement the production pipeline (code generation + quality assurance)

**Files to implement**:
- `agents/code/code_agent.py`
- `agents/review/review_agent.py`

**Key Requirements**:
- Code Agent must integrate with MCP Git Tools for version control operations
- Follow MCP integration patterns from `/acp_examples/ACPxMCP.py`
- Code Agent must generate production-ready code with comprehensive error handling
- Review Agent must perform multi-dimensional analysis (security, performance, maintainability)
- Both agents must stream structured feedback for orchestrator consumption

**Integration Points**:
- Code Agent consumes design blueprints and produces Git-committed implementations
- Review Agent analyzes code against original specifications
- Review Agent must generate actionable feedback for potential code iteration

**Validation**: Generate code from a design, commit it via MCP Git tools, and run it through review analysis.

### PHASE 5: Test Agent & MCP Integration (Context Window 5)
**Objective**: Complete the validation pipeline and Git operations

**Files to implement**:
- `agents/testing/test_agent.py`
- `mcp/git_tools.py` (MCP server implementation)

**Key Requirements**:
- Test Agent must generate comprehensive test suites covering unit, integration, and edge cases
- MCP Git Tools must implement branch management, commits, and pull request creation
- Test Agent must execute tests and provide structured reporting
- Follow MCP server patterns for proper tool exposure
- Implement GitHub API integration for pull request workflows

**Integration Points**:
- Test Agent validates code implementations against specifications
- MCP Git Tools coordinates with Code Agent for version control
- Test reports feed back to Review Agent and Orchestrator for pipeline decisions

**Validation**: Complete end-to-end pipeline from user request to tested, committed code with pull request.

### PHASE 6: State Management & Human Review UI (Context Window 6)
**Objective**: Complete the persistence and human-in-the-loop systems

**Files to implement**:
- `state/state_manager.py`
- `ui/review_app.py` (Streamlit application)

**Key Requirements**:
- StateManager must implement thread-safe pipeline state tracking
- Follow ACP store patterns from `/acp_examples/examples/python/basic/servers/store.py`
- Streamlit UI must integrate with ACP clients for real-time pipeline visibility
- Implement human feedback collection and pipeline continuation/remediation
- Add proper session management and authentication

**Integration Points**:
- StateManager persists all pipeline artifacts and progress across agents
- Review UI provides human oversight at critical milestones
- Human feedback must integrate back into pipeline decision-making

**Validation**: Run complete pipeline with human review checkpoints and state persistence.

## CRITICAL IMPLEMENTATION NOTES

### Environment & Dependencies
- ALWAYS use `uv` virtual environment (user rule)
- Use `dotenv` for environment variable management (user rule)
- All LLM configurations must be centralized in `config.py` (user rule)
- Reference existing optimized PROMPT_TEMPLATES in config.py

### ACP Integration Patterns
- Study `/acp_examples/examples/python/` extensively before implementing
- Use `acp-agent-generator` as primary reference for Orchestrator patterns
- Follow streaming patterns from basic clients for incremental outputs
- Implement proper error handling and graceful degradation

### Testing Strategy
- Test each phase independently before integration
- Use simple, focused test cases to validate ACP protocol compliance
- Validate agent-to-agent communication patterns
- Test human review workflows end-to-end

### Development Approach
- Implement one phase completely before moving to the next
- Validate each agent individually, then test integration points
- Use the comprehensive pseudocode as your implementation guide
- Reference specific ACP examples mentioned in the pseudocode comments

## SUCCESS CRITERIA
- Complete autonomous pipeline from user request to tested, reviewed, committed code
- Human review integration at design, code review, and test validation milestones
- Proper Git workflow with branch management and pull requests
- Real-time pipeline visibility through Streamlit UI
- Comprehensive state persistence and audit trails

---

[← Back to Architecture](../architecture/) | [← Back to Developer Guide](../../developer-guide/) | [← Back to Docs](../../../)