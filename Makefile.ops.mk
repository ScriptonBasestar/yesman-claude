# Makefile.ops.mk - Operations and Maintenance for yesman-claude
# Cleanup, information, Docker operations, and system maintenance

# ==============================================================================
# Operations Configuration
# ==============================================================================

# Colors are now exported from main Makefile

# Docker settings
DOCKER_IMAGE_NAME ?= yesman-claude
DOCKER_TAG ?= $(VERSION)
DOCKER_REGISTRY ?= ghcr.io/yourusername
DOCKER_FULL_IMAGE = $(DOCKER_REGISTRY)/$(DOCKER_IMAGE_NAME):$(DOCKER_TAG)
DOCKER_LATEST = $(DOCKER_REGISTRY)/$(DOCKER_IMAGE_NAME):latest

# Docker build args
DOCKER_BUILD_ARGS ?= \
	--build-arg PYTHON_VERSION=3.11 \
	--build-arg PROJECT_NAME=$(PROJECT_NAME)

# ==============================================================================
# Cleanup Operations
# ==============================================================================

.PHONY: clean clean-all clean-build clean-pyc clean-test clean-dashboard
.PHONY: clean-tools clean-docker clean-deep

clean: clean-build clean-pyc clean-test ## clean all build artifacts

clean-all: clean clean-dashboard clean-tools ## clean everything including dashboard

clean-build: ## clean Python build artifacts
	@echo -e "$(CYAN)Cleaning build artifacts...$(RESET)"
	@rm -rf build/ dist/ *.egg-info/
	@echo -e "$(GREEN)✅ Build artifacts cleaned$(RESET)"

clean-pyc: ## clean Python cache files
	@echo -e "$(CYAN)Cleaning Python cache files...$(RESET)"
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@find . -type f -name "*~" -delete
	@echo -e "$(GREEN)✅ Python cache cleaned$(RESET)"

clean-test: ## clean test artifacts
	@echo -e "$(CYAN)Cleaning test artifacts...$(RESET)"
	@rm -rf .pytest_cache/
	@rm -rf htmlcov/
	@rm -f .coverage
	@rm -f coverage.xml
	@echo -e "$(GREEN)✅ Test artifacts cleaned$(RESET)"

clean-dashboard: ## clean dashboard build artifacts
	@echo -e "$(CYAN)Cleaning dashboard artifacts...$(RESET)"
	@if [ -d "tauri-dashboard" ]; then \
		cd tauri-dashboard && rm -rf build/ .svelte-kit/ node_modules/.vite/; \
		cd tauri-dashboard && rm -rf src-tauri/target/; \
		echo -e "$(GREEN)✅ Dashboard artifacts cleaned$(RESET)"; \
	else \
		echo -e "$(YELLOW)⚠️  Dashboard directory not found$(RESET)"; \
	fi

clean-tools: ## remove tool caches and temporary files
	@echo -e "$(CYAN)Cleaning tool caches...$(RESET)"
	@rm -rf .mypy_cache/
	@rm -rf .pytest_cache/
	@rm -rf .ruff_cache/
	@rm -rf .coverage
	@rm -f .coverage.*
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo -e "$(GREEN)✅ Tool caches cleaned$(RESET)"

clean-docker: ## clean up Docker containers and images
	@echo -e "$(CYAN)Cleaning up Docker resources...$(RESET)"
	@docker stop $(shell docker ps -q --filter name=$(DOCKER_IMAGE_NAME)) 2>/dev/null || true
	@docker rm $(shell docker ps -aq --filter name=$(DOCKER_IMAGE_NAME)) 2>/dev/null || true
	@docker rmi $(DOCKER_IMAGE_NAME):$(DOCKER_TAG) 2>/dev/null || true
	@docker rmi $(DOCKER_IMAGE_NAME):latest 2>/dev/null || true
	@echo -e "$(GREEN)✅ Docker cleanup completed$(RESET)"

clean-deep: clean-all clean-docker ## deep clean everything including Docker
	@echo -e "$(CYAN)Performing deep cleanup...$(RESET)"
	@docker system prune -f 2>/dev/null || true
	@echo -e "$(GREEN)✅ Deep cleanup completed$(RESET)"

# ==============================================================================
# Docker Operations
# ==============================================================================

.PHONY: docker-build docker-run docker-stop docker-push docker-scan
.PHONY: docker-shell docker-logs docker-status

docker-build: ## build Docker image for local development
	@echo -e "$(CYAN)Building Docker image: $(DOCKER_IMAGE_NAME):$(DOCKER_TAG)$(RESET)"
	docker build -t $(DOCKER_IMAGE_NAME):$(DOCKER_TAG) \
		-t $(DOCKER_IMAGE_NAME):latest \
		$(DOCKER_BUILD_ARGS) \
		-f Dockerfile \
		.
	@echo -e "$(GREEN)✅ Docker image built successfully$(RESET)"

docker-run: ## run Docker container
	@echo -e "$(CYAN)Running Docker container...$(RESET)"
	docker run --rm \
		--name $(DOCKER_IMAGE_NAME) \
		-p 8000:8000 \
		-v $(PWD):/app \
		$(DOCKER_IMAGE_NAME):$(DOCKER_TAG)

docker-stop: ## stop running Docker containers
	@echo -e "$(CYAN)Stopping Docker containers...$(RESET)"
	@docker stop $(DOCKER_IMAGE_NAME) 2>/dev/null || true
	@docker stop $(DOCKER_IMAGE_NAME)-interactive 2>/dev/null || true
	@docker stop $(DOCKER_IMAGE_NAME)-detached 2>/dev/null || true
	@echo -e "$(GREEN)✅ Containers stopped$(RESET)"

docker-push: ## push Docker image to registry
	@echo -e "$(CYAN)Pushing Docker image to registry...$(RESET)"
	docker tag $(DOCKER_IMAGE_NAME):$(DOCKER_TAG) $(DOCKER_FULL_IMAGE)
	docker tag $(DOCKER_IMAGE_NAME):$(DOCKER_TAG) $(DOCKER_LATEST)
	docker push $(DOCKER_FULL_IMAGE)
	docker push $(DOCKER_LATEST)
	@echo -e "$(GREEN)✅ Docker image pushed$(RESET)"

docker-scan: ## scan Docker image for vulnerabilities
	@echo -e "$(CYAN)Scanning Docker image for vulnerabilities...$(RESET)"
	@if command -v trivy >/dev/null 2>&1; then \
		trivy image $(DOCKER_IMAGE_NAME):$(DOCKER_TAG); \
	else \
		docker scan $(DOCKER_IMAGE_NAME):$(DOCKER_TAG) 2>/dev/null || \
		echo -e "$(YELLOW)Install trivy or enable docker scan for vulnerability scanning$(RESET)"; \
	fi

docker-shell: ## open shell in running container
	@echo -e "$(CYAN)Opening shell in container...$(RESET)"
	@container=$$(docker ps -q --filter name=$(DOCKER_IMAGE_NAME) | head -1); \
	if [ -n "$$container" ]; then \
		docker exec -it $$container /bin/bash; \
	else \
		echo -e "$(YELLOW)No running container found$(RESET)"; \
	fi

docker-logs: ## show container logs
	@echo -e "$(CYAN)Showing container logs...$(RESET)"
	@container=$$(docker ps -q --filter name=$(DOCKER_IMAGE_NAME) | head -1); \
	if [ -n "$$container" ]; then \
		docker logs -f $$container; \
	else \
		echo -e "$(YELLOW)No running container found$(RESET)"; \
	fi

docker-status: ## show Docker container status
	@echo -e "$(CYAN)Docker Status$(RESET)"
	@echo -e "$(BLUE)==============$(RESET)"
	@echo ""
	@echo -e "$(YELLOW)Running Containers:$(RESET)"
	@docker ps --filter name=$(DOCKER_IMAGE_NAME) --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" || echo "  None"
	@echo ""
	@echo -e "$(YELLOW)Images:$(RESET)"
	@docker images --filter reference=$(DOCKER_IMAGE_NAME) --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}\t{{.Created}}" || echo "  None"

# ==============================================================================
# Information and Status
# ==============================================================================

.PHONY: ops-info ops-version status system-info project-status

ops-info: ## show project information and current configuration
	@echo -e "$(CYAN)"
	@echo -e "╔══════════════════════════════════════════════════════════════════════════════╗"
	@echo -e "║                         $(MAGENTA)yesman-claude Project Information$(CYAN)                   ║"
	@echo -e "╚══════════════════════════════════════════════════════════════════════════════╝"
	@echo -e "$(RESET)"
	@echo -e "$(GREEN)📋 Project Details:$(RESET)"
	@echo -e "  Name:           $(YELLOW)$(PROJECT_NAME)$(RESET)"
	@echo -e "  Executable:     $(YELLOW)$(EXECUTABLE_NAME)$(RESET)"
	@echo -e "  Version:        $(YELLOW)$(VERSION)$(RESET)"
	@echo ""
	@echo -e "$(GREEN)🏗️  Python Environment:$(RESET)"
	@echo "  Python:         $$(python --version 2>&1)"
	@echo "  UV:            $$(uv --version 2>&1 || echo 'Not installed')"
	@echo "  pip:           $$(pip --version | cut -d' ' -f2)"
	@echo ""
	@echo -e "$(GREEN)📁 Key Features:$(RESET)"
	@echo "  • Automated Claude CLI interaction"
	@echo "  • Project template management"
	@echo "  • tmux session automation"
	@echo "  • Web and Tauri dashboard interfaces"
	@echo "  • Rich CLI interface with Textual"

ops-version: ## show version
	@echo -e "$(PROJECT_NAME) version: $(VERSION)"

status: ## check system and project status
	@echo -e "$(CYAN)System Status$(RESET)"
	@echo -e "$(BLUE)==============$(RESET)"
	@echo ""
	@echo -e "$(GREEN)🖥️  System:$(RESET)"
	@echo "  OS:            $$(uname -s)"
	@echo "  Architecture:  $$(uname -m)"
	@echo "  Hostname:      $$(hostname)"
	@echo ""
	@echo -e "$(GREEN)🐍 Python:$(RESET)"
	@echo "  Version:       $$(python --version 2>&1)"
	@echo "  Location:      $$(which python)"
	@echo ""
	@echo -e "$(GREEN)📦 Dependencies:$(RESET)"
	@echo -e "  Packages:      $(pip list | tail -n +3 | wc -l) installed"
	@echo ""
	@echo -e "$(GREEN)🚀 Services:$(RESET)"
	@if pgrep -f "yesman.py" >/dev/null; then \
		echo -e "  Yesman:        $(GREEN)✅ Running$(RESET)"; \
	else \
		echo -e "  Yesman:        $(YELLOW)⚠️  Not running$(RESET)"; \
	fi

system-info: ## show detailed system information
	@echo -e "$(CYAN)Detailed System Information$(RESET)"
	@echo -e "$(BLUE)============================$(RESET)"
	@echo ""
	@echo -e "$(GREEN)🖥️  System Details:$(RESET)"
	@echo "  OS:            $$(uname -a)"
	@echo "  Uptime:        $$(uptime | cut -d',' -f1 | cut -d' ' -f4-)"
	@echo "  Load:          $$(uptime | awk -F'load average:' '{print $$2}')"
	@echo ""
	@echo -e "$(GREEN)💾 Memory:$(RESET)"
	@free -h | grep -E "Mem|Swap" | awk '{printf "  %-8s %s used of %s total\\n", $$1, $$3, $$2}'
	@echo ""
	@echo -e "$(GREEN)💽 Disk:$(RESET)"
	@df -h . | tail -1 | awk '{printf "  Usage:       %s used of %s (%s)\\n", $$3, $$2, $$5}'

project-status: ## show project-specific status
	@echo -e "$(CYAN)Project Status$(RESET)"
	@echo -e "$(BLUE)===============$(RESET)"
	@echo ""
	@echo -e "$(GREEN)📁 Project Structure:$(RESET)"
	@echo -e "  Root:          $(PWD)"
	@if [ -d "libs" ]; then echo -e "  Libraries:     $(GREEN)✅ Present$(RESET)"; else echo -e "  Libraries:     $(YELLOW)⚠️  Missing$(RESET)"; fi
	@if [ -d "commands" ]; then echo -e "  Commands:      $(GREEN)✅ Present$(RESET)"; else echo -e "  Commands:      $(YELLOW)⚠️  Missing$(RESET)"; fi
	@if [ -d "tests" ]; then echo -e "  Tests:         $(GREEN)✅ Present$(RESET)"; else echo -e "  Tests:         $(YELLOW)⚠️  Missing$(RESET)"; fi
	@if [ -d "tauri-dashboard" ]; then echo -e "  Dashboard:     $(GREEN)✅ Present$(RESET)"; else echo -e "  Dashboard:     $(YELLOW)⚠️  Missing$(RESET)"; fi
	@echo ""
	@echo -e "$(GREEN)📄 Configuration:$(RESET)"
	@if [ -f "pyproject.toml" ]; then echo -e "  pyproject.toml: $(GREEN)✅ Present$(RESET)"; else echo -e "  pyproject.toml: $(RED)❌ Missing$(RESET)"; fi
	@if [ -f "Makefile" ]; then echo -e "  Makefile:      $(GREEN)✅ Present$(RESET)"; else echo -e "  Makefile:      $(RED)❌ Missing$(RESET)"; fi

# ==============================================================================
# Maintenance Operations
# ==============================================================================

.PHONY: maintenance backup restore check-health

maintenance: ## run routine maintenance tasks
	@echo -e "$(CYAN)Running routine maintenance...$(RESET)"
	@echo -e "$(YELLOW)1. Cleaning temporary files...$(RESET)"
	@$(MAKE) clean-tools
	@echo -e "$(YELLOW)2. Checking for outdated dependencies...$(RESET)"
	@$(MAKE) deps-outdated
	@echo -e "$(YELLOW)3. Running security check...$(RESET)"
	@$(MAKE) deps-security
	@echo -e "$(GREEN)✅ Maintenance completed$(RESET)"

backup: ## create backup of important files
	@echo -e "$(CYAN)Creating backup...$(RESET)"
	@backup_dir=".backups/backup_$(shell date +%Y%m%d_%H%M%S)"; \
	mkdir -p $$backup_dir; \
	cp -r libs commands tests pyproject.toml Makefile*.mk $$backup_dir/ 2>/dev/null || true; \
		echo -e "$(GREEN)✅ Backup created in $$backup_dir$(RESET)"

restore: ## restore from latest backup (interactive)
	@echo -e "$(CYAN)Available backups:$(RESET)"
	@ls -la .backups/ 2>/dev/null || echo "No backups found"
	@echo -e "$(YELLOW)Use: cp -r .backups/<backup_name>/* . to restore$(RESET)"

check-health: ## perform health check
	@echo -e "$(CYAN)Performing health check...$(RESET)"
	@echo -e "$(YELLOW)Checking Python installation...$(RESET)"
	@python --version >/dev/null 2>&1 && echo -e "$(GREEN)✅ Python OK$(RESET)" || echo -e "$(RED)❌ Python issue$(RESET)"
	@echo -e "$(YELLOW)Checking dependencies...$(RESET)"
	@pip check >/dev/null 2>&1 && echo -e "$(GREEN)✅ Dependencies OK$(RESET)" || echo -e "$(RED)❌ Dependency conflicts$(RESET)"
	@echo -e "$(YELLOW)Checking project structure...$(RESET)"
	@if [ -f "pyproject.toml" ] && [ -d "libs" ] && [ -d "commands" ]; then \
		echo -e "$(GREEN)✅ Project structure OK$(RESET)"; \
	else \
		echo -e "$(RED)❌ Project structure issues$(RESET)"; \
	fi
	@echo -e "$(GREEN)✅ Health check completed$(RESET)"

# ==============================================================================
# Documentation Generation
# ==============================================================================

.PHONY: generate-api-docs generate-docs docs-clean docs-serve

generate-api-docs: ## generate API documentation from FastAPI
	@echo -e "$(CYAN)Generating API documentation...$(RESET)"
	@if [ -f "scripts/generate-docs.py" ]; then \
		uv run python scripts/generate-docs.py --api; \
		echo -e "$(GREEN)✅ API documentation generated$(RESET)"; \
	else \
		echo -e "$(YELLOW)⚠️  Documentation generator not found$(RESET)"; \
		echo -e "$(YELLOW)   Creating basic OpenAPI export...$(RESET)"; \
		uv run python -c "from api.main import app; import json; print(json.dumps(app.openapi(), indent=2))" > api-docs/openapi.json 2>/dev/null || \
		echo -e "$(RED)❌ Failed to generate API docs$(RESET)"; \
	fi

generate-docs: generate-api-docs ## generate all documentation
	@echo -e "$(CYAN)Generating project documentation...$(RESET)"
	@if [ -f "scripts/generate-docs.py" ]; then \
		uv run python scripts/generate-docs.py --all; \
	else \
		echo -e "$(YELLOW)⚠️  Full documentation generator not implemented yet$(RESET)"; \
	fi

docs-clean: ## clean generated documentation
	@echo -e "$(CYAN)Cleaning generated documentation...$(RESET)"
	@rm -rf api-docs/generated/
	@rm -f api-docs/openapi.json
	@echo -e "$(GREEN)✅ Generated documentation cleaned$(RESET)"

docs-serve: ## serve documentation locally
	@echo -e "$(CYAN)Starting documentation server...$(RESET)"
	@if command -v python -m http.server >/dev/null 2>&1; then \
		echo -e "$(GREEN)Documentation available at http://localhost:8001$(RESET)"; \
		cd docs && python -m http.server 8001; \
	else \
		echo -e "$(RED)❌ Python http.server not available$(RESET)"; \
	fi

# ==============================================================================
# Operations Information
# ==============================================================================

.PHONY: ops-tools-info

ops-tools-info: ## show operations information
	@echo -e "$(CYAN)"
	@echo "╔══════════════════════════════════════════════════════════════════════════════╗"
	@echo -e "║                         $(YELLOW)Operations Information$(CYAN)                           ║"
	@echo "╚══════════════════════════════════════════════════════════════════════════════╝"
	@echo -e "$(RESET)"
	@echo -e "$(GREEN)🧹 Cleanup Commands:$(RESET)"
	@echo -e "  • $(CYAN)clean$(RESET)               Clean build artifacts"
	@echo -e "  • $(CYAN)clean-all$(RESET)           Clean everything"
	@echo -e "  • $(CYAN)clean-deep$(RESET)          Deep clean including Docker"
	@echo ""
	@echo -e "$(GREEN)🐳 Docker Commands:$(RESET)"
	@echo -e "  • $(CYAN)docker-build$(RESET)        Build Docker image"
	@echo -e "  • $(CYAN)docker-run$(RESET)          Run container"
	@echo -e "  • $(CYAN)docker-status$(RESET)       Show container status"
	@echo -e "  • $(CYAN)docker-scan$(RESET)         Security scan"
	@echo ""
	@echo -e "$(GREEN)📚 Documentation Commands:$(RESET)"
	@echo -e "  • $(CYAN)generate-api-docs$(RESET)   Generate API documentation"
	@echo -e "  • $(CYAN)generate-docs$(RESET)       Generate all documentation"
	@echo -e "  • $(CYAN)docs-clean$(RESET)          Clean generated docs"
	@echo -e "  • $(CYAN)docs-serve$(RESET)          Serve docs locally"
	@echo ""
	@echo -e "$(GREEN)ℹ️  Information Commands:$(RESET)"
	@echo -e "  • $(CYAN)info$(RESET)                Project information"
	@echo -e "  • $(CYAN)status$(RESET)              System status"
	@echo -e "  • $(CYAN)project-status$(RESET)      Project-specific status"
	@echo -e "  • $(CYAN)system-info$(RESET)         Detailed system info"
	@echo ""
	@echo -e "$(GREEN)🔧 Maintenance Commands:$(RESET)"
	@echo -e "  • $(CYAN)maintenance$(RESET)         Routine maintenance"
	@echo -e "  • $(CYAN)backup$(RESET)              Create backup"
	@echo -e "  • $(CYAN)check-health$(RESET)        Health check"