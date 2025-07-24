# Makefile.env.mk - Environment Setup and Tool Management for yesman-claude
# Unified dependency management, tool installation, and environment setup

# ==============================================================================
# Environment Configuration
# ==============================================================================

# Colors are now exported from main Makefile

# Tool categories
PYTHON_TOOLS = ruff mypy black isort pytest pytest-cov bandit safety
DEV_TOOLS = ipython ipdb rich textual click typer
QUALITY_TOOLS = radon vulture pylint flake8
DOC_TOOLS = sphinx pdoc mkdocs mkdocs-material
ALL_TOOLS = $(PYTHON_TOOLS) $(DEV_TOOLS) $(QUALITY_TOOLS) $(DOC_TOOLS)

# ==============================================================================
# Project Installation
# ==============================================================================

.PHONY: install install-dev install-test install-all dev-install

install: ## install yesman-claude in development mode
	@echo -e "$(CYAN)Installing $(PROJECT_NAME)...$(RESET)"
	uv pip install -e .
	@echo -e "$(GREEN)✅ $(PROJECT_NAME) installed successfully$(RESET)"

install-dev: ## install with dev dependencies
	@echo -e "$(CYAN)Installing with dev dependencies...$(RESET)"
	uv pip install -e . --group dev
	@echo -e "$(GREEN)✅ Dev dependencies installed$(RESET)"

install-test: ## install with test dependencies
	@echo -e "$(CYAN)Installing with test dependencies...$(RESET)"
	uv pip install -e . --group test
	@echo -e "$(GREEN)✅ Test dependencies installed$(RESET)"

install-all: ## install with all dependencies (dev + test)
	@echo -e "$(CYAN)Installing with all dependencies...$(RESET)"
	uv pip install -e . --group dev --group test
	@echo -e "$(GREEN)✅ All dependencies installed$(RESET)"

dev-install: ## install with pip editable mode
	@echo -e "$(CYAN)Installing with pip editable mode...$(RESET)"
	pip install -e . --config-settings editable_mode=compat
	@echo -e "$(GREEN)✅ Installed in editable mode$(RESET)"

# ==============================================================================
# Dependency Management
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
# Tool Installation
# ==============================================================================

.PHONY: install-tools install-dev-tools install-test-tools install-quality-tools
.PHONY: install-doc-tools install-all-tools tools-upgrade

install-tools: ## install essential development tools
	@echo -e "$(CYAN)Installing essential development tools...$(RESET)"
	pip install --upgrade pip setuptools wheel
	pip install $(PYTHON_TOOLS)
	@echo -e "$(GREEN)✅ Essential tools installed$(RESET)"

install-dev-tools: ## install development and debugging tools
	@echo -e "$(CYAN)Installing development tools...$(RESET)"
	pip install $(DEV_TOOLS)
	@echo -e "$(GREEN)✅ Development tools installed$(RESET)"

install-test-tools: ## install testing tools
	@echo -e "$(CYAN)Installing testing tools...$(RESET)"
	pip install pytest pytest-cov pytest-mock pytest-asyncio pytest-xdist pytest-watch
	pip install coverage hypothesis faker factory-boy
	@echo -e "$(GREEN)✅ Testing tools installed$(RESET)"

install-quality-tools: ## install code quality tools
	@echo -e "$(CYAN)Installing code quality tools...$(RESET)"
	pip install $(QUALITY_TOOLS)
	pip install pre-commit detect-secrets
	@echo -e "$(GREEN)✅ Quality tools installed$(RESET)"

install-doc-tools: ## install documentation tools
	@echo -e "$(CYAN)Installing documentation tools...$(RESET)"
	pip install $(DOC_TOOLS)
	pip install sphinx-rtd-theme sphinx-autodoc-typehints
	@echo -e "$(GREEN)✅ Documentation tools installed$(RESET)"

install-all-tools: install-tools install-dev-tools install-test-tools install-quality-tools install-doc-tools ## install all tools
	@echo -e "$(GREEN)✅ All tools installed successfully$(RESET)"

tools-upgrade: ## upgrade all installed tools
	@echo -e "$(CYAN)Upgrading all tools...$(RESET)"
	pip install --upgrade $(ALL_TOOLS)
	@echo -e "$(GREEN)✅ All tools upgraded$(RESET)"

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
# Environment Setup
# ==============================================================================

.PHONY: setup-all setup-env setup-vscode setup-pycharm setup-hooks setup-complete

setup-all: install-all install-all-tools setup-hooks ## complete project setup
	@echo -e "$(GREEN)🎉 Complete project setup finished!$(RESET)"
	@echo -e "$(YELLOW)Next steps:$(RESET)"
	@echo "  1. Run $(CYAN)make quick$(RESET) to verify setup"
	@echo "  2. Run $(CYAN)make help$(RESET) to see available commands"

setup-env: ## setup development environment
	@echo -e "$(CYAN)Setting up development environment...$(RESET)"
	@$(MAKE) install-all-tools
	@$(MAKE) deps-install
	@$(MAKE) setup-hooks
	@echo -e "$(GREEN)✅ Development environment ready$(RESET)"

setup-vscode: ## setup VS Code settings
	@echo -e "$(CYAN)Setting up VS Code...$(RESET)"
	@mkdir -p .vscode
	@echo '{\n  "python.linting.enabled": true,\n  "python.linting.ruffEnabled": true,\n  "python.formatting.provider": "black",\n  "python.testing.pytestEnabled": true,\n  "editor.formatOnSave": true,\n  "python.linting.mypyEnabled": true\n}' > .vscode/settings.json
	@echo -e "$(GREEN)✅ VS Code configured$(RESET)"

setup-pycharm: ## setup PyCharm settings
	@echo -e "$(CYAN)Setting up PyCharm...$(RESET)"
	@mkdir -p .idea
	@echo -e "$(YELLOW)PyCharm configuration:$(RESET)"
	@echo "  1. Set Python interpreter"
	@echo "  2. Enable pytest as test runner"
	@echo "  3. Configure black as formatter"
	@echo "  4. Enable mypy inspections"

setup-hooks: ## setup git hooks
	@echo -e "$(CYAN)Setting up git hooks...$(RESET)"
	@command -v pre-commit >/dev/null 2>&1 || pip install pre-commit
	@pre-commit install
	@echo -e "$(GREEN)✅ Git hooks configured$(RESET)"

setup-complete: setup-env setup-vscode ## complete development setup
	@echo -e "$(GREEN)🎉 Complete development setup finished!$(RESET)"
	@echo ""
	@echo -e "$(YELLOW)Next steps:$(RESET)"
	@echo "  1. Activate your virtual environment"
	@echo "  2. Run $(CYAN)make test$(RESET) to verify setup"
	@echo "  3. Run $(CYAN)make help$(RESET) to see available commands"

# ==============================================================================
# Tool Status and Management
# ==============================================================================

.PHONY: tools-status tools-check tools-list tools-outdated

tools-status: ## check status of installed tools
	@echo -e "$(CYAN)Development Tools Status$(RESET)"
	@echo -e "$(BLUE)========================$(RESET)"
	@echo ""
	@echo -e "$(YELLOW)Essential Tools:$(RESET)"
	@for tool in ruff mypy black isort pytest; do \
		if command -v $$tool >/dev/null 2>&1; then \
			printf "  %-15s $(GREEN)✅ Installed$(RESET) - " "$$tool"; \
			$$tool --version 2>/dev/null | head -1 || echo "version unknown"; \
		else \
			printf "  %-15s $(RED)❌ Not installed$(RESET)\n" "$$tool"; \
		fi; \
	done
	@echo ""
	@echo -e "$(YELLOW)Quality Tools:$(RESET)"
	@for tool in bandit safety radon vulture; do \
		if command -v $$tool >/dev/null 2>&1; then \
			printf "  %-15s $(GREEN)✅ Installed$(RESET)\n" "$$tool"; \
		else \
			printf "  %-15s $(RED)❌ Not installed$(RESET)\n" "$$tool"; \
		fi; \
	done

tools-check: ## verify all required tools are installed
	@echo -e "$(CYAN)Checking required tools...$(RESET)"
	@missing=0; \
	for tool in python pip uv git make; do \
		if ! command -v $$tool >/dev/null 2>&1; then \
			echo "$(RED)❌ Missing required tool: $$tool$(RESET)"; \
			missing=1; \
		fi; \
	done; \
	if [ $$missing -eq 0 ]; then \
		echo "$(GREEN)✅ All required tools are installed$(RESET)"; \
	else \
		echo "$(RED)Please install missing tools before continuing$(RESET)"; \
		exit 1; \
	fi

tools-list: ## list all available tools with descriptions
	@echo -e "$(CYAN)Available Development Tools$(RESET)"
	@echo -e "$(BLUE)============================$(RESET)"
	@echo ""
	@echo -e "$(YELLOW)🔧 Essential Tools:$(RESET)"
	@echo "  • $(CYAN)ruff$(RESET)         - Fast Python linter"
	@echo "  • $(CYAN)mypy$(RESET)         - Static type checker"
	@echo "  • $(CYAN)black$(RESET)        - Code formatter"
	@echo "  • $(CYAN)isort$(RESET)        - Import sorter"
	@echo "  • $(CYAN)pytest$(RESET)       - Testing framework"
	@echo ""
	@echo -e "$(YELLOW)🛡️  Security Tools:$(RESET)"
	@echo "  • $(CYAN)bandit$(RESET)       - Security linter"
	@echo "  • $(CYAN)safety$(RESET)       - Dependency checker"
	@echo "  • $(CYAN)pip-audit$(RESET)    - Package auditor"
	@echo ""
	@echo -e "$(YELLOW)📊 Analysis Tools:$(RESET)"
	@echo "  • $(CYAN)radon$(RESET)        - Code metrics"
	@echo "  • $(CYAN)vulture$(RESET)      - Dead code finder"
	@echo "  • $(CYAN)prospector$(RESET)   - Code analyzer"
	@echo ""
	@echo -e "$(YELLOW)📚 Documentation:$(RESET)"
	@echo "  • $(CYAN)sphinx$(RESET)       - Documentation generator"
	@echo "  • $(CYAN)mkdocs$(RESET)       - Project documentation"
	@echo "  • $(CYAN)pdoc$(RESET)         - API documentation"

tools-outdated: ## show outdated tools
	@echo -e "$(CYAN)Checking for outdated tools...$(RESET)"
	@pip list --outdated | grep -E "($(subst $(space),|,$(ALL_TOOLS)))" || echo "$(GREEN)All tools are up to date$(RESET)"

# ==============================================================================
# Environment Information
# ==============================================================================

.PHONY: env-info deps-info

env-info: ## show environment information
	@echo -e "$(CYAN)"
	@echo "╔══════════════════════════════════════════════════════════════════════════════╗"
	@echo "║                         $(YELLOW)Environment Information$(CYAN)                         ║"
	@echo "╚══════════════════════════════════════════════════════════════════════════════╝"
	@echo "$(RESET)"
	@echo -e "$(GREEN)🐍 Python Environment:$(RESET)"
	@echo "  Python:         $$(python --version 2>&1)"
	@echo "  UV:            $$(uv --version 2>&1 || echo 'Not installed')"
	@echo "  pip:           $$(pip --version | cut -d' ' -f2)"
	@echo ""
	@echo -e "$(GREEN)📦 Dependencies:$(RESET)"
	@pip list | tail -n +3 | wc -l | xargs printf "  Installed packages: %d\n"
	@pip list --outdated 2>/dev/null | tail -n +3 | wc -l | xargs printf "  Outdated packages:  %d\n"
	@echo ""
	@echo -e "$(GREEN)🔧 Available Commands:$(RESET)"
	@echo "  • $(CYAN)install-all$(RESET)         Install everything"
	@echo "  • $(CYAN)setup-all$(RESET)           Complete setup"
	@echo "  • $(CYAN)tools-status$(RESET)        Check tool status"
	@echo "  • $(CYAN)deps-outdated$(RESET)       Check outdated deps"
	@echo "  • $(CYAN)deps-security$(RESET)       Security scan"

deps-info: env-info ## show dependency information (alias)