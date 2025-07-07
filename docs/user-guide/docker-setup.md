# 🐳 Docker Quick Start Guide

Get the Multi-Agent Coding System running in 3 minutes with Docker!

## Prerequisites
- Docker Desktop installed and running
- Git installed
- OpenAI API key

## Quick Start

1. **Clone and setup**
   ```bash
   git clone <repository-url>
   cd rebuild
   cp docker.env.example .env
   ```

2. **Add your OpenAI API key to .env**
   ```bash
   # Edit .env file and add your key:
   OPENAI_API_KEY=your-actual-api-key-here
   ```

3. **Start everything**
   ```bash
   docker-compose up
   ```

4. **Open the web interface**
   ```bash
   open http://localhost:3000
   ```

## Test It Works

### Via Web Interface
1. Go to http://localhost:3000
2. Select "TDD Workflow"
3. Enter: "Create a simple calculator"
4. Click Send and watch the agents work!

### Via Command Line
```bash
# Quick test
docker compose exec orchestrator python run.py example hello_world

# API test
curl -X POST http://localhost:8000/execute-workflow \
  -H "Content-Type: application/json" \
  -d '{"requirements": "Create a hello world function", "workflow_type": "full"}'
```

## What's Running?

- **Orchestrator** (port 8080): Core agent coordinator
- **API** (port 8000): REST API for external access
- **Frontend** (port 3000): Web interface

## Common Issues

**"Connection refused"**
- Wait 30 seconds for services to start
- Check logs: `docker-compose logs`

**"Invalid API key"**
- Ensure your OpenAI API key is set in .env
- Restart: `docker-compose restart`

## Stop Everything
```bash
docker-compose down
```

## Next Steps
See [Demo Guide](demo-guide.md) for comprehensive examples and features!

---

[← Back to User Guide](../user-guide/) | [← Back to Docs](../)