# Makefile.build.mk - Build and Packaging for yesman-claude
# Pure build operations for Python packages and frontend components

# ==============================================================================
# Build Configuration
# ==============================================================================

# Colors are now exported from main Makefile

# ==============================================================================
# Build Targets
# ==============================================================================

.PHONY: build build-dashboard build-tauri build-all build-info

build: ## build Python package
	@echo -e "$(CYAN)Building $(PROJECT_NAME) package...$(RESET)"
	python -m build
	@echo -e "$(GREEN)✅ Package built successfully$(RESET)"

# ==============================================================================
# Dashboard Build Targets
# ==============================================================================

.PHONY: build-dashboard build-tauri install-dashboard-deps

build-dashboard: ## build SvelteKit dashboard
	@echo -e "$(CYAN)Building SvelteKit dashboard...$(RESET)"
	@if [ -d "tauri-dashboard" ]; then \
		cd tauri-dashboard && npm run build; \
		echo "$(GREEN)✅ Dashboard built successfully$(RESET)"; \
	else \
		echo "$(YELLOW)⚠️  Dashboard directory not found$(RESET)"; \
	fi

build-tauri: ## build Tauri for production
	@echo -e "$(CYAN)Building Tauri for production...$(RESET)"
	@if [ -d "tauri-dashboard" ]; then \
		cd tauri-dashboard && npm run tauri build; \
		echo "$(GREEN)✅ Tauri app built successfully$(RESET)"; \
	else \
		echo "$(YELLOW)⚠️  Dashboard directory not found$(RESET)"; \
	fi

install-dashboard-deps: ## install dashboard dependencies
	@echo -e "$(CYAN)Installing dashboard dependencies...$(RESET)"
	@if [ -d "tauri-dashboard" ]; then \
		cd tauri-dashboard && npm install; \
		echo "$(GREEN)✅ Dashboard dependencies installed$(RESET)"; \
	else \
		echo "$(YELLOW)⚠️  Dashboard directory not found$(RESET)"; \
	fi

build-all: build build-dashboard ## build complete project
	@echo -e "$(GREEN)✅ Complete project built successfully$(RESET)"


# ==============================================================================
# Build Information
# ==============================================================================

build-info: ## show build information and targets
	@echo -e "$(CYAN)"
	@echo "╔══════════════════════════════════════════════════════════════════════════════╗"
	@echo "║                         $(YELLOW)Build Information$(CYAN)                              ║"
	@echo "╚══════════════════════════════════════════════════════════════════════════════╝"
	@echo "$(RESET)"
	@echo -e "$(GREEN)📋 Build Details:$(RESET)"
	@echo "  Project:        $(YELLOW)$(PROJECT_NAME)$(RESET)"
	@echo "  Version:        $(YELLOW)$(VERSION)$(RESET)"
	@echo "  Python:         $$(python --version 2>&1)"
	@echo "  UV:            $$(uv --version 2>&1 || echo 'Not installed')"
	@echo ""
	@echo -e "$(GREEN)🎯 Build Targets:$(RESET)"
	@echo "  • $(CYAN)build$(RESET)               Build Python package"
	@echo "  • $(CYAN)build-dashboard$(RESET)     Build SvelteKit dashboard"
	@echo "  • $(CYAN)build-tauri$(RESET)         Build Tauri desktop app"
	@echo "  • $(CYAN)build-all$(RESET)           Build complete project"
	@echo "  • $(CYAN)install-dashboard-deps$(RESET) Install dashboard dependencies"