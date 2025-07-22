# Makefile - yesman-claude Development Automation
# Modular Makefile structure with comprehensive functionality
# Automated Claude CLI tool with project management

# ==============================================================================
# Project Configuration
# ==============================================================================

# Project metadata
PROJECT_NAME := yesman-claude
EXECUTABLE_NAME := yesman
VERSION ?= $(shell git describe --always --abbrev=0 --tags 2>/dev/null || echo "dev")

# Python configuration
export UV_SYSTEM_PYTHON=true

# Colors for output (exported for use in all included modules)
export CYAN := \033[36m
export GREEN := \033[32m
export YELLOW := \033[33m
export RED := \033[31m
export BLUE := \033[34m
export MAGENTA := \033[35m
export RESET := \033[0m

# ==============================================================================
# Include Modular Makefiles
# ==============================================================================

include Makefile.deps.mk     # Dependency management
include Makefile.build.mk    # Build and installation
include Makefile.test.mk     # Testing and coverage
include Makefile.quality.mk  # Code quality and linting
include Makefile.tools.mk    # Tool installation and management
include Makefile.dev.mk      # Development workflow
include Makefile.docker.mk   # Docker operations

# ==============================================================================
# Enhanced Help System
# ==============================================================================

.DEFAULT_GOAL := help

.PHONY: help help-full help-build help-test help-quality help-deps help-dev
.PHONY: help-tools help-docker

help: ## show main help menu with categories
	@echo "$(CYAN)"
	@echo "╔══════════════════════════════════════════════════════════════════════════════╗"
	@echo "║                           $(MAGENTA)yesman-claude Makefile Help$(CYAN)                       ║"
	@echo "║                    $(YELLOW)Automated Claude CLI Tool$(CYAN)                              ║"
	@echo "╚══════════════════════════════════════════════════════════════════════════════╝"
	@echo "$(RESET)"
	@echo "$(GREEN)📋 Main Categories:$(RESET)"
	@echo "  $(YELLOW)make help-build$(RESET)    🔨 Build, installation, and deployment"
	@echo "  $(YELLOW)make help-test$(RESET)     🧪 Testing, coverage, and validation"
	@echo "  $(YELLOW)make help-quality$(RESET)  ✨ Code quality, formatting, and linting"
	@echo "  $(YELLOW)make help-deps$(RESET)     📦 Dependency management and updates"
	@echo "  $(YELLOW)make help-tools$(RESET)    🔧 Tool installation and management"
	@echo "  $(YELLOW)make help-dev$(RESET)      🛠️  Development tools and workflow"
	@echo "  $(YELLOW)make help-docker$(RESET)   🐳 Docker operations and containers"
	@echo ""
	@echo "$(GREEN)🚀 Quick Commands:$(RESET)"
	@echo "  $(CYAN)make start$(RESET)         Start yesman"
	@echo "  $(CYAN)make stop$(RESET)          Stop yesman processes"
	@echo "  $(CYAN)make restart$(RESET)       Restart yesman"
	@echo "  $(CYAN)make status$(RESET)        Check yesman status"
	@echo "  $(CYAN)make quick$(RESET)         Quick check (lint-fast + test-unit)"
	@echo "  $(CYAN)make full$(RESET)          Full quality check (comprehensive)"
	@echo "  $(CYAN)make setup-all$(RESET)     Complete project setup"
	@echo ""
	@echo "$(GREEN)💡 Pro Tips:$(RESET)"
	@echo "  • Use $(YELLOW)'make quick'$(RESET) for fast development iteration"
	@echo "  • Use $(YELLOW)'make full'$(RESET) before committing changes"
	@echo "  • Use $(YELLOW)'make hooks-install'$(RESET) for automatic quality checks"
	@echo "  • All commands support tab completion if configured"
	@echo ""
	@echo "$(BLUE)📖 Documentation: $(RESET)https://github.com/yourusername/yesman-claude"

help-full: help help-build help-test help-quality help-deps help-tools help-dev help-docker ## show all help sections

help-build: ## show build and deployment help
	@echo "$(GREEN)🔨 Build and Installation Commands:$(RESET)"
	@echo "  $(CYAN)build$(RESET)              Build Python package"
	@echo "  $(CYAN)install$(RESET)            Install yesman-claude in development mode"
	@echo "  $(CYAN)install-dev$(RESET)        Install with dev dependencies"
	@echo "  $(CYAN)install-test$(RESET)       Install with test dependencies"
	@echo "  $(CYAN)install-all$(RESET)        Install with all dependencies"
	@echo "  $(CYAN)clean$(RESET)              Clean build artifacts and caches"
	@echo "  $(CYAN)build-dashboard$(RESET)    Build SvelteKit dashboard"
	@echo "  $(CYAN)build-tauri$(RESET)        Build Tauri desktop app"
	@echo "  $(CYAN)build-all$(RESET)          Build complete project"
	@echo "  $(CYAN)build-info$(RESET)         Show build environment information"

help-test: ## show testing help
	@echo "$(GREEN)🧪 Testing and Validation Commands:$(RESET)"
	@echo "  $(CYAN)test$(RESET)               Run all tests with coverage"
	@echo "  $(CYAN)test-unit$(RESET)          Run only unit tests"
	@echo "  $(CYAN)test-integration$(RESET)   Run integration tests"
	@echo "  $(CYAN)test-e2e$(RESET)           Run end-to-end tests"
	@echo "  $(CYAN)test-all$(RESET)           Run all test suites"
	@echo "  $(CYAN)cover$(RESET)              Run tests with coverage report"
	@echo "  $(CYAN)cover-html$(RESET)         Generate HTML coverage report"
	@echo "  $(CYAN)test-watch$(RESET)         Run tests in watch mode"
	@echo "  $(CYAN)test-info$(RESET)          Show testing information and targets"

help-quality: ## show quality help
	@echo "$(GREEN)✨ Code Quality Commands:$(RESET)"
	@echo "  $(CYAN)fmt$(RESET)                Format code with black/isort"
	@echo "  $(CYAN)format-check$(RESET)       Check formatting without fixing"
	@echo "  $(CYAN)type-check$(RESET)         Run mypy type checking"
	@echo "  $(CYAN)security$(RESET)           Run security scans"
	@echo "  $(CYAN)analyze$(RESET)            Code complexity analysis"
	@echo "  $(CYAN)quality$(RESET)            Run standard quality checks"
	@echo "  $(CYAN)quality-strict$(RESET)     Run comprehensive checks"
	@echo "  $(CYAN)quality-info$(RESET)       Show quality tools info"


help-deps: ## show dependency help
	@echo "$(GREEN)📦 Dependency Management Commands:$(RESET)"
	@echo "  $(CYAN)deps-install$(RESET)       Install project dependencies"
	@echo "  $(CYAN)deps-update$(RESET)        Update to compatible versions"
	@echo "  $(CYAN)deps-upgrade$(RESET)       Upgrade to latest versions"
	@echo "  $(CYAN)deps-tree$(RESET)          Show dependency tree"
	@echo "  $(CYAN)deps-outdated$(RESET)      List outdated packages"
	@echo "  $(CYAN)deps-security$(RESET)      Security vulnerability scan"
	@echo "  $(CYAN)deps-info$(RESET)          Show dependency information"
	@echo "  $(CYAN)venv-create$(RESET)        Create virtual environment"

help-tools: ## show tools help
	@echo "$(GREEN)🔧 Tool Management Commands:$(RESET)"
	@echo "  $(CYAN)install-tools$(RESET)      Install essential tools"
	@echo "  $(CYAN)install-all-tools$(RESET)  Install all dev tools"
	@echo "  $(CYAN)tools-status$(RESET)       Check tool installation"
	@echo "  $(CYAN)tools-upgrade$(RESET)      Upgrade all tools"
	@echo "  $(CYAN)setup-env$(RESET)          Setup dev environment"
	@echo "  $(CYAN)setup-complete$(RESET)     Complete dev setup"
	@echo "  $(CYAN)tools-info$(RESET)         Show tool information"

help-dev: ## show development workflow help
	@echo "$(GREEN)🛠️  Development Workflow Commands:$(RESET)"
	@echo "  $(CYAN)dev$(RESET)                Standard development workflow"
	@echo "  $(CYAN)dev-fast$(RESET)           Quick development cycle"
	@echo "  $(CYAN)quick$(RESET)              Quick check (alias for dev-fast)"
	@echo "  $(CYAN)full$(RESET)               Full quality check"
	@echo "  $(CYAN)verify$(RESET)             Complete verification before PR"
	@echo "  $(CYAN)ci-local$(RESET)           Run full CI pipeline locally"
	@echo "  $(CYAN)comments$(RESET)           Show TODO/FIXME/NOTE comments"
	@echo "  $(CYAN)structure$(RESET)          Show project structure"
	@echo "  $(CYAN)dev-info$(RESET)           Show development environment info"

help-docker: ## show docker help
	@echo "$(GREEN)🐳 Docker Commands:$(RESET)"
	@echo "  $(CYAN)docker-build$(RESET)       Build Docker image"
	@echo "  $(CYAN)docker-run$(RESET)         Run Docker container"
	@echo "  $(CYAN)docker-stop$(RESET)        Stop containers"
	@echo "  $(CYAN)docker-push$(RESET)        Push to registry"
	@echo "  $(CYAN)docker-scan$(RESET)        Security scan image"
	@echo "  $(CYAN)compose-up$(RESET)         Start with docker-compose"
	@echo "  $(CYAN)docker-info$(RESET)        Show Docker information"

# ==============================================================================
# Project Information
# ==============================================================================

.PHONY: info version

info: ## show project information and current configuration
	@echo "$(CYAN)"
	@echo "╔══════════════════════════════════════════════════════════════════════════════╗"
	@echo "║                         $(MAGENTA)yesman-claude Project Information$(CYAN)                   ║"
	@echo "╚══════════════════════════════════════════════════════════════════════════════╝"
	@echo "$(RESET)"
	@echo "$(GREEN)📋 Project Details:$(RESET)"
	@echo "  Name:           $(YELLOW)$(PROJECT_NAME)$(RESET)"
	@echo "  Executable:     $(YELLOW)$(EXECUTABLE_NAME)$(RESET)"
	@echo "  Version:        $(YELLOW)$(VERSION)$(RESET)"
	@echo ""
	@echo "$(GREEN)🏗️  Python Environment:$(RESET)"
	@echo "  Python:         $$(python --version 2>&1)"
	@echo "  UV:            $$(uv --version 2>&1 || echo 'Not installed')"
	@echo "  pip:           $$(pip --version | cut -d' ' -f2)"
	@echo ""
	@echo "$(GREEN)📁 Key Features:$(RESET)"
	@echo "  • Automated Claude CLI interaction"
	@echo "  • Project template management"
	@echo "  • tmux session automation"
	@echo "  • Web and Tauri dashboard interfaces"
	@echo "  • Rich CLI interface with Textual"
	@echo ""
	@echo "$(GREEN)🔧 Available Modules:$(RESET)"
	@echo "  • $(CYAN)Dependencies$(RESET)     (Makefile.deps.mk)    - Package management"
	@echo "  • $(CYAN)Build & Deploy$(RESET)   (Makefile.build.mk)   - Build and installation"
	@echo "  • $(CYAN)Testing$(RESET)          (Makefile.test.mk)    - Test suites and coverage"
	@echo "  • $(CYAN)Code Quality$(RESET)     (Makefile.quality.mk) - Formatting and analysis"
	@echo "  • $(CYAN)Tools$(RESET)            (Makefile.tools.mk)   - Tool management"
	@echo "  • $(CYAN)Development$(RESET)      (Makefile.dev.mk)     - Dev workflows"
	@echo "  • $(CYAN)Docker$(RESET)           (Makefile.docker.mk)  - Containerization"


version: ## show version
	@echo "$(PROJECT_NAME) version: $(VERSION)"

# ==============================================================================
# Main Workflow Aliases (defined here to override module definitions)
# ==============================================================================

.PHONY: quick full

# These are the most common workflows, defined at the top level for convenience
quick: dev-fast ## quick development check (lint-fast + test-unit)

full: lint test-coverage ## full quality check (comprehensive lint + coverage)

# ==============================================================================
# End of Main Makefile
# ==============================================================================