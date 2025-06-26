# 🤖 Agent Blackwell

<div align="center">

![Version](https://img.shields.io/badge/version-0.1.0-blue.svg?cacheSeconds=2592000)
![Python](https://img.shields.io/badge/Python-3.11-brightgreen.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-latest-teal.svg)
![LangChain](https://img.shields.io/badge/LangChain-latest-orange.svg)


**A modular LLM-powered agent orchestration system featuring autonomous agents working together via Redis streams and Pinecone vector DB**

</div>

## 🌟 Overview

Agent Blackwell is a cutting-edge orchestration system that harnesses the power of multiple specialized AI agents working in concert to transform requirements into working software. By decomposing complex tasks into specialized workflows, Agent Blackwell delivers higher-quality results than single-LLM approaches, with enhanced reliability, transparency, and control.

### 🚀 Business Value

- **Massive Productivity Boost** - Automates routine coding tasks, allowing developers to focus on high-level architecture and business-critical features
- **24/7 Development Cycle** - Agents work around the clock, accelerating project timelines dramatically
- **Knowledge Augmentation** - Captures and applies best practices, ensuring consistent quality across projects
- **Scalable Expertise** - Supplements team knowledge with specialized agents trained in security, testing, and optimization
- **Reduced Technical Debt** - Built-in code review and testing agents ensure high-quality output from the start

## 🧠 How It Works: The Symphony of Agents

Imagine an orchestra where each musician is a specialized AI agent. When a feature request arrives, it kicks off a carefully choreographed performance:

1. **The Conductor (Orchestrator)** receives your feature request and coordinates the entire process through Redis streams—like musical notes flowing between performers.

2. **The Composer (Spec Agent)** transforms your high-level ideas into a detailed specification—akin to turning a musical theme into a complete score with parts for each instrument.

3. **The Architect (Design Agent)** visualizes the system structure with Mermaid diagrams and API contracts—sketching the blueprint before construction begins.

4. **The Builder (Coding Agent)** crafts the actual code modules—like a master craftsman turning architectural plans into tangible structures.

5. **The Inspector (Review Agent)** meticulously examines the code for quality and security issues—acting as a diligent quality control officer finding subtle flaws before they cause problems.

6. **The Scientist (Test Agent)** develops comprehensive test suites—experimenting with the code under various conditions to ensure it performs reliably.

Each agent specializes in what it does best, and together they create high-quality software faster than traditional approaches. The magic happens through:

- **Redis Streams**: A flowing river of tasks and results that agents tap into
- **Pinecone Vector DB**: The collective memory that helps agents learn from past work
- **Agent Registry**: The talent manager ensuring the right agent handles the right job through module-level agent wrappers

## 🏗️ Architecture

```mermaid
graph TD
    A[User Request] -->|API| B[Orchestrator]
    B -->|Task Queue| C[Redis Streams]
    C -->|Tasks| D[Agent Registry]
    D -->|Dispatch| E[Specialized Agents]
    E -->|Results| C
    E -->|Vector Storage| F[Pinecone DB]

    subgraph "Agents"
    G[Spec Agent]
    H[Design Agent]
    I[Coding Agent]
    J[Review Agent]
    K[Test Agent]
    end

    E -->|Delegates to| G
    E -->|Delegates to| H
    E -->|Delegates to| I
    E -->|Delegates to| J
    E -->|Delegates to| K
```

## 💻 Tech Stack

- **Core Runtime**: Python 3.11+
- **Framework**: FastAPI
- **Agent Technology**: LangChain with GPT-4
- **Message Broker**: Redis Streams
- **Vector Database**: Pinecone
- **Containerization**: Docker with Docker Compose
- **Orchestration**: Kubernetes with Helm Charts
- **Monitoring**: Prometheus & Grafana
- **ChatOps**: Slack API Integration
- **Dependency Management**: Poetry

## 🧠 Specialized Agents: The Dream Team

### 🔍 Spec Agent: The Requirements Whisperer
Transforms vague user requests like "I need user authentication" into detailed specifications with user stories, acceptance criteria, and a breakdown of subtasks. It's like having a business analyst who never misses important details.

### 📐 Design Agent: The System Architect
Creates beautiful architecture diagrams and API contracts that visualize how components will fit together. It considers scalability, security, and best practices—laying the groundwork for rock-solid implementations.

### 👨‍💻 Coding Agent: The Master Craftsman
Generates clean, production-ready code that follows your team's coding standards. Whether it's a complex algorithm or boilerplate CRUD operations, this agent writes code that humans will actually enjoy maintaining.

### 🔬 Review Agent: The Quality Guardian
Scans code with a magnifying glass, finding subtle bugs, security vulnerabilities, and performance bottlenecks before they reach production. It's like having a senior developer review every line of code 24/7.

### 🧪 Test Agent: The Confidence Builder
Creates comprehensive test suites that verify functionality, catch edge cases, and maintain high coverage metrics. It ensures your application remains stable as it evolves—protecting against regressions and unexpected behavior.

## 🛠️ Getting Started

### Prerequisites

- Python 3.11+
- Redis server (standalone or Docker)
- OpenAI API key
- Pinecone API key
- Slack API key
- Docker and Docker Compose (for containerized deployment)
- Kubernetes and Helm (for orchestrated deployment)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/Agent_Blackwell.git
cd Agent_Blackwell

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
poetry install

# Set up environment variables
export OPENAI_API_KEY="your-openai-key"
export PINECONE_API_KEY="your-pinecone-key"
export SLACK_API_KEY="your-slack-key"
```

### Running the System

#### Local Development

```bash
# Start Redis server (if not already running)
redis-server

# Start the orchestrator
python -m src.orchestrator.main
```

#### Using Docker Compose

```bash
# Build and start all services
docker-compose up --build

# Run in detached mode
docker-compose up -d

# View logs
docker-compose logs -f
```

#### Kubernetes Deployment with Helm

```bash
# Add required Helm repositories
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts

# Update dependencies
cd infra/helm/agent-blackwell
helm dependency update

# Install the chart
helm install agent-blackwell ./infra/helm/agent-blackwell \
  --values ./infra/helm/agent-blackwell/values.yaml \
  --namespace agent-blackwell \
  --create-namespace

# Check deployment status
kubectl get pods -n agent-blackwell
```

## 📝 Real-World Example

Imagine you need to add a user authentication system. Here's how Agent Blackwell transforms that request into working code:

```python
from src.orchestrator.main import Orchestrator

# Initialize the orchestrator
orchestrator = Orchestrator(
    openai_api_key="your-openai-key",
    pinecone_api_key="your-pinecone-key",
    slack_api_key="your-slack-key"
)

# Start the orchestrator
await orchestrator.start()

# Submit a feature request
task = {
    "task_id": "auth-feature-123",
    "task_type": "spec",
    "payload": {
        "description": "Create a user authentication module with JWT support, password reset functionality, and social login options"
    }
}

# The magic begins here!
result = await orchestrator.process_task(task)
```

### What Happens Behind the Scenes:

1. The **Spec Agent** breaks this down into detailed tasks:
   - User registration endpoint
   - JWT token generation and validation
   - Password reset flow with email verification
   - OAuth integration for social logins

2. The **Design Agent** creates:
   - An authentication flow diagram
   - API endpoint specifications
   - Database schema for user accounts

3. The **Coding Agent** generates:
   - User model classes
   - API route handlers
   - JWT middleware for authentication
   - Password hashing utilities

4. The **Review Agent** verifies:
   - Security best practices
   - Input validation
   - Error handling completeness
   - Code style and documentation

5. The **Test Agent** creates:
   - Unit tests for each component
   - Integration tests for the authentication flow
   - Performance tests for token validation
   - Mocked dependencies for isolated testing

## 🔄 The Agent Workflow

1. **Task Reception**: A task enters the system via API or Slack command
2. **Task Queuing**: The task is placed in a Redis stream for processing
3. **Agent Assignment**: The Orchestrator matches the task to the appropriate agent
4. **Task Processing**: The agent performs its specialized work on the task
5. **Result Streaming**: Results flow back through Redis to the Orchestrator
6. **Knowledge Storage**: Insights and artifacts are stored in Pinecone for future reference
7. **Task Chaining**: Results can trigger new tasks for other agents (e.g., code → review)
8. **Status Updates**: Progress is visible through API endpoints or Slack notifications

## 🧪 Testing

Run the test suite with pytest:

```bash
pytest
```

## 📁 File Structure

```
Agent_Blackwell/
├── infra/                # Infrastructure configuration
│   ├── docker/           # Dockerfiles and Docker Compose
│   └── helm/             # Kubernetes Helm charts
│       └── agent-blackwell/
│           ├── templates/  # Kubernetes manifests
│           ├── Chart.yaml  # Chart definition
│           ├── values.yaml # Default configuration
│           └── test-values.yaml # Values for local testing
├── src/                  # Source code
│   ├── agents/           # Agent implementations
│   │   ├── coding_agent.py   # Generates code based on task description and design
│   │   ├── design_agent.py   # Creates design specifications and architecture diagrams
│   │   ├── review_agent.py   # Analyzes code quality, security, and linting issues
│   │   ├── spec_agent.py     # Generates task lists from high-level descriptions
│   │   └── test_agent.py     # Creates unit tests and integration tests for code
│   ├── api/              # API endpoints
│   │   └── v1/           # API version 1
│   │       ├── chatops/  # Slack integration
│   │       ├── feature_request.py
│   │       └── task_status.py
│   ├── orchestrator/     # Task orchestration
│   │   ├── agent_registry.py  # Agent registration & wrappers
│   │   └── main.py      # Orchestrator core
│   └── prompts/         # Agent prompts
├── tests/               # Test suites
│   ├── api/             # API tests
│   └── ...              # Agent-specific tests
├── blog_notes.md        # Development journal
├── docker-compose.yml   # Multi-service deployment
├── pyproject.toml      # Project dependencies (Poetry)
└── README.md           # Project documentation
```

### Key Components

- **Agent Wrappers**: Located in `src/orchestrator/agent_registry.py`, these module-level classes provide a consistent interface (`ainvoke` method) for different agent types to interact with the orchestrator.
- **Helm Charts**: Located in `infra/helm/agent-blackwell/`, these templates enable deployment to Kubernetes with integrated Redis, Prometheus, and Grafana services.
- **ChatOps Integration**: Located in `src/api/v1/chatops/`, this code enables Slack commands and message processing for interacting with agents.
- **Docker Compose**: Provides local multi-service development with app, Redis, Prometheus, and Grafana services.
- **Messages Endpoint**: Located at `/api/v1/messages`, this endpoint provides access to inter-agent communication messages stored in Redis Streams for observability and debugging.

## 🗺️ Roadmap

The following features are planned for upcoming releases:

### Near-term (Q3 2025)

- **Per-Agent Model Configuration**: A flexible configuration system to customize LLM models and parameters for each agent through a central YAML file, enabling:
  - Different models for different agents (e.g., GPT-4o for Review, Claude for Coding)
  - Custom temperature and token settings per agent type
  - Environment variable overrides for flexible deployment
  - Support for multiple LLM providers

### Future Features

- **Multi-modal Agent Support**: Enabling agents to process and generate images and diagrams
- **Fine-tuning Pipeline**: Automated evaluation and fine-tuning of agent models
- **Agent Memory Persistence**: Long-term knowledge retention across sessions
- **Advanced Monitoring Dashboard**: Real-time insights into agent performance and resource usage

## 📚 Comprehensive User Guide

This section provides detailed instructions on using Agent Blackwell, from initial setup to advanced features and troubleshooting.

### 🚀 Quick Start

#### 1. Environment Setup

Create a `.env` file in the project root with your API keys:

```bash
# Required API keys
OPENAI_API_KEY=your-openai-key
PINECONE_API_KEY=your-pinecone-key

# Optional integrations
SLACK_API_TOKEN=your-slack-token
SLACK_SIGNING_SECRET=your-slack-signing-secret

# Infrastructure configuration
REDIS_URL=redis://localhost:6379/0
PORT=8000
```

#### 2. Start Required Services

Using Docker Compose (recommended for new users):

```bash
# Start all services (API, Redis, Prometheus, Grafana)
docker-compose up -d

# View logs
docker-compose logs -f app
```

Or start services individually:

```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start the API server
python -m src.api.main
```

#### 3. Submit Your First Feature Request

```bash
curl -X POST "http://localhost:8000/api/v1/feature-request" \
  -H "Content-Type: application/json" \
  -d '{"description": "Create a simple function that calculates the Fibonacci sequence up to n terms"}'
```

You'll receive a response with a `workflow_id` that you can use to check status:

```bash
curl -X GET "http://localhost:8000/api/v1/workflow-status/your-workflow-id"
```

### 🔄 End-to-End Workflow

Here's what happens when you submit a feature request:

1. **Initialization**: The system assigns a unique workflow_id
2. **Spec Generation**: The Spec Agent creates detailed requirements
3. **Design Phase**: The Design Agent creates architecture diagrams
4. **Implementation**: The Coding Agent writes code to fulfill specs
5. **Quality Assurance**: The Review Agent analyzes code quality
6. **Testing**: The Test Agent creates comprehensive tests
7. **Delivery**: Final code and documentation are delivered

You can monitor progress at any time using the workflow status endpoint.

### 🧪 Test Run Procedures

#### Running the E2E Test Gauntlet

The `e2e_test_gauntlet.py` script provides comprehensive validation of all API endpoints and flexible execution modes:

```bash
# Ensure the API is running first, then:
cd scripts
python e2e_test_gauntlet.py --url http://localhost:8000

# Run with options:
python e2e_test_gauntlet.py --url http://localhost:8000 --max-tests 3 --output-dir logs
```

The script tests:
- Health check endpoint
- Feature request creation
- Workflow status checking
- Synchronous workflow execution
- Streaming workflow execution
- Legacy endpoint compatibility

Results are saved to `e2e_test_results.json` for analysis.

#### Running Unit Tests

```bash
# Run all tests
pytest

# Run specific test modules
pytest tests/agents/test_spec_agent.py

# Run with coverage report
python -m pytest --cov=src tests/
```

### 📋 API Reference

| Endpoint | Method | Purpose |
|----------|--------|--------|
| `/` | GET | Health check |
| `/health` | GET | Detailed health with service status |
| `/api/v1/feature-request` | POST | Submit new feature request |
| `/api/v1/workflow-status/{id}` | GET | Check workflow status |
| `/api/v1/execute-workflow` | POST | Execute workflow synchronously |
| `/api/v1/stream-workflow/{id}` | GET | Stream workflow execution |
| `/api/v1/task-status/{id}` | GET | Legacy status endpoint |
| `/api/v1/messages` | GET | Access inter-agent communications |

### 🔍 Monitoring and Observability

Agent Blackwell provides comprehensive monitoring capabilities:

#### 1. Agent Message Stream

Monitor inter-agent communications in real-time:

```bash
curl -X GET "http://localhost:8000/api/v1/messages?number_of_messages=10"
```

Filter by task:

```bash
curl -X GET "http://localhost:8000/api/v1/messages?task_id=your-workflow-id"
```

#### 2. Prometheus Metrics

Access API performance metrics at:

```
http://localhost:8000/metrics
```

#### 3. Grafana Dashboards

When using Docker Compose, access pre-configured dashboards at:

```
http://localhost:3000
```

Default credentials: admin/admin

### 🔧 Specific Feature Guides

#### Custom Agent Configuration (Coming Soon)

> **Note**: This feature is planned for future implementation and is not yet available.

In an upcoming release, agent configuration will be customizable through environment variables:

```bash
# Example: Configure the Spec Agent to use GPT-4o (FUTURE FEATURE)
SPEC_AGENT_MODEL=gpt-4o
SPEC_AGENT_TEMPERATURE=0.7

# Example: Configure the Coding Agent to use Claude (FUTURE FEATURE)
CODING_AGENT_PROVIDER=anthropic
CODING_AGENT_MODEL=claude-3-opus-20240229
CODING_AGENT_TEMPERATURE=0.2
```

This will be part of the planned "Per-Agent Model Configuration" feature mentioned in the roadmap.

#### Slack Integration

To enable Slack integration:

1. Create a Slack app at https://api.slack.com/apps
2. Enable Socket Mode and Event Subscriptions
3. Subscribe to the `app_mention` event
4. Install the app to your workspace
5. Set environment variables:

```bash
SLACK_API_TOKEN=xoxb-your-token
SLACK_SIGNING_SECRET=your-signing-secret
SLACK_APP_TOKEN=xapp-your-app-token
```

Once configured, mention the bot in Slack:

```
@Agent-Blackwell Create a function to parse CSV files
```

The bot will respond with a workflow ID and status updates.

#### Advanced Redis Configuration

Fine-tune Redis for production:

```bash
# Persistence configuration
REDIS_PERSISTENCE_MODE=rdb
REDIS_RDB_FILENAME=dump.rdb
REDIS_SAVE_FREQUENCY=60

# Performance tuning
REDIS_MAX_MEMORY=2gb
REDIS_MAX_MEMORY_POLICY=allkeys-lru

# Security (if exposed)
REDIS_PASSWORD=your-strong-password
REDIS_TLS_ENABLED=true
```

#### Vector Database Management

Manage Pinecone indexes:

```bash
# List indexes
python -m src.utils.pinecone_tools list-indexes

# Create a new index
python -m src.utils.pinecone_tools create-index \
  --name agent-blackwell \
  --dimension 1536 \
  --metric cosine

# Delete an index
python -m src.utils.pinecone_tools delete-index --name agent-blackwell
```

### 🔮 Troubleshooting

#### Common Issues

1. **Redis Connection Errors**
   - Verify Redis is running: `redis-cli ping`
   - Check connection URL in .env file
   - Ensure Redis port (6379) is not blocked by firewall

2. **API Key Errors**
   - Verify API keys are correctly set in .env
   - Check for trailing spaces in API keys
   - Ensure you have proper subscription level for required features

3. **Agent Timeout Issues**
   - Increase timeout settings in `src/config/settings.py`
   - Check API provider status for outages
   - Consider using a different model or reducing complexity

4. **Docker Networking Problems**
   - Restart Docker: `docker-compose down && docker-compose up -d`
   - Check for port conflicts: `netstat -tulpn | grep 8000`
   - Verify Docker network setup: `docker network ls`

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the issues page.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

<div align="center">
Built with ❤️ and AI
</div>
