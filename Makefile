# Makefile for TeamSpeak MCP
.PHONY: help build run test stop clean logs shell

# Variables
IMAGE_NAME = teamspeak-mcp
CONTAINER_NAME = teamspeak-mcp
VERSION = 1.0.0

# Help
help: ## Show this help
	@echo "TeamSpeak MCP - Available commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Build
build: ## Build Docker image
	docker build -t $(IMAGE_NAME):$(VERSION) -t $(IMAGE_NAME):latest .

build-no-cache: ## Build Docker image without cache
	docker build --no-cache -t $(IMAGE_NAME):$(VERSION) -t $(IMAGE_NAME):latest .

# Execution
run: ## Start MCP server with Docker Compose
	docker-compose up -d

run-logs: ## Start MCP server with real-time logs
	docker-compose up

stop: ## Stop MCP server
	docker-compose down

restart: ## Restart MCP server
	docker-compose restart

# Tests
test: ## Run tests in container
	docker-compose --profile test run --rm teamspeak-mcp-test

test-local: ## Run tests with local image
	docker run --rm -it --env-file .env $(IMAGE_NAME):latest python test_mcp.py

# Development
shell: ## Open shell in container
	docker run --rm -it --env-file .env --entrypoint /bin/bash $(IMAGE_NAME):latest

debug: ## Start container in debug mode
	docker run --rm -it --env-file .env --entrypoint /bin/bash $(IMAGE_NAME):latest

# Logs and monitoring
logs: ## Show container logs
	docker-compose logs -f

logs-tail: ## Show last logs
	docker-compose logs --tail=50

status: ## Show container status
	docker-compose ps

# Cleanup
clean: ## Clean containers and images
	docker-compose down --rmi all --volumes --remove-orphans

clean-all: ## Clean everything (warning: removes all local Docker images for this project)
	docker system prune -f
	docker rmi $(IMAGE_NAME):latest $(IMAGE_NAME):$(VERSION) 2>/dev/null || true

# Installation and configuration
install: ## Install dependencies locally
	pip install -r requirements.txt

setup: ## Complete initial setup
	@echo "Setting up TeamSpeak MCP..."
	@if [ ! -f .env ]; then \
		echo "Creating .env file..."; \
		cp config.docker.env .env; \
		echo "⚠️  Modify .env file with your TeamSpeak parameters"; \
	fi
	$(MAKE) build
	@echo "✅ Setup complete!"
	@echo "💡 Modify .env then run: make run"

# Docker Compose shortcuts
up: run ## Alias for 'run'
down: stop ## Alias for 'stop'

# Info
info: ## Show image information
	docker image inspect $(IMAGE_NAME):latest --format='{{.Config.Labels}}'

version: ## Show version
	@echo "TeamSpeak MCP version: $(VERSION)"

# Default help
.DEFAULT_GOAL := help 