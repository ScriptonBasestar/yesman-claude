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
	@pkill -f "yesman" || echo "$(GREEN)No running yesman processes found$(RESET)"

restart: stop start ## restart yesman

status: ## check yesman status
	@echo -e "$(CYAN)Checking for running yesman processes...$(RESET)"
	@pgrep -f "yesman" > /dev/null && echo "$(GREEN)✅ yesman is running$(RESET)" || echo "$(RED)❌ yesman is not running$(RESET)"

logs: ## show recent log files
	@echo -e "$(CYAN)Recent log files:$(RESET)"
	@find . -name "*.log" -type f -mtime -7 -exec ls -la {} \; 2>/dev/null || echo "$(YELLOW)No recent log files found$(RESET)"

run: ## run yesman.py
	@echo -e "$(CYAN)Running yesman...$(RESET)"
	uv run ./yesman.py

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

.PHONY: shell console format-imports type-check security-check profile

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

# ==============================================================================
# Documentation
# ==============================================================================

.PHONY: docs docs-serve docs-build api-docs changelog

docs: docs-serve ## alias for docs-serve

docs-serve: ## serve documentation locally
	@echo -e "$(CYAN)Starting documentation server...$(RESET)"
	@if [ -d "docs" ]; then \
		python -m http.server 8000 --directory docs; \
	else \
		echo "$(YELLOW)No docs directory found$(RESET)"; \
	fi

docs-build: ## build documentation
	@echo -e "$(CYAN)Building documentation...$(RESET)"
	@command -v sphinx-build >/dev/null 2>&1 || pip install sphinx
	@if [ -f "docs/conf.py" ]; then \
		sphinx-build -b html docs docs/_build; \
		echo "$(GREEN)✅ Documentation built in docs/_build$(RESET)"; \
	else \
		echo "$(YELLOW)No Sphinx configuration found$(RESET)"; \
	fi

api-docs: ## generate API documentation
	@echo -e "$(CYAN)Generating API documentation...$(RESET)"
	@command -v pdoc >/dev/null 2>&1 || pip install pdoc
	@pdoc --html --output-dir docs/api libs commands
	@echo -e "$(GREEN)✅ API docs generated in docs/api$(RESET)"

changelog: ## generate changelog
	@echo -e "$(CYAN)Generating changelog...$(RESET)"
	@if [ -f ".git/HEAD" ]; then \
		git log --pretty=format:"* %s (%h)" --reverse > CHANGELOG.tmp.md; \
		echo "$(GREEN)✅ Changelog generated in CHANGELOG.tmp.md$(RESET)"; \
	else \
		echo "$(RED)Not a git repository$(RESET)"; \
	fi

# ==============================================================================
# Development Information
# ==============================================================================

.PHONY: dev-info dev-status env-info

dev-info: ## show development environment information
	@echo -e "$(CYAN)"
	@echo "╔══════════════════════════════════════════════════════════════════════════════╗"
	@echo "║                         $(MAGENTA)Development Environment$(CYAN)                         ║"
	@echo "╚══════════════════════════════════════════════════════════════════════════════╝"
	@echo "$(RESET)"
	@echo -e "$(GREEN)🏗️  Environment Details:$(RESET)"
	@echo "  Python:         $$(python --version 2>&1)"
	@echo "  UV:            $$(uv --version 2>&1 || echo 'Not installed')"
	@echo "  pip:           $$(pip --version | cut -d' ' -f2)"
	@echo "  Platform:      $$(python -c 'import platform; print(platform.platform())')"
	@echo ""
	@echo -e "$(GREEN)🔄 Development Workflows:$(RESET)"
	@echo "  • $(CYAN)dev$(RESET)                 Standard development workflow"
	@echo "  • $(CYAN)dev-fast$(RESET)            Quick development cycle"
	@echo "  • $(CYAN)quick$(RESET)               Quick check (lint + test)"
	@echo "  • $(CYAN)full$(RESET)                Full quality check"
	@echo "  • $(CYAN)verify$(RESET)              Complete verification"
	@echo "  • $(CYAN)ci-local$(RESET)            Run full CI locally"
	@echo ""
	@echo -e "$(GREEN)🚀 Quick Commands:$(RESET)"
	@echo "  • $(CYAN)start$(RESET)               Start yesman"
	@echo "  • $(CYAN)stop$(RESET)                Stop yesman"
	@echo "  • $(CYAN)restart$(RESET)             Restart yesman"
	@echo "  • $(CYAN)status$(RESET)              Check status"
	@echo "  • $(CYAN)logs$(RESET)                Show log files"

dev-status: ## show current development status
	@echo -e "$(CYAN)Development Status Check$(RESET)"
	@echo -e "$(BLUE)========================$(RESET)"
	@echo ""
	@echo -e "$(GREEN)📊 Project Status:$(RESET)"
	@printf "  %-20s " "Git Status:"; if git status --porcelain | grep -q .; then echo "$(YELLOW)Modified files$(RESET)"; else echo "$(GREEN)Clean$(RESET)"; fi
	@printf "  %-20s " "Current Branch:"; git branch --show-current 2>/dev/null || echo "$(RED)Unknown$(RESET)"
	@printf "  %-20s " "Last Commit:"; git log -1 --format="%h %s" 2>/dev/null | cut -c1-50 || echo "$(RED)No commits$(RESET)"
	@echo ""
	@echo -e "$(GREEN)🔧 Development Status:$(RESET)"
	@printf "  %-20s " "Tests Passing:"; if make test-unit > /dev/null 2>&1; then echo "$(GREEN)Yes$(RESET)"; else echo "$(RED)No$(RESET)"; fi
	@printf "  %-20s " "Coverage File:"; if [ -f ".coverage" ]; then echo "$(GREEN)Yes$(RESET)"; else echo "$(YELLOW)No$(RESET)"; fi
	@printf "  %-20s " "Virtual Env:"; if [ -n "$$VIRTUAL_ENV" ]; then echo "$(GREEN)Active$(RESET)"; else echo "$(YELLOW)None$(RESET)"; fi

env-info: ## show environment variables
	@echo -e "$(CYAN)Environment Variables:$(RESET)"
	@echo -e "$(YELLOW)Python-related:$(RESET)"
	@env | grep -E "PYTHON|PATH|VIRTUAL" | sort || echo "  No Python env vars set"
	@echo ""
	@echo -e "$(YELLOW)Project-related:$(RESET)"
	@env | grep -i "yesman" | sort || echo "  No project env vars set"