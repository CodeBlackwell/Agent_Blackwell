# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a modular multi-agent system that orchestrates specialized AI agents to collaborate on software development tasks. The system implements the Agent Communication Protocol (ACP) architecture with a team of specialized agents (Planner, Designer, Coder, Test Writer, Reviewer, and Executor) working together through configurable workflows.

## Core Architecture

The system follows a **modular, single-server architecture** with these key components:

1. **Orchestrator Agent** (`orchestrator/orchestrator_agent.py`): Central coordinator managing workflows via `EnhancedCodingTeamTool`
2. **Workflow Manager** (`workflows/workflow_manager.py`): Dispatches requests to appropriate workflow modules
3. **Specialized Agents** (in `agents/` directory): Each agent handles specific development tasks
4. **Shared Data Models** (`shared/data_models.py`): Common data structures for agent communication
5. **REST API** (`api/orchestrator_api.py`): External interface for submitting workflow requests

## Execution Reporting Memories

- The execution report should track every single exchange between all of the agents, every single command that was run, all test reports, all things that could be useful for debugging each individual run.
- Additionally, those reports should be saved in both JSON and CSV format, and they should be hard saved to the generated code file for retroactive debugging.

[Rest of the file remains unchanged...]