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
│   │   ├── coding_agent.py
│   │   ├── design_agent.py
│   │   ├── review_agent.py
│   │   ├── spec_agent.py
│   │   └── test_agent.py
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

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the issues page.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

<div align="center">
Built with ❤️ and AI
</div>
