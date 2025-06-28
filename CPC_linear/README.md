# ACP Code Writing Application

A proof-of-concept application demonstrating how to build multi-agent systems using the Agent Communication Protocol (ACP). This application combines two specialized agents - a planner and a coder - to generate code from natural language descriptions.

## Overview

This application demonstrates a simple yet powerful agent collaboration pattern using ACP:

1. A **Planner Agent** takes a user's code request and generates a structured development plan
2. A **Coder Agent** receives the plan and generates functional code to implement it
3. A **Client** coordinates the communication between these agents and presents the results

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│             │     │             │     │             │
│  Client     │────►│  Planner    │────►│  Coder      │
│  (CLI)      │◄────│  Agent      │◄────│  Agent      │
│             │     │             │     │             │
└─────────────┘     └─────────────┘     └─────────────┘
```

### Components

- **Planner Agent**: Analyzes natural language requests and creates structured plans
- **Coder Agent**: Generates code based on development plans
- **Client**: Coordinates the communication flow between agents

## Installation

```bash
# Create and activate a virtual environment
uv venv
source .venv/bin/activate

# Install dependencies
uv pip install acp-sdk openai python-dotenv
```

## Configuration

Create a `.env` file in the project root with the following content:

```
OPENAI_API_KEY="your-openai-api-key-here"
```

## Usage

1. Start the planner agent:
   ```bash
   python planner.py
   ```

2. Start the coder agent:
   ```bash
   python coder.py
   ```

3. Run the client with your code request:
   ```bash
   python client.py "Write a function to calculate fibonacci sequence"
   ```

## Key Lessons Learned

### 1. ACP Architecture Fundamentals

- **Agent as Service**: Each agent runs as an independent service accessible via HTTP
- **Message-Based Communication**: Agents communicate using structured messages
- **Asynchronous Processing**: Agents can yield incremental results during processing
- **Stateless by Default**: Agents are stateless unless explicitly using sessions

### 2. Agent Design Patterns

- **Single Responsibility Principle**: Each agent focuses on a specific task
- **Sequential Chain of Work**: Agents can form a pipeline where output from one feeds the next
- **Separation of Concerns**: Planning and implementation are handled by separate specialized agents

### 3. Implementation Best Practices

- **Virtual Environment**: Always use isolated environments for dependencies
- **Environment Variables**: Securely manage API keys using dotenv
- **Fallback Mechanisms**: Handle potential failures gracefully with fallback logic
- **Streaming Output**: Use ACP's async generator pattern for responsive interactions

### 4. ACP Integration with LLMs

- **Prompt Engineering**: Carefully designed prompts yield better agent results
- **Context Management**: Keep agent contexts focused for optimal performance
- **Error Handling**: Gracefully handle API limitations and failures

## Extending This Application

This proof-of-concept can be extended in several ways:

1. Add more specialized agents (testing, documentation, etc.)
2. Implement the awaiting pattern for interactive refinement
3. Add session management for stateful interactions
4. Create a web interface instead of CLI
5. Integrate with version control systems

## Project Structure

```
acp_code_poc/
├── .env                # Environment variables (API keys)
├── planner.py         # Planner agent implementation
├── coder.py           # Coder agent implementation
├── client.py          # Client script to coordinate agents
└── README.md          # This documentation
```
