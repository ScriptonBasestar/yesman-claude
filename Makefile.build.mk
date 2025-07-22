# Makefile.build.mk - Build and Installation targets for yesman-claude
# Build, installation, and deployment management

# ==============================================================================
# Build Configuration
# ==============================================================================

# Colors are now exported from main Makefile

# ==============================================================================
# Build & Installation Targets
# ==============================================================================

.PHONY: build install install-dev install-test install-all dev-install
.PHONY: clean clean-all clean-build clean-pyc clean-test setup-all

install: ## install yesman-claude in development mode
	@echo "$(CYAN)Installing $(PROJECT_NAME)...$(RESET)"
	uv pip install -e .
	@echo "$(GREEN)✅ $(PROJECT_NAME) installed successfully$(RESET)"

install-dev: ## install with dev dependencies
	@echo "$(CYAN)Installing with dev dependencies...$(RESET)"
	uv pip install -e . --group dev
	@echo "$(GREEN)✅ Dev dependencies installed$(RESET)"

install-test: ## install with test dependencies
	@echo "$(CYAN)Installing with test dependencies...$(RESET)"
	uv pip install -e . --group test
	@echo "$(GREEN)✅ Test dependencies installed$(RESET)"

install-all: ## install with all dependencies (dev + test)
	@echo "$(CYAN)Installing with all dependencies...$(RESET)"
	uv pip install -e . --group dev --group test
	@echo "$(GREEN)✅ All dependencies installed$(RESET)"

dev-install: ## install with pip editable mode
	@echo "$(CYAN)Installing with pip editable mode...$(RESET)"
	pip install -e . --config-settings editable_mode=compat
	@echo "$(GREEN)✅ Installed in editable mode$(RESET)"

build: ## build Python package
	@echo "$(CYAN)Building $(PROJECT_NAME) package...$(RESET)"
	python -m build
	@echo "$(GREEN)✅ Package built successfully$(RESET)"

# ==============================================================================
# Dashboard Build Targets
# ==============================================================================

.PHONY: build-dashboard build-dashboard-dev install-dashboard-deps
.PHONY: run-web-dashboard run-web-dashboard-detached run-tauri-dashboard
.PHONY: run-tauri-dev build-tauri clean-dashboard build-all

build-dashboard: ## build SvelteKit dashboard
	@echo "$(CYAN)Building SvelteKit dashboard...$(RESET)"
	@if [ -d "tauri-dashboard" ]; then \
		cd tauri-dashboard && npm run build; \
		echo "$(GREEN)✅ Dashboard built successfully$(RESET)"; \
	else \
		echo "$(YELLOW)⚠️  Dashboard directory not found$(RESET)"; \
	fi

build-dashboard-dev: ## build dashboard in development mode
	@echo "$(CYAN)Building dashboard in development mode...$(RESET)"
	@if [ -d "tauri-dashboard" ]; then \
		cd tauri-dashboard && npm run dev; \
	else \
		echo "$(YELLOW)⚠️  Dashboard directory not found$(RESET)"; \
	fi

install-dashboard-deps: ## install dashboard dependencies
	@echo "$(CYAN)Installing dashboard dependencies...$(RESET)"
	@if [ -d "tauri-dashboard" ]; then \
		cd tauri-dashboard && npm install; \
		echo "$(GREEN)✅ Dashboard dependencies installed$(RESET)"; \
	else \
		echo "$(YELLOW)⚠️  Dashboard directory not found$(RESET)"; \
	fi

run-web-dashboard: build-dashboard ## build and run web dashboard
	@echo "$(CYAN)Starting web dashboard...$(RESET)"
	uv run ./yesman.py dash run -i web -p 8080

run-web-dashboard-detached: build-dashboard ## run web dashboard in background
	@echo "$(CYAN)Starting web dashboard in background...$(RESET)"
	uv run ./yesman.py dash run -i web -p 8080 --detach
	@echo "$(GREEN)✅ Web dashboard running on http://localhost:8080$(RESET)"

run-tauri-dashboard: build-dashboard ## build and run Tauri app
	@echo "$(CYAN)Starting Tauri app...$(RESET)"
	uv run ./yesman.py dash run -i tauri

run-tauri-dev: ## run Tauri in development mode
	@echo "$(CYAN)Starting Tauri in development mode...$(RESET)"
	@if [ -d "tauri-dashboard" ]; then \
		cd tauri-dashboard && npm run tauri dev; \
	else \
		echo "$(YELLOW)⚠️  Dashboard directory not found$(RESET)"; \
	fi

build-tauri: ## build Tauri for production
	@echo "$(CYAN)Building Tauri for production...$(RESET)"
	@if [ -d "tauri-dashboard" ]; then \
		cd tauri-dashboard && npm run tauri build; \
		echo "$(GREEN)✅ Tauri app built successfully$(RESET)"; \
	else \
		echo "$(YELLOW)⚠️  Dashboard directory not found$(RESET)"; \
	fi

build-all: build-dashboard install ## build complete project
	@echo "$(GREEN)✅ Complete project built successfully$(RESET)"

# ==============================================================================
# Clean Targets
# ==============================================================================

clean: clean-build clean-pyc clean-test ## clean all build artifacts

clean-all: clean clean-dashboard ## clean everything including dashboard

clean-build: ## clean Python build artifacts
	@echo "$(CYAN)Cleaning build artifacts...$(RESET)"
	@rm -rf build/ dist/ *.egg-info/
	@echo "$(GREEN)✅ Build artifacts cleaned$(RESET)"

clean-pyc: ## clean Python cache files
	@echo "$(CYAN)Cleaning Python cache files...$(RESET)"
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@find . -type f -name "*~" -delete
	@echo "$(GREEN)✅ Python cache cleaned$(RESET)"

clean-test: ## clean test artifacts
	@echo "$(CYAN)Cleaning test artifacts...$(RESET)"
	@rm -rf .pytest_cache/
	@rm -rf htmlcov/
	@rm -f .coverage
	@rm -f coverage.xml
	@echo "$(GREEN)✅ Test artifacts cleaned$(RESET)"

clean-dashboard: ## clean dashboard build artifacts
	@echo "$(CYAN)Cleaning dashboard artifacts...$(RESET)"
	@if [ -d "tauri-dashboard" ]; then \
		cd tauri-dashboard && rm -rf build/ .svelte-kit/ node_modules/.vite/; \
		cd tauri-dashboard && rm -rf src-tauri/target/; \
		echo "$(GREEN)✅ Dashboard artifacts cleaned$(RESET)"; \
	else \
		echo "$(YELLOW)⚠️  Dashboard directory not found$(RESET)"; \
	fi

# ==============================================================================
# Setup Targets
# ==============================================================================

setup-all: install-all install-dashboard-deps hooks-install ## complete project setup
	@echo "$(GREEN)🎉 Complete project setup finished!$(RESET)"
	@echo "$(YELLOW)Next steps:$(RESET)"
	@echo "  1. Run $(CYAN)make quick$(RESET) to verify setup"
	@echo "  2. Run $(CYAN)make help$(RESET) to see available commands"

# ==============================================================================
# Build Information
# ==============================================================================

.PHONY: build-info

build-info: ## show build information and targets
	@echo "$(CYAN)"
	@echo "╔══════════════════════════════════════════════════════════════════════════════╗"
	@echo "║                         $(YELLOW)Build Information$(CYAN)                              ║"
	@echo "╚══════════════════════════════════════════════════════════════════════════════╝"
	@echo "$(RESET)"
	@echo "$(GREEN)📋 Build Details:$(RESET)"
	@echo "  Project:        $(YELLOW)$(PROJECT_NAME)$(RESET)"
	@echo "  Version:        $(YELLOW)$(VERSION)$(RESET)"
	@echo "  Python:         $$(python --version 2>&1)"
	@echo "  UV:            $$(uv --version 2>&1 || echo 'Not installed')"
	@echo ""
	@echo "$(GREEN)🎯 Build Targets:$(RESET)"
	@echo "  • $(CYAN)build$(RESET)               Build Python package"
	@echo "  • $(CYAN)install$(RESET)             Install in development mode"
	@echo "  • $(CYAN)install-all$(RESET)         Install with all dependencies"
	@echo "  • $(CYAN)build-dashboard$(RESET)     Build SvelteKit dashboard"
	@echo "  • $(CYAN)build-tauri$(RESET)         Build Tauri desktop app"
	@echo "  • $(CYAN)build-all$(RESET)           Build complete project"
	@echo "  • $(CYAN)clean$(RESET)               Clean build artifacts"
	@echo "  • $(CYAN)setup-all$(RESET)           Complete project setup"