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
# Note: These require echo -e or printf for proper color rendering
export CYAN := \033[36m
export GREEN := \033[32m
export YELLOW := \033[33m
export RED := \033[31m
export BLUE := \033[34m
export MAGENTA := \033[35m
export RESET := \033[0m

# Color helper functions for cross-platform compatibility
define print_color
	@printf "$(1)%s$(RESET)\n" "$(2)"
endef

define print_color_inline
	@printf "$(1)%s$(RESET)" "$(2)"
endef

# ==============================================================================
# Include Modular Makefiles
# ==============================================================================

include Makefile.env.mk      # Environment setup and tool management
include Makefile.build.mk    # Build and packaging
include Makefile.test.mk     # Testing and coverage
include Makefile.quality.mk  # Code quality and linting
include Makefile.dev.mk      # Development workflow and servers
include Makefile.ops.mk      # Operations and maintenance

# ==============================================================================
# Enhanced Help System
# ==============================================================================

.DEFAULT_GOAL := help

.PHONY: help help-full help-build help-test help-quality help-env help-dev help-ops

help: ## show main help menu with categories
	@echo -e "$(CYAN)"
	@echo -e "╔══════════════════════════════════════════════════════════════════════════════╗"
	@echo -e "║                           $(MAGENTA)yesman-claude Makefile Help$(CYAN)                       ║"
	@echo -e "║                    $(YELLOW)Automated Claude CLI Tool$(CYAN)                              ║"
	@echo -e "╚══════════════════════════════════════════════════════════════════════════════╝"
	@echo -e "$(RESET)"
	@echo -e "$(GREEN)📋 Main Categories:$(RESET)"
	@echo -e "  $(YELLOW)make help-build$(RESET)    🔨 Build and packaging"
	@echo -e "  $(YELLOW)make help-test$(RESET)     🧪 Testing, coverage, and validation"
	@echo -e "  $(YELLOW)make help-quality$(RESET)  ✨ Code quality, formatting, and linting"
	@echo -e "  $(YELLOW)make help-env$(RESET)      🌍 Environment setup and tool management"
	@echo -e "  $(YELLOW)make help-dev$(RESET)      🛠️  Development workflow and servers"
	@echo -e "  $(YELLOW)make help-ops$(RESET)      🔧 Operations and maintenance"
	@echo ""
	@echo -e "$(GREEN)🚀 Quick Commands:$(RESET)"
	@echo -e "  $(CYAN)make start$(RESET)         Start yesman"
	@echo -e "  $(CYAN)make stop$(RESET)          Stop yesman processes"
	@echo -e "  $(CYAN)make restart$(RESET)       Restart yesman"
	@echo -e "  $(CYAN)make status$(RESET)        Check yesman status"
	@echo -e "  $(CYAN)make quick$(RESET)         Quick check (lint-fast + test-unit)"
	@echo -e "  $(CYAN)make full$(RESET)          Full quality check (comprehensive)"
	@echo -e "  $(CYAN)make setup-all$(RESET)     Complete project setup"
	@echo ""
	@echo -e "$(GREEN)💡 Pro Tips:$(RESET)"
	@echo -e "  • Use $(YELLOW)'make quick'$(RESET) for fast development iteration"
	@echo -e "  • Use $(YELLOW)'make full'$(RESET) before committing changes"
	@echo -e "  • Use $(YELLOW)'make hooks-install'$(RESET) for automatic quality checks"
	@echo "  • All commands support tab completion if configured"
	@echo ""
	@echo -e "$(BLUE)📖 Documentation: $(RESET)https://github.com/yourusername/yesman-claude"

help-full: help help-build help-test help-quality help-env help-dev help-ops ## show all help sections

help-build: ## show build and packaging help
	@echo -e "$(GREEN)🔨 Build and Packaging Commands:$(RESET)"
	@echo -e "  $(CYAN)build$(RESET)              Build Python package"
	@echo -e "  $(CYAN)build-dashboard$(RESET)    Build SvelteKit dashboard"
	@echo -e "  $(CYAN)build-tauri$(RESET)        Build Tauri desktop app"
	@echo -e "  $(CYAN)build-all$(RESET)          Build complete project"
	@echo -e "  $(CYAN)install-dashboard-deps$(RESET) Install dashboard dependencies"
	@echo -e "  $(CYAN)build-info$(RESET)         Show build environment information"

help-test: ## show testing help
	@echo -e "$(GREEN)🧪 Testing and Validation Commands:$(RESET)"
	@echo -e "  $(CYAN)test$(RESET)               Run all tests with coverage"
	@echo -e "  $(CYAN)test-unit$(RESET)          Run only unit tests"
	@echo -e "  $(CYAN)test-integration$(RESET)   Run integration tests"
	@echo -e "  $(CYAN)test-e2e$(RESET)           Run end-to-end tests"
	@echo -e "  $(CYAN)test-all$(RESET)           Run all test suites"
	@echo -e "  $(CYAN)cover$(RESET)              Run tests with coverage report"
	@echo -e "  $(CYAN)cover-html$(RESET)         Generate HTML coverage report"
	@echo -e "  $(CYAN)test-watch$(RESET)         Run tests in watch mode"
	@echo -e "  $(CYAN)test-info$(RESET)          Show testing information and targets"

help-quality: ## show quality help
	@echo -e "$(GREEN)✨ Code Quality Commands:$(RESET)"
	@echo -e "  $(CYAN)fmt$(RESET)                Format code with black/isort"
	@echo -e "  $(CYAN)format-check$(RESET)       Check formatting without fixing"
	@echo -e "  $(CYAN)type-check$(RESET)         Run mypy type checking"
	@echo -e "  $(CYAN)security$(RESET)           Run security scans"
	@echo -e "  $(CYAN)analyze$(RESET)            Code complexity analysis"
	@echo -e "  $(CYAN)quality$(RESET)            Run standard quality checks"
	@echo -e "  $(CYAN)quality-strict$(RESET)     Run comprehensive checks"
	@echo -e "  $(CYAN)quality-info$(RESET)       Show quality tools info"


help-env: ## show environment and tool help
	@echo -e "$(GREEN)🌍 Environment Setup and Tool Management:$(RESET)"
	@echo -e "  $(CYAN)install$(RESET)            Install yesman-claude in development mode"
	@echo -e "  $(CYAN)install-dev$(RESET)        Install with dev dependencies"
	@echo -e "  $(CYAN)install-all$(RESET)        Install with all dependencies"
	@echo -e "  $(CYAN)install-tools$(RESET)      Install essential development tools"
	@echo -e "  $(CYAN)install-all-tools$(RESET)  Install all development tools"
	@echo -e "  $(CYAN)deps-install$(RESET)       Install project dependencies"
	@echo -e "  $(CYAN)deps-update$(RESET)        Update to compatible versions"
	@echo -e "  $(CYAN)deps-security$(RESET)      Security vulnerability scan"
	@echo -e "  $(CYAN)setup-all$(RESET)          Complete project setup"
	@echo -e "  $(CYAN)tools-status$(RESET)       Check tool installation status"
	@echo -e "  $(CYAN)venv-create$(RESET)        Create virtual environment"
	@echo -e "  $(CYAN)env-info$(RESET)           Show environment information"

help-dev: ## show development workflow help
	@echo -e "$(GREEN)🛠️  Development Workflow and Server Commands:$(RESET)"
	@echo -e "  $(CYAN)start$(RESET)              Start yesman services"
	@echo -e "  $(CYAN)stop$(RESET)               Stop all services"
	@echo -e "  $(CYAN)restart$(RESET)            Restart services"
	@echo -e "  $(CYAN)status$(RESET)             Check service status"
	@echo -e "  $(CYAN)dev-dashboard$(RESET)      Full development environment"
	@echo -e "  $(CYAN)run-web-dashboard$(RESET)  Run web dashboard"
	@echo -e "  $(CYAN)run-tauri-dev$(RESET)      Run Tauri in development mode"
	@echo -e "  $(CYAN)dev$(RESET)                Standard development workflow"
	@echo -e "  $(CYAN)quick$(RESET)              Quick check (lint + test)"
	@echo -e "  $(CYAN)full$(RESET)               Full quality check"
	@echo -e "  $(CYAN)verify$(RESET)             Complete verification before PR"
	@echo -e "  $(CYAN)debug-api$(RESET)          Debug API server"
	@echo -e "  $(CYAN)logs$(RESET)               Show service logs"
	@echo -e "  $(CYAN)commit-helper$(RESET)      Run commit organization helper"
	@echo -e "  $(CYAN)dev-info$(RESET)           Show development environment info"

help-ops: ## show operations help
	@echo -e "$(GREEN)🔧 Operations and Maintenance Commands:$(RESET)"
	@echo -e "  $(CYAN)clean$(RESET)              Clean build artifacts"
	@echo -e "  $(CYAN)clean-all$(RESET)          Clean everything"
	@echo -e "  $(CYAN)clean-deep$(RESET)         Deep clean including Docker"
	@echo -e "  $(CYAN)docker-build$(RESET)       Build Docker image"
	@echo -e "  $(CYAN)docker-run$(RESET)         Run Docker container"
	@echo -e "  $(CYAN)docker-status$(RESET)      Show Docker status"
	@echo -e "  $(CYAN)info$(RESET)               Project information"
	@echo -e "  $(CYAN)status$(RESET)             System status"
	@echo -e "  $(CYAN)maintenance$(RESET)        Routine maintenance"
	@echo -e "  $(CYAN)backup$(RESET)             Create backup"
	@echo -e "  $(CYAN)check-health$(RESET)       Health check"
	@echo -e "  $(CYAN)ops-info$(RESET)           Show operations information"

# ==============================================================================
# Project Information
# ==============================================================================

.PHONY: info version

info: ## show project information and current configuration
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
	@echo ""
	@echo -e "$(GREEN)🔧 Available Modules:$(RESET)"
	@echo -e "  • $(CYAN)Environment$(RESET)      (Makefile.env.mk)     - Setup and tool management"
	@echo -e "  • $(CYAN)Build & Package$(RESET)  (Makefile.build.mk)   - Build and packaging"
	@echo -e "  • $(CYAN)Testing$(RESET)          (Makefile.test.mk)    - Test suites and coverage"
	@echo -e "  • $(CYAN)Code Quality$(RESET)     (Makefile.quality.mk) - Formatting and analysis"
	@echo -e "  • $(CYAN)Development$(RESET)      (Makefile.dev.mk)     - Dev workflows and servers"
	@echo -e "  • $(CYAN)Operations$(RESET)       (Makefile.ops.mk)     - Operations and maintenance"


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