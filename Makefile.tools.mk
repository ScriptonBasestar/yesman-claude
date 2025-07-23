# Makefile.tools.mk - Tool Management for yesman-claude
# Development tool installation, updates, and management

# ==============================================================================
# Tools Configuration
# ==============================================================================

# Colors are now exported from main Makefile

# Tool categories
PYTHON_TOOLS = ruff mypy black isort pytest pytest-cov bandit safety
DEV_TOOLS = ipython ipdb rich textual click typer
QUALITY_TOOLS = radon vulture pylint flake8
DOC_TOOLS = sphinx pdoc mkdocs mkdocs-material
ALL_TOOLS = $(PYTHON_TOOLS) $(DEV_TOOLS) $(QUALITY_TOOLS) $(DOC_TOOLS)

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
# Tool Status and Management
# ==============================================================================

.PHONY: tools-status tools-check tools-list tools-outdated tools-clean

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

tools-clean: ## remove tool caches and temporary files
	@echo -e "$(CYAN)Cleaning tool caches...$(RESET)"
	@rm -rf .mypy_cache/
	@rm -rf .pytest_cache/
	@rm -rf .ruff_cache/
	@rm -rf .coverage
	@rm -f .coverage.*
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo -e "$(GREEN)✅ Tool caches cleaned$(RESET)"

# ==============================================================================
# Environment Setup
# ==============================================================================

.PHONY: setup-env setup-vscode setup-pycharm setup-hooks setup-complete

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

setup-hooks: pre-commit-install ## setup git hooks
	@echo -e "$(GREEN)✅ Git hooks configured$(RESET)"

setup-complete: setup-env setup-vscode ## complete development setup
	@echo -e "$(GREEN)🎉 Complete development setup finished!$(RESET)"
	@echo ""
	@echo -e "$(YELLOW)Next steps:$(RESET)"
	@echo "  1. Activate your virtual environment"
	@echo "  2. Run $(CYAN)make test$(RESET) to verify setup"
	@echo "  3. Run $(CYAN)make help$(RESET) to see available commands"

# ==============================================================================
# Mock and Stub Generation
# ==============================================================================

.PHONY: generate-mocks generate-stubs update-stubs

generate-mocks: ## generate mock files for testing
	@echo -e "$(CYAN)Generating mock files...$(RESET)"
	@command -v pytest-mock >/dev/null 2>&1 || pip install pytest-mock
	@echo -e "$(YELLOW)Mock generation is project-specific$(RESET)"
	@echo "Add your mock generation commands here"

generate-stubs: ## generate type stubs
	@echo -e "$(CYAN)Generating type stubs...$(RESET)"
	@command -v stubgen >/dev/null 2>&1 || pip install mypy
	@stubgen -p libs -o stubs/
	@stubgen -p commands -o stubs/
	@echo -e "$(GREEN)✅ Type stubs generated in stubs/$(RESET)"

update-stubs: generate-stubs ## update type stubs
	@echo -e "$(GREEN)✅ Type stubs updated$(RESET)"

# ==============================================================================
# Tool Specific Commands
# ==============================================================================

.PHONY: ruff-config mypy-config pytest-config pre-commit-config

ruff-config: ## generate ruff configuration
	@echo -e "$(CYAN)Generating ruff configuration...$(RESET)"
	@echo "[tool.ruff]\nline-length = 100\nselect = [\"E\", \"F\", \"I\", \"N\", \"W\"]\nignore = [\"E501\"]\n" > ruff.toml
	@echo -e "$(GREEN)✅ ruff.toml created$(RESET)"

mypy-config: ## generate mypy configuration
	@echo -e "$(CYAN)Generating mypy configuration...$(RESET)"
	@echo "[mypy]\npython_version = \"3.11\"\nwarn_return_any = true\nwarn_unused_configs = true\ndisallow_untyped_defs = true\n" > mypy.ini
	@echo -e "$(GREEN)✅ mypy.ini created$(RESET)"

pytest-config: ## generate pytest configuration
	@echo -e "$(CYAN)Generating pytest configuration...$(RESET)"
	@echo "[tool.pytest.ini_options]\nminversion = \"6.0\"\naddopts = \"-ra -q --strict-markers\"\ntestpaths = [\"tests\"]\n" > pytest.ini
	@echo -e "$(GREEN)✅ pytest.ini created$(RESET)"

pre-commit-config: ## generate pre-commit configuration
	@echo -e "$(CYAN)Generating pre-commit configuration...$(RESET)"
	@if [ ! -f .pre-commit-config.yaml ]; then \
		echo "repos:" > .pre-commit-config.yaml; \
		echo "  - repo: https://github.com/pre-commit/pre-commit-hooks" >> .pre-commit-config.yaml; \
		echo "    rev: v4.5.0" >> .pre-commit-config.yaml; \
		echo "    hooks:" >> .pre-commit-config.yaml; \
		echo "      - id: trailing-whitespace" >> .pre-commit-config.yaml; \
		echo "      - id: end-of-file-fixer" >> .pre-commit-config.yaml; \
		echo "      - id: check-yaml" >> .pre-commit-config.yaml; \
		echo "      - id: check-added-large-files" >> .pre-commit-config.yaml; \
		echo "  - repo: https://github.com/psf/black" >> .pre-commit-config.yaml; \
		echo "    rev: 23.12.1" >> .pre-commit-config.yaml; \
		echo "    hooks:" >> .pre-commit-config.yaml; \
		echo "      - id: black" >> .pre-commit-config.yaml; \
		echo "  - repo: https://github.com/pycqa/isort" >> .pre-commit-config.yaml; \
		echo "    rev: 5.13.2" >> .pre-commit-config.yaml; \
		echo "    hooks:" >> .pre-commit-config.yaml; \
		echo "      - id: isort" >> .pre-commit-config.yaml; \
		echo "  - repo: https://github.com/charliermarsh/ruff-pre-commit" >> .pre-commit-config.yaml; \
		echo "    rev: v0.1.9" >> .pre-commit-config.yaml; \
		echo "    hooks:" >> .pre-commit-config.yaml; \
		echo "      - id: ruff" >> .pre-commit-config.yaml; \
		echo "$(GREEN)✅ .pre-commit-config.yaml created$(RESET)"; \
	else \
		echo "$(YELLOW).pre-commit-config.yaml already exists$(RESET)"; \
	fi

# ==============================================================================
# Tool Information
# ==============================================================================

.PHONY: tools-info

tools-info: ## show comprehensive tool information
	@echo -e "$(CYAN)"
	@echo "╔══════════════════════════════════════════════════════════════════════════════╗"
	@echo "║                         $(YELLOW)Tool Management Information$(CYAN)                      ║"
	@echo "╚══════════════════════════════════════════════════════════════════════════════╝"
	@echo "$(RESET)"
	@echo -e "$(GREEN)🔧 Tool Categories:$(RESET)"
	@echo "  • $(CYAN)Essential$(RESET)       Core development tools"
	@echo "  • $(CYAN)Testing$(RESET)         Test frameworks and utilities"
	@echo "  • $(CYAN)Quality$(RESET)         Code quality and analysis"
	@echo "  • $(CYAN)Security$(RESET)        Security scanning tools"
	@echo "  • $(CYAN)Documentation$(RESET)   Doc generation tools"
	@echo ""
	@echo -e "$(GREEN)📦 Installation Commands:$(RESET)"
	@echo "  • $(CYAN)install-tools$(RESET)         Essential tools only"
	@echo "  • $(CYAN)install-all-tools$(RESET)     Everything"
	@echo "  • $(CYAN)tools-upgrade$(RESET)         Upgrade all tools"
	@echo ""
	@echo -e "$(GREEN)🔍 Management Commands:$(RESET)"
	@echo "  • $(CYAN)tools-status$(RESET)          Check installed tools"
	@echo "  • $(CYAN)tools-outdated$(RESET)        Find outdated tools"
	@echo "  • $(CYAN)tools-clean$(RESET)           Clean tool caches"
	@echo ""
	@echo -e "$(GREEN)⚙️  Setup Commands:$(RESET)"
	@echo "  • $(CYAN)setup-env$(RESET)             Complete environment"
	@echo "  • $(CYAN)setup-vscode$(RESET)          VS Code configuration"
	@echo "  • $(CYAN)setup-hooks$(RESET)           Git hooks"