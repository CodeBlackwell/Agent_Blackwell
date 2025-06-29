# Complex Team - Job Pipeline

A modular, agent-based job pipeline system using the Agent Communication Protocol (ACP) with integrated human review checkpoints via Git Pull Requests. This system follows a structured workflow with clear separation between planning, orchestration, and execution phases.

## Architecture Overview

```
User ────────→ Job Planning ─────→ Orchestrator ─────→ Agent Pipeline(x N)
 ↑                                     │
 │                                     ↓
 │                              Agent Teams Pipeline
 │                 ┌Spec─→Design→Code→Review→Test─┐
 │                 │                              │
 │                 ↓                              │
 │         [Milestone Complete]                   │
 │                 │                              │
 │          [HUMAN REVIEW By Git Pull Request]    │
 │                 │                              │
 │                 ↓                              │
 │        ┌─Spec─→Design→Code→Review→Test┐        │
 │        │      (Enhanced Features)     │        │
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

### Core Components

1. **Job Planning Agent**: Entry point where user requests are processed and translated into actionable job plans
2. **Orchestrator Agent**: Central controller that manages workflow and coordinates between phases
3. **Pipeline Agents**: Specialized agents for each development phase
   - Specification Agent: Defines requirements and functionality specifications
   - Design Agent: Creates technical architecture and component designs
   - Code Agent: Implements the design according to specifications
   - Review Agent: Performs automated code review and quality checks
   - Test Agent: Writes and executes tests to validate functionality
4. **Human Review Integration**: Checkpoints where human oversight ensures quality and alignment with goals
5. **Multiple Pipeline Coordination**: Support for parallel or sequential agent pipelines to handle complex jobs

## Technology Stack

This project uses state-of-the-art technologies for agent-based development:

- **ACP SDK**: Agent Communication Protocol for standardized agent interactions
- **BeeAI Framework**: LLM integration for cognitive agents
- **MCP**: Model Context Protocol for tool integration
- **Python 3.13**: Modern Python features for efficient development
- **uv**: Fast, reliable Python package management and virtual environment tool
- **Pydantic**: Data validation and settings management
- **Centralized Configuration**: All LLM configurations and prompts follow the project rule of centralization

## Setup and Installation

### Option 1: Docker Setup (Recommended)

For the easiest setup experience, we've provided a Docker configuration that runs all services in containers:

```bash
cd job_pipeline
chmod +x run-docker.sh
./run-docker.sh
```

This will start all agent servers, the MCP Git Tools, and the UI in separate containers. 
See `job_pipeline/README-DOCKER.md` for detailed instructions and troubleshooting.

### Option 2: Manual Setup

#### Prerequisites

- Python 3.13+
- Git
- uv (Python package installer) - `pip install uv`
- LLM provider (OpenAI, Ollama, etc.)

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd complex_team/job_pipeline
   ```

2. Create and activate a virtual environment using uv:
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies with uv:
   ```bash
   # Install main dependencies
   uv pip install -e .
   
   # Install dev dependencies (for testing)
   uv pip install -e ".[dev]"
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   ```
   Edit the `.env` file with your specific configuration:
   - LLM model and API settings
   - Agent port configurations
   - Git integration settings

## Usage

### Starting the Pipeline

1. Start the LLM backend (if using Ollama):
   ```bash
   ollama serve
   ```

2. Launch the agents in separate terminals:
   ```bash
   # Terminal 1: Planning Agent
   python -m agents.planning.server
   
   # Terminal 2: Orchestrator Agent
   python -m agents.orchestrator.server
   
   # Terminal 3: Specification Agent
   python -m agents.specification.server
   
   # Terminal 4: Design Agent
   python -m agents.design.server
   
   # Terminal 5: Code Agent
   python -m agents.code.server
   
   # Terminal 6: Review Agent
   python -m agents.review.server
   
   # Terminal 7: Test Agent
   python -m agents.testing.server
   
   # Terminal 8: MCP Git Tools
   python -m mcp.git_tools
   
   # Terminal 9: UI (optional)
   python -m ui.app
   ```

3. Access the system:
   - Use the provided client to interact with the planning agent
   - Or access the UI at http://localhost:8501 (if enabled)


## Testing

### Running Tests

The project includes comprehensive tests for all components:

```bash
# Run all tests
pytest

# Run tests for a specific component
pytest tests/test_planning_agent.py

# Run tests with coverage report
pytest --cov=agents tests/
```

### Test Structure

- **Unit Tests**: Test individual agent functionality
- **Integration Tests**: Test communication between agents
- **End-to-End Tests**: Test complete workflows

## Testing Individual Servers with curl

For debugging or API exploration, you can test each agent server individually using curl. Below are examples for each server:

### Planning Agent (Port 8001)

```bash
curl -X POST http://localhost:8001/api/v1/run \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "planner",
    "input": [
      {
        "parts": [
          {
            "content": "Create a web application for a small e-commerce shop"
          }
        ]
      }
    ]
  }'
```

### Orchestrator Agent (Port 8002)

```bash
curl -X POST http://localhost:8002/api/v1/run \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "orchestrator",
    "input": [
      {
        "parts": [
          {
            "content": "{\"title\": \"E-commerce Application\", \"description\": \"Web application for a small e-commerce shop\", \"features\": [{\"name\": \"User Authentication\", \"priority\": \"high\"}]}"
          }
        ]
      }
    ]
  }'
```

### Specification Agent (Port 8005)

```bash
curl -X POST http://localhost:8005/api/v1/run \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "specification",
    "input": [
      {
        "parts": [
          {
            "content": "Create detailed specifications for a User Authentication feature"
          }
        ]
      }
    ]
  }'
```

### Design Agent (Port 8003)

```bash
curl -X POST http://localhost:8003/api/v1/run \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "design",
    "input": [
      {
        "parts": [
          {
            "content": "Design the architecture for a User Authentication system with login, signup, and password reset"
          }
        ]
      }
    ]
  }'
```

### Code Agent (Port 8004)

```bash
curl -X POST http://localhost:8004/api/v1/run \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "code",
    "input": [
      {
        "parts": [
          {
            "content": "Implement a User class with authentication methods based on Flask-Login"
          }
        ]
      }
    ]
  }'
```

### Review Agent (Port 8006)

```bash
curl -X POST http://localhost:8006/api/v1/run \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "review",
    "input": [
      {
        "parts": [
          {
            "content": "class User:\n    def __init__(self, username, email):\n        self.username = username\n        self.email = email\n        self.is_active = False\n\n    def verify_password(self, password):\n        # Dummy implementation\n        return True"
          }
        ]
      }
    ]
  }'
```

### Testing Agent (Port 8007)

```bash
curl -X POST http://localhost:8007/api/v1/run \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "testing",
    "input": [
      {
        "parts": [
          {
            "content": "Create unit tests for a User class with authentication methods"
          }
        ]
      }
    ]
  }'
```

### Notes on Using curl with ACP SDK Servers

- The format follows the ACP protocol structure with inputs as an array of message objects
- For streaming responses, add `"stream": true` to the JSON payload
- For session-based interactions, include a session ID using the `"session_id": "your-session-id"` field
- To view the full response, pipe the output to `jq`: `curl ... | jq`

## Project Structure

```
complex_team/job_pipeline/
├── agents/                     # Agent implementations
│   ├── planning/               # Planning agent
│   ├── orchestrator/           # Orchestrator agent
│   ├── specification/          # Specification agent
│   ├── design/                 # Design agent
│   ├── code/                   # Code agent
│   ├── review/                 # Review agent
│   └── testing/                # Test agent
├── config/                     # Configuration
│   ├── config.py               # Centralized LLM and agent configuration
│   └── prompt_schemas.py       # Pydantic schemas for prompt templates
├── state/                      # State management
│   └── state_manager.py        # Pipeline state tracking
├── tests/                      # Tests
├── pyproject.toml              # Project configuration and dependencies
├── .env.example                # Example environment variables
└── README.md                   # This file
```

## Configuration

All LLM configurations, including prompts and model parameters, are centralized in the `config/config.py` file with schemas defined in `prompt_schemas.py`. This follows the project rule of centralizing all LLM configurations.

### Prompt Template Pattern

The project uses BeeAI Framework's prompt template pattern:

1. Prompt text defined in `config.py` as simple strings/dictionaries
2. Schemas defined in `prompt_schemas.py` as Pydantic models
3. Conversion to BeeAI `PromptTemplate` instances performed in agent code

This pattern maintains separation of concerns while ensuring type safety and validation.

## Contributing

1. Create a feature branch
2. Make your changes
3. Write or update tests
4. Submit a pull request

## License

[License information]
