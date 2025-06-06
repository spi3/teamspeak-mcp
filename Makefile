# Makefile for TeamSpeak MCP
.PHONY: help build run test stop clean logs shell docker-build docker-test docker-run docker-clean release-patch release-minor release-major setup-pypi

# Variables
IMAGE_NAME = teamspeak-mcp
CONTAINER_NAME = teamspeak-mcp
GHCR_IMAGE = ghcr.io/marlburrow/teamspeak-mcp
VERSION = $(shell grep '^version =' pyproject.toml | sed 's/version = "\(.*\)"/\1/')

# === HELP ===
help: ## Show this help
	@echo "🚀 TeamSpeak MCP - Available commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "🎯 Quick workflows:"
	@echo "  make release-patch    # $(VERSION) -> next patch (bug fixes)"
	@echo "  make release-minor    # $(VERSION) -> next minor (new features)"
	@echo "  make release-major    # $(VERSION) -> next major (breaking changes)"

# === DEVELOPMENT ===
install-dev: ## Install in editable mode for development
	pip install -e .

test-local: ## Run tests locally
	python test_mcp.py

lint: ## Run code linting
	@echo "🔍 Running linters..."
	@command -v black >/dev/null 2>&1 && black --check . || echo "⚠️  black not found, skipping"

format: ## Format code
	@echo "🎨 Formatting code..."
	@command -v black >/dev/null 2>&1 && black . || echo "⚠️  black not found, skipping"

# === DOCKER BUILD ===
build: ## Build Docker image
	docker build -t $(IMAGE_NAME):$(VERSION) -t $(IMAGE_NAME):latest .

build-no-cache: ## Build Docker image without cache
	docker build --no-cache -t $(IMAGE_NAME):$(VERSION) -t $(IMAGE_NAME):latest .

# === DOCKER RUN ===
run: ## Start MCP server with Docker Compose
	docker-compose up -d

run-ghcr: ## Start MCP server with pre-built GHCR image
	docker-compose -f docker-compose.ghcr.yml up -d

run-logs: ## Start MCP server with real-time logs
	docker-compose up

stop: ## Stop MCP server
	docker-compose down

restart: ## Restart MCP server
	docker-compose restart

# === DOCKER TESTING ===
test: ## Run tests in Docker container
	docker-compose --profile test run --rm teamspeak-mcp-test

test-docker: ## Test with local Docker image
	docker run --rm --env-file .env.test $(IMAGE_NAME):$(VERSION) test

test-ghcr: ## Test with GHCR image
	docker run --rm --env-file .env.test $(GHCR_IMAGE):latest test

# === DOCKER UTILITIES ===
shell: ## Open shell in container
	docker run --rm -it --env-file .env $(IMAGE_NAME):latest shell

shell-ghcr: ## Open shell in GHCR container
	docker run --rm -it --env-file .env $(GHCR_IMAGE):latest shell

debug: ## Start container in debug mode
	docker run --rm -it --env-file .env $(IMAGE_NAME):latest debug

# === REGISTRY OPERATIONS ===
pull: ## Pull latest image from GHCR
	docker pull $(GHCR_IMAGE):latest

pull-version: ## Pull specific version from GHCR
	docker pull $(GHCR_IMAGE):$(VERSION)

# === LOGS AND MONITORING ===
logs: ## Show container logs
	docker-compose logs -f

logs-tail: ## Show last logs
	docker-compose logs --tail=50

status: ## Show container status
	docker-compose ps
	@echo ""
	@echo "📊 Project Status:"
	@echo "  Version: $(VERSION)"
	@echo "  Docker image: $(IMAGE_NAME):$(VERSION)"
	@echo "  GHCR image: $(GHCR_IMAGE):$(VERSION)"
	@echo ""
	@echo "🔗 Links:"
	@echo "  - PyPI: https://pypi.org/project/teamspeak-mcp/"
	@echo "  - GitHub: https://github.com/MarlBurroW/teamspeak-mcp"
	@echo "  - Docker: $(GHCR_IMAGE)"

# === RELEASES (Automated via GitHub Actions) ===
release-patch: ## Release patch version (bug fixes)
	@echo "🚀 Creating patch release..."
	python3 scripts/release.py patch

release-minor: ## Release minor version (new features)
	@echo "🚀 Creating minor release..."
	python3 scripts/release.py minor

release-major: ## Release major version (breaking changes)
	@echo "🚀 Creating major release..."
	python3 scripts/release.py major

# === PYPI SETUP ===
setup-pypi: ## Setup PyPI tokens (run once)
	@echo "🔧 Setting up PyPI tokens..."
	@echo ""
	@echo "1. Go to: https://github.com/MarlBurroW/teamspeak-mcp/settings/secrets/actions"
	@echo "2. Add these secrets:"
	@echo "   - PYPI_API_TOKEN (from https://pypi.org/manage/account/token/)"
	@echo "   - TEST_PYPI_API_TOKEN (from https://test.pypi.org/manage/account/token/)"
	@echo ""
	@echo "3. Then run: make release-patch"

# === MANUAL PYPI (Fallback) ===
build-package: ## Build Python package
	rm -rf dist/ build/ *.egg-info/
	python3 -m build
	twine check dist/*

upload-test: ## Upload to TestPyPI
	twine upload --repository testpypi dist/*

upload-pypi: ## Upload to PyPI
	twine upload dist/*

# === SETUP ===
setup: ## Complete initial setup
	@echo "🚀 Setting up TeamSpeak MCP..."
	@if [ ! -f .env ]; then \
		echo "📝 Creating .env file..."; \
		cp config.docker.env .env; \
		echo "⚠️  Modify .env file with your TeamSpeak parameters"; \
	fi
	$(MAKE) build
	@echo "✅ Setup complete!"
	@echo "💡 Modify .env then run: make run"

setup-ghcr: ## Setup with pre-built GHCR image
	@echo "🚀 Setting up TeamSpeak MCP with GHCR image..."
	@if [ ! -f .env ]; then \
		echo "📝 Creating .env file..."; \
		cp config.docker.env .env; \
		echo "⚠️  Modify .env file with your TeamSpeak parameters"; \
	fi
	$(MAKE) pull
	@echo "✅ Setup complete with GHCR image!"
	@echo "💡 Modify .env then run: make run-ghcr"

# === CLEANUP ===
clean: ## Clean containers and images
	docker-compose down --rmi all --volumes --remove-orphans

clean-all: ## Clean everything
	docker system prune -f
	docker rmi $(IMAGE_NAME):latest $(IMAGE_NAME):$(VERSION) 2>/dev/null || true
	rm -rf build/ dist/ *.egg-info/ __pycache__/ .pytest_cache/
	find . -name "*.pyc" -delete

# === LEGACY ALIASES ===
up: run ## Alias for 'run'
down: stop ## Alias for 'stop'
version: status ## Alias for 'status'

# Default help
.DEFAULT_GOAL := help 