# Makefile.dev.mk - Development Workflow for yesman-claude
# Development environment, workflow automation, and quick iteration

# ==============================================================================
# Development Configuration
# ==============================================================================

# Colors are now exported from main Makefile

# ==============================================================================
# Quick Access Aliases for Development
# ==============================================================================

.PHONY: start stop restart status logs run run-detached

# Application control
start: run ## quick start: run yesman
stop: ## stop running yesman processes
	@echo -e "$(YELLOW)Stopping yesman processes...$(RESET)"
	@pkill -f "yesman" || echo -e "$(GREEN)No running yesman processes found$(RESET)"

restart: stop start ## restart yesman

yesman-status: ## check yesman status
	@echo -e "$(CYAN)Checking for running yesman processes...$(RESET)"
	@pgrep -f "yesman" > /dev/null && echo -e "$(GREEN)✅ yesman is running$(RESET)" || echo -e "$(RED)❌ yesman is not running$(RESET)"

logs: ## show recent log files
	@echo -e "$(CYAN)Recent log files:$(RESET)"
	@find . -name "*.log" -type f -mtime -7 -exec ls -la {} \; 2>/dev/null || echo -e "$(YELLOW)No recent log files found$(RESET)"

run: ## run yesman.py
	@echo -e "$(CYAN)Running yesman...$(RESET)"
	uv run ./yesman.py
	#uv run python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 10501

run-dev: ## run yesman.py in development mode
	@echo -e "$(CYAN)Running yesman in development mode...$(RESET)"
	uv run ./yesman.py --dev

run-detached: ## run yesman in background
	@echo -e "$(CYAN)Running yesman in background...$(RESET)"
	nohup uv run ./yesman.py > yesman.log 2>&1 &
	@echo -e "$(GREEN)✅ yesman started in background (see yesman.log)$(RESET)"

# ==============================================================================
# Development Workflow Targets
# ==============================================================================

.PHONY: dev dev-fast quick full verify ci-local pr-check

dev: lint-check test ## standard development workflow (lint + test)
	@echo -e "$(GREEN)✅ Standard development workflow completed!$(RESET)"

dev-fast: lint-fast test-unit ## quick development cycle (fast lint + unit tests)
	@echo -e "$(GREEN)✅ Fast development cycle completed!$(RESET)"

quick: dev-fast ## quick check (alias for dev-fast)

full: lint test-coverage ## full quality check (comprehensive)
	@echo -e "$(GREEN)✅ Full quality check completed!$(RESET)"

verify: lint test cover-report ## complete verification
	@echo -e "$(GREEN)✅ Complete verification completed!$(RESET)"

ci-local: clean-all lint-strict test-all cover-check ## run full CI pipeline locally
	@echo -e "$(GREEN)✅ Local CI pipeline completed!$(RESET)"

pr-check: lint test cover-report ## pre-PR submission check
	@echo -e "$(GREEN)✅ Pre-PR check completed - ready for submission!$(RESET)"


# ==============================================================================
# Development Tools
# ==============================================================================

.PHONY: shell console format-imports type-check security-check profile commit-helper

shell: ## start Python shell with project context
	@echo -e "$(CYAN)Starting Python shell...$(RESET)"
	@uv run python

console: ## start IPython console with project loaded
	@echo -e "$(CYAN)Starting IPython console...$(RESET)"
	@command -v ipython >/dev/null 2>&1 || pip install ipython
	@uv run ipython

organize-imports: ## organize and format imports
	@echo -e "$(CYAN)Organizing imports...$(RESET)"
	@command -v isort >/dev/null 2>&1 || pip install isort
	@isort . --profile black
	@echo -e "$(GREEN)✅ Imports organized$(RESET)"

profile: ## profile the application
	@echo -e "$(CYAN)Starting profiler...$(RESET)"
	@echo -e "$(YELLOW)Run: python -m cProfile -o profile.stats yesman.py$(RESET)"
	@echo -e "$(YELLOW)Then: python -m pstats profile.stats$(RESET)"

commit-helper: ## run commit organization helper script
	@echo -e "$(CYAN)Running commit organization helper...$(RESET)"
	@if [ -f "scripts/commit_helper.sh" ]; then \
		chmod +x scripts/commit_helper.sh && ./scripts/commit_helper.sh; \
	else \
		echo -e "$(RED)❌ Commit helper script not found$(RESET)"; \
	fi


# ==============================================================================
# Development Information
# ==============================================================================

.PHONY: dev-info dev-status env-info

dev-info: ## show development environment information
	@echo -e "$(CYAN)"
	@echo "╔══════════════════════════════════════════════════════════════════════════════╗"
	@echo -e "║                         $(YELLOW)Development Information$(CYAN)                         ║"
	@echo "╚══════════════════════════════════════════════════════════════════════════════╝"
	@echo -e "$(RESET)"
	@echo -e "$(GREEN)🚀 Server Commands:$(RESET)"
	@echo -e "  • $(CYAN)start$(RESET)               Start yesman services"
	@echo -e "  • $(CYAN)stop$(RESET)                Stop all services"
	@echo -e "  • $(CYAN)restart$(RESET)             Restart services"
	@echo -e "  • $(CYAN)status$(RESET)              Check service status"
	@echo -e "  • $(CYAN)dev-dashboard$(RESET)       Full development environment"
	@echo ""
	@echo -e "$(GREEN)🛠️  Development Commands:$(RESET)"
	@echo -e "  • $(CYAN)dev$(RESET)                 Standard development workflow"
	@echo -e "  • $(CYAN)quick$(RESET)               Quick check (alias for dev-fast)"
	@echo -e "  • $(CYAN)full$(RESET)                Full quality check"
	@echo -e "  • $(CYAN)verify$(RESET)              Complete verification before PR"
	@echo ""
	@echo -e "$(GREEN)🐛 Debug Commands:$(RESET)"
	@echo -e "  • $(CYAN)debug-api$(RESET)           Debug API server"
	@echo -e "  • $(CYAN)debug-frontend$(RESET)      Debug frontend"
	@echo -e "  • $(CYAN)logs$(RESET)                Show service logs"
	@echo ""
	@echo -e "$(GREEN)📊 Current Status:$(RESET)"
	@echo -e "  Python:         $$(python --version 2>&1)"
	@echo -e "  Git branch:     $$(git branch --show-current 2>/dev/null || echo 'N/A')"
	@echo -e "  Git status:     $$(git status --porcelain 2>/dev/null | wc -l | xargs echo) files changed"
	@echo -e "  Last commit:    $$(git log -1 --format='%h %s' 2>/dev/null || echo 'N/A')"
	@echo ""
	@echo -e "$(GREEN)🌐 Server Ports:$(RESET)"
	@echo -e "  API Server:     $(YELLOW)$(API_SERVER_PORT)$(RESET)"
	@echo -e "  Dev Server:     $(YELLOW)$(DEV_SERVER_PORT)$(RESET)"

dev-status: ## show current development status
	@echo -e "$(CYAN)Development Status Check$(RESET)"
	@echo -e "$(BLUE)========================$(RESET)"
	@echo ""
	@echo -e "$(GREEN)📊 Project Status:$(RESET)"
	@echo -n -e "  Git Status:         "; if git status --porcelain | grep -q .; then echo -e "$(YELLOW)Modified files$(RESET)"; else echo -e "$(GREEN)Clean$(RESET)"; fi
	@echo -n -e "  Current Branch:     "; git branch --show-current 2>/dev/null || echo -e "$(RED)Unknown$(RESET)"
	@echo -n -e "  Last Commit:        "; git log -1 --format="%h %s" 2>/dev/null | cut -c1-50 || echo -e "$(RED)No commits$(RESET)"
	@echo ""
	@echo -e "$(GREEN)🔧 Development Status:$(RESET)"
	@echo -n -e "  Tests Passing:      "; if make test-unit > /dev/null 2>&1; then echo -e "$(GREEN)Yes$(RESET)"; else echo -e "$(RED)No$(RESET)"; fi
	@echo -n -e "  Coverage File:      "; if [ -f ".coverage" ]; then echo -e "$(GREEN)Yes$(RESET)"; else echo -e "$(YELLOW)No$(RESET)"; fi
	@echo -n -e "  Virtual Env:        "; if [ -n "$$VIRTUAL_ENV" ]; then echo -e "$(GREEN)Active$(RESET)"; else echo -e "$(YELLOW)None$(RESET)"; fi


# ==============================================================================
# Dashboard Development Servers
# ==============================================================================

.PHONY: dashboard dev-dashboard run-web-dashboard run-tauri-dev run-api-server debug-api stop-servers dashboard-status

# Default dashboard command - auto-detect best interface
dashboard: ## run yesman dashboard (auto-detect interface)
	@echo -e "$(CYAN)Starting Yesman Dashboard...$(RESET)"
	uv run ./yesman.py dashboard run

dev-dashboard: run-api-server run-web-dashboard ## full development environment (API + Web dashboard)
	@echo -e "$(GREEN)✅ Full development dashboard environment started!$(RESET)"

run-web-dashboard: ## run web dashboard only (Vite dev server)
	@echo -e "$(CYAN)Starting Web Dashboard (Vite dev server)...$(RESET)"
	@if [ -d "tauri-dashboard" ]; then \
		cd tauri-dashboard && npm run dev; \
	else \
		echo -e "$(RED)❌ tauri-dashboard directory not found$(RESET)"; \
		echo -e "$(YELLOW)Run 'make install-dashboard-deps' first$(RESET)"; \
	fi

run-tauri-dev: ## run Tauri desktop app in development mode  
	@echo -e "$(CYAN)Starting Tauri Development Mode...$(RESET)"
	@if [ -d "tauri-dashboard" ]; then \
		cd tauri-dashboard && npm run tauri dev; \
	else \
		echo -e "$(RED)❌ tauri-dashboard directory not found$(RESET)"; \
		echo -e "$(YELLOW)Run 'make install-dashboard-deps' first$(RESET)"; \
	fi

run-api-server: ## run API server in background
	@echo -e "$(CYAN)Starting API Server...$(RESET)"
	@if pgrep -f "uvicorn.*api.main:app" > /dev/null; then \
		echo -e "$(YELLOW)⚠️  API server already running$(RESET)"; \
	else \
		nohup uv run python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 10501 > api.log 2>&1 & \
		echo -e "$(GREEN)✅ API server started in background (see api.log)$(RESET)"; \
		echo -e "$(BLUE)🌐 API available at: http://localhost:10501$(RESET)"; \
	fi

debug-api: ## debug API server (foreground with detailed logs)
	@echo -e "$(CYAN)Starting API Server in Debug Mode...$(RESET)"
	@echo -e "$(YELLOW)Press Ctrl+C to stop$(RESET)"
	uv run python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 10501 --log-level debug

stop-servers: ## stop all dashboard-related servers
	@echo -e "$(YELLOW)Stopping dashboard servers...$(RESET)"
	@pkill -f "uvicorn.*api.main:app" || echo -e "$(BLUE)No API server running$(RESET)"
	@pkill -f "vite.*tauri-dashboard" || echo -e "$(BLUE)No Vite server running$(RESET)"
	@pkill -f "tauri dev" || echo -e "$(BLUE)No Tauri dev server running$(RESET)"
	@echo -e "$(GREEN)✅ All servers stopped$(RESET)"

dashboard-status: ## check dashboard server status
	@echo -e "$(CYAN)Dashboard Server Status:$(RESET)"
	@echo ""
	@echo -n -e "  API Server:         "; \
	if pgrep -f "uvicorn.*api.main:app" > /dev/null; then \
		echo -e "$(GREEN)✅ Running$(RESET) (port 10501)"; \
	else \
		echo -e "$(RED)❌ Not running$(RESET)"; \
	fi
	@echo -n -e "  Vite Dev Server:    "; \
	if pgrep -f "vite.*tauri-dashboard" > /dev/null; then \
		echo -e "$(GREEN)✅ Running$(RESET) (port 5173)"; \
	else \
		echo -e "$(RED)❌ Not running$(RESET)"; \
	fi
	@echo -n -e "  Tauri Dev:          "; \
	if pgrep -f "tauri dev" > /dev/null; then \
		echo -e "$(GREEN)✅ Running$(RESET)"; \
	else \
		echo -e "$(RED)❌ Not running$(RESET)"; \
	fi
