# Makefile for Multi-Agent Coding System

.PHONY: help build up down logs clean test shell api-test frontend setup

help: ## Show this help message
	@echo "Multi-Agent Coding System - Docker Commands"
	@echo ""
	@echo "Usage: make [command]"
	@echo ""
	@echo "Commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

setup: ## Initial setup: copy env file and build
	@if [ ! -f .env ]; then cp docker.env.example .env && echo "Created .env file - please add your API keys"; fi
	@docker-compose build

build: ## Build all Docker images
	docker-compose build

up: ## Start all services
	docker-compose up

up-d: ## Start all services in detached mode
	docker-compose up -d

down: ## Stop all services
	docker-compose down

clean: ## Stop services and remove volumes
	docker-compose down -v

logs: ## View logs for all services
	docker-compose logs -f

logs-orchestrator: ## View orchestrator logs
	docker-compose logs -f orchestrator

logs-api: ## View API logs
	docker-compose logs -f api

test: ## Run all tests
	docker-compose exec orchestrator ./test_runner.py

test-unit: ## Run unit tests
	docker-compose exec orchestrator ./test_runner.py unit

test-integration: ## Run integration tests
	docker-compose exec orchestrator ./test_runner.py integration

shell: ## Open shell in orchestrator container
	docker-compose exec orchestrator /bin/bash

api-test: ## Test API with curl
	@echo "Testing API endpoint..."
	@curl -X POST http://localhost:8000/execute-workflow \
	  -H "Content-Type: application/json" \
	  -d '{"requirements": "Create a hello world function", "workflow_type": "full"}' | jq

frontend: ## Open frontend in browser
	@echo "Opening frontend..."
	@open http://localhost:3000 2>/dev/null || xdg-open http://localhost:3000 2>/dev/null || echo "Please open http://localhost:3000 in your browser"

hello: ## Run hello world example
	docker-compose exec orchestrator python hello_agents.py

demo: ## Run interactive demo
	docker-compose exec orchestrator python quickstart.py

health: ## Check service health
	@echo "Checking service health..."
	@curl -s http://localhost:8080/health | jq '.' 2>/dev/null || echo "Orchestrator: Not responding"
	@curl -s http://localhost:8000/health | jq '.' 2>/dev/null || echo "API: Not responding"
	@curl -s http://localhost:3000 >/dev/null 2>&1 && echo "Frontend: Healthy" || echo "Frontend: Not responding"

rebuild: ## Force rebuild without cache
	docker-compose build --no-cache

restart: ## Restart all services
	docker-compose restart

ps: ## Show running containers
	docker-compose ps