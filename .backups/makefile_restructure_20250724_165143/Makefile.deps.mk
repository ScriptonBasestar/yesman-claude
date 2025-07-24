# Makefile.deps.mk - Dependency Management for yesman-claude
# Python dependency management, updates, and security checks

# ==============================================================================
# Dependency Configuration
# ==============================================================================

# Colors are now exported from main Makefile

# ==============================================================================
# Dependency Management Targets
# ==============================================================================

.PHONY: deps deps-install deps-update deps-upgrade deps-sync deps-check
.PHONY: deps-tree deps-outdated deps-security deps-clean deps-freeze

deps: deps-install ## install dependencies (alias)

deps-install: ## install project dependencies
	@echo -e "$(CYAN)Installing project dependencies...$(RESET)"
	uv pip install -e .
	@echo -e "$(GREEN)✅ Dependencies installed$(RESET)"

deps-update: ## update dependencies to latest compatible versions
	@echo -e "$(CYAN)Updating dependencies...$(RESET)"
	uv pip install --upgrade -e .
	@echo -e "$(GREEN)✅ Dependencies updated$(RESET)"

deps-upgrade: ## upgrade all dependencies to latest versions
	@echo -e "$(CYAN)Upgrading all dependencies to latest versions...$(RESET)"
	@if [ -f "requirements.txt" ]; then \
		pip install --upgrade -r requirements.txt; \
	fi
	@if [ -f "requirements-dev.txt" ]; then \
		pip install --upgrade -r requirements-dev.txt; \
	fi
	@echo -e "$(GREEN)✅ Dependencies upgraded$(RESET)"

deps-sync: ## sync dependencies with lock file
	@echo -e "$(CYAN)Syncing dependencies...$(RESET)"
	uv pip sync
	@echo -e "$(GREEN)✅ Dependencies synced$(RESET)"

deps-check: ## check dependency conflicts and issues
	@echo -e "$(CYAN)Checking dependencies...$(RESET)"
	pip check
	@echo -e "$(GREEN)✅ Dependency check completed$(RESET)"

deps-tree: ## show dependency tree
	@echo -e "$(CYAN)Dependency tree:$(RESET)"
	@command -v pipdeptree >/dev/null 2>&1 || pip install pipdeptree
	@pipdeptree

deps-outdated: ## show outdated dependencies
	@echo -e "$(CYAN)Checking for outdated dependencies...$(RESET)"
	pip list --outdated

deps-security: ## check dependencies for security vulnerabilities
	@echo -e "$(CYAN)Running security vulnerability check...$(RESET)"
	@command -v safety >/dev/null 2>&1 || pip install safety
	@safety check || echo "$(YELLOW)⚠️  Some vulnerabilities found$(RESET)"

deps-clean: ## remove unused dependencies
	@echo -e "$(CYAN)Cleaning unused dependencies...$(RESET)"
	@command -v pip-autoremove >/dev/null 2>&1 || pip install pip-autoremove
	@pip-autoremove -y
	@echo -e "$(GREEN)✅ Unused dependencies removed$(RESET)"

deps-freeze: ## freeze current dependencies
	@echo -e "$(CYAN)Freezing dependencies...$(RESET)"
	pip freeze > requirements.freeze.txt
	@echo -e "$(GREEN)✅ Dependencies frozen to requirements.freeze.txt$(RESET)"

# ==============================================================================
# Requirements File Management
# ==============================================================================

.PHONY: reqs-generate reqs-compile reqs-update reqs-dev reqs-test

reqs-generate: ## generate requirements files from pyproject.toml
	@echo -e "$(CYAN)Generating requirements files...$(RESET)"
	@if command -v pip-compile >/dev/null 2>&1; then \
		pip-compile pyproject.toml -o requirements.txt; \
		echo "$(GREEN)✅ requirements.txt generated$(RESET)"; \
	else \
		echo "$(YELLOW)pip-tools not installed. Install with: pip install pip-tools$(RESET)"; \
	fi

reqs-compile: ## compile requirements with hashes
	@echo -e "$(CYAN)Compiling requirements with hashes...$(RESET)"
	@command -v pip-compile >/dev/null 2>&1 || pip install pip-tools
	pip-compile --generate-hashes pyproject.toml -o requirements.txt
	@echo -e "$(GREEN)✅ Requirements compiled with hashes$(RESET)"

reqs-update: ## update requirements files
	@echo -e "$(CYAN)Updating requirements files...$(RESET)"
	@command -v pip-compile >/dev/null 2>&1 || pip install pip-tools
	pip-compile --upgrade pyproject.toml -o requirements.txt
	@echo -e "$(GREEN)✅ Requirements updated$(RESET)"

reqs-dev: ## generate dev requirements
	@echo -e "$(CYAN)Generating dev requirements...$(RESET)"
	pip freeze | grep -E "(ruff|mypy|black|pytest|bandit)" > requirements-dev.txt
	@echo -e "$(GREEN)✅ Dev requirements generated$(RESET)"

reqs-test: ## generate test requirements
	@echo -e "$(CYAN)Generating test requirements...$(RESET)"
	pip freeze | grep -E "(pytest|pytest-|mock)" > requirements-test.txt
	@echo -e "$(GREEN)✅ Test requirements generated$(RESET)"

# ==============================================================================
# Virtual Environment Management
# ==============================================================================

.PHONY: venv venv-create venv-activate venv-clean

venv: venv-create ## create virtual environment (alias)

venv-create: ## create new virtual environment
	@echo -e "$(CYAN)Creating virtual environment...$(RESET)"
	python -m venv .venv
	@echo -e "$(GREEN)✅ Virtual environment created$(RESET)"
	@echo -e "$(YELLOW)Activate with: source .venv/bin/activate$(RESET)"

venv-activate: ## show how to activate virtual environment
	@echo -e "$(CYAN)To activate virtual environment:$(RESET)"
	@echo "  $(YELLOW)source .venv/bin/activate$(RESET)  (Linux/Mac)"
	@echo "  $(YELLOW).venv\\Scripts\\activate$(RESET)     (Windows)"

venv-clean: ## remove virtual environment
	@echo -e "$(CYAN)Removing virtual environment...$(RESET)"
	rm -rf .venv
	@echo -e "$(GREEN)✅ Virtual environment removed$(RESET)"

# ==============================================================================
# Dependency Information
# ==============================================================================

.PHONY: deps-info deps-licenses deps-size

deps-info: ## show dependency information
	@echo -e "$(CYAN)"
	@echo "╔══════════════════════════════════════════════════════════════════════════════╗"
	@echo "║                         $(YELLOW)Dependency Information$(CYAN)                          ║"
	@echo "╚══════════════════════════════════════════════════════════════════════════════╝"
	@echo "$(RESET)"
	@echo -e "$(GREEN)📦 Package Management:$(RESET)"
	@echo "  Tool:           $(YELLOW)uv (primary), pip (fallback)$(RESET)"
	@echo "  Config:         $(YELLOW)pyproject.toml$(RESET)"
	@echo "  Python:         $$(python --version 2>&1)"
	@echo ""
	@echo -e "$(GREEN)📊 Dependency Statistics:$(RESET)"
	@pip list | tail -n +3 | wc -l | xargs printf "  Installed packages: %d\n"
	@pip list --outdated 2>/dev/null | tail -n +3 | wc -l | xargs printf "  Outdated packages:  %d\n"
	@echo ""
	@echo -e "$(GREEN)🎯 Management Commands:$(RESET)"
	@echo "  • $(CYAN)deps-install$(RESET)        Install dependencies"
	@echo "  • $(CYAN)deps-update$(RESET)         Update to compatible versions"
	@echo "  • $(CYAN)deps-upgrade$(RESET)        Upgrade to latest versions"
	@echo "  • $(CYAN)deps-tree$(RESET)           Show dependency tree"
	@echo "  • $(CYAN)deps-outdated$(RESET)       List outdated packages"
	@echo "  • $(CYAN)deps-security$(RESET)       Security vulnerability scan"

deps-licenses: ## show dependency licenses
	@echo -e "$(CYAN)Dependency Licenses:$(RESET)"
	@command -v pip-licenses >/dev/null 2>&1 || pip install pip-licenses
	@pip-licenses --with-authors --order=license

deps-size: ## show dependency sizes
	@echo -e "$(CYAN)Dependency Sizes:$(RESET)"
	@du -sh $$(python -c "import site; print(site.getsitepackages()[0])") 2>/dev/null || \
		echo "$(YELLOW)Cannot determine site-packages location$(RESET)"
	@echo ""
	@echo -e "$(YELLOW)Top 10 largest packages:$(RESET)"
	@find $$(python -c "import site; print(site.getsitepackages()[0])") -maxdepth 1 -type d -exec du -sh {} \; 2>/dev/null | sort -hr | head -10 || \
		echo "$(YELLOW)Cannot analyze package sizes$(RESET)"