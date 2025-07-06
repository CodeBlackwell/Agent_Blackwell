# AI Development Team Frontend

A bare minimum MVP frontend interface for the multi-agent orchestrator system.

## Features

- **Chat Interface**: Natural language input to describe what you want to build
- **Workflow Selection**: Choose between Full, TDD, or Individual step workflows
- **Real-time Monitoring**: View agent activity and outputs as they process your request
- **Status Updates**: Track workflow progress with visual indicators

## Quick Start

1. Start the orchestrator server:
   ```bash
   python orchestrator/orchestrator_agent.py
   ```

2. Start the API server:
   ```bash
   python api/orchestrator_api.py
   ```

3. Open the frontend:
   - Simply open `frontend/index.html` in your web browser
   - Or serve it with any static file server

## Usage

1. Select a workflow type:
   - **Full Workflow**: Planning → Design → Implementation → Review
   - **TDD Workflow**: Planning → Design → Test Writing → Implementation → Execution → Review
   - **Individual Step**: Execute a single step (requires selecting which step)

2. Type your requirements in the chat input

3. Click Send or press Enter

4. Monitor agent activity in the right panel

## Technical Details

- Pure HTML/CSS/JavaScript (no frameworks required)
- Uses Fetch API for REST communication
- Polling mechanism for real-time updates (2-second intervals)
- Responsive design for different screen sizes