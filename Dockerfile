# Multi-stage Dockerfile for Multi-Agent Coding System

# Base stage with common dependencies
FROM python:3.11-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    # Docker CLI for executor agent
    ca-certificates \
    gnupg \
    lsb-release \
    && rm -rf /var/lib/apt/lists/*

# Install Docker CLI
RUN curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null \
    && apt-get update \
    && apt-get install -y docker-ce-cli \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Create necessary directories
RUN mkdir -p logs generated tests/outputs

# Set Python path
ENV PYTHONPATH=/app

# Orchestrator service
FROM base as orchestrator
EXPOSE 8080
CMD ["python", "orchestrator/orchestrator_agent.py"]

# API service
FROM base as api
EXPOSE 8000
CMD ["python", "api/orchestrator_api.py"]

# Frontend service
FROM python:3.11-slim as frontend
WORKDIR /app
COPY frontend/ ./frontend/
EXPOSE 3000
CMD ["python", "frontend/serve.py"]

# Default to orchestrator if no target specified
FROM orchestrator