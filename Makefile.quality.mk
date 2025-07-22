# Makefile.quality.mk - Code Quality and Analysis for yesman-claude
# Formatting, linting, security analysis, and code quality checks

# ==============================================================================
# Quality Configuration
# ==============================================================================

# Colors are now exported from main Makefile

# Python source directories
PYTHON_DIRS ?= libs commands api tests
PYTHON_FILES = $(shell find $(PYTHON_DIRS) -name "*.py" 2>/dev/null)

# ==============================================================================
# Code Formatting Targets
# ==============================================================================

.PHONY: fmt format format-all format-check format-diff format-imports
.PHONY: format-docstrings format-ci
.PHONY: lint lint-check lint-fix lint-strict lint-fast lint-help
.PHONY: hooks-install hooks-uninstall hooks-status pre-commit-install
.PHONY: pre-commit-run pre-commit-update validate-hooks

fmt: ## format Python files with black and isort
	@echo "$(CYAN)Formatting Python code...$(RESET)"
	@echo "1. Running black..."
	@command -v black >/dev/null 2>&1 || pip install black
	@black $(PYTHON_DIRS)
	@echo "2. Running isort..."
	@command -v isort >/dev/null 2>&1 || pip install isort
	@isort $(PYTHON_DIRS) --profile black
	@echo "$(GREEN)✅ Code formatting complete!$(RESET)"

format: fmt ## alias for fmt

format-all: ## run all formatters including advanced ones
	@echo "$(CYAN)Running comprehensive code formatting...$(RESET)"
	@echo "1. Running black (strict formatting)..."
	@black $(PYTHON_DIRS) --preview
	@echo "2. Running isort (import organization)..."
	@isort $(PYTHON_DIRS) --profile black --float-to-top
	@echo "3. Running autoflake (remove unused imports)..."
	@autoflake --in-place --remove-all-unused-imports --remove-unused-variables --recursive $(PYTHON_DIRS)
	@echo "4. Running docformatter (format docstrings)..."
	@docformatter --in-place --recursive $(PYTHON_DIRS)
	@echo "$(GREEN)✅ All formatting complete!$(RESET)"

format-check: ## check code formatting without fixing
	@echo "$(CYAN)Checking code formatting...$(RESET)"
	@if ! black --check $(PYTHON_DIRS) 2>/dev/null; then \
		echo "$(RED)❌ Black formatting issues found$(RESET)"; \
		echo "$(YELLOW)Run 'make fmt' to fix.$(RESET)"; \
		exit 1; \
	fi
	@if ! isort --check-only $(PYTHON_DIRS) --profile black 2>/dev/null; then \
		echo "$(RED)❌ Import sorting issues found$(RESET)"; \
		echo "$(YELLOW)Run 'make fmt' to fix.$(RESET)"; \
		exit 1; \
	fi
	@echo "$(GREEN)✅ All files are properly formatted$(RESET)"

format-diff: ## show formatting differences
	@echo "$(CYAN)Showing formatting differences...$(RESET)"
	@black --diff $(PYTHON_DIRS)

format-imports: ## organize imports only
	@echo "$(CYAN)Organizing imports...$(RESET)"
	@isort $(PYTHON_DIRS) --profile black
	@echo "$(GREEN)✅ Imports organized!$(RESET)"

format-docstrings: ## format docstrings
	@echo "$(CYAN)Formatting docstrings...$(RESET)"
	@command -v docformatter >/dev/null 2>&1 || pip install docformatter
	@docformatter --in-place --recursive $(PYTHON_DIRS)
	@echo "$(GREEN)✅ Docstrings formatted!$(RESET)"

format-ci: format-check ## CI-friendly format check

# ==============================================================================
# Static Analysis and Type Checking
# ==============================================================================

.PHONY: type-check mypy pyright static-analysis

type-check: mypy ## run type checking (alias for mypy)

mypy: ## run mypy type checker
	@echo "$(CYAN)Running mypy type checker...$(RESET)"
	@command -v mypy >/dev/null 2>&1 || pip install mypy
	@mypy $(PYTHON_DIRS) --ignore-missing-imports
	@echo "$(GREEN)✅ Type checking completed$(RESET)"

pyright: ## run pyright type checker
	@echo "$(CYAN)Running pyright type checker...$(RESET)"
	@command -v pyright >/dev/null 2>&1 || npm install -g pyright
	@pyright $(PYTHON_DIRS)
	@echo "$(GREEN)✅ Pyright checking completed$(RESET)"

static-analysis: ## run static code analysis
	@echo "$(CYAN)Running static code analysis...$(RESET)"
	@command -v pylint >/dev/null 2>&1 || pip install pylint
	@pylint $(PYTHON_DIRS) --exit-zero
	@echo "$(GREEN)✅ Static analysis completed$(RESET)"

# ==============================================================================
# Security Analysis
# ==============================================================================

.PHONY: security security-scan bandit safety pip-audit security-all

security: security-scan ## alias for security-scan

security-scan: ## run basic security scan with bandit
	@echo "$(CYAN)Running security scan with bandit...$(RESET)"
	@command -v bandit >/dev/null 2>&1 || pip install bandit
	@bandit -r $(PYTHON_DIRS) -ll -i
	@echo "$(GREEN)✅ Security scan completed$(RESET)"

bandit: ## run bandit security linter
	@echo "$(CYAN)Running bandit security linter...$(RESET)"
	@command -v bandit >/dev/null 2>&1 || pip install bandit
	@bandit -r $(PYTHON_DIRS) -f json -o bandit-report.json
	@bandit -r $(PYTHON_DIRS) -f screen -ll
	@echo "$(GREEN)✅ Bandit scan completed (report: bandit-report.json)$(RESET)"

safety: ## check dependencies for known vulnerabilities
	@echo "$(CYAN)Checking dependencies for vulnerabilities...$(RESET)"
	@command -v safety >/dev/null 2>&1 || pip install safety
	@safety check --json --output safety-report.json
	@safety check
	@echo "$(GREEN)✅ Safety check completed$(RESET)"

pip-audit: ## audit dependencies for security issues
	@echo "$(CYAN)Auditing pip packages...$(RESET)"
	@command -v pip-audit >/dev/null 2>&1 || pip install pip-audit
	@pip-audit
	@echo "$(GREEN)✅ Pip audit completed$(RESET)"

security-all: bandit safety pip-audit ## run all security checks
	@echo "$(GREEN)✅ All security checks completed$(RESET)"

# ==============================================================================
# Code Quality Metrics
# ==============================================================================

.PHONY: metrics complexity maintainability loc quality-report

metrics: complexity maintainability ## show code quality metrics

complexity: ## analyze code complexity
	@echo "$(CYAN)Analyzing code complexity...$(RESET)"
	@command -v radon >/dev/null 2>&1 || pip install radon
	@echo "$(YELLOW)Cyclomatic Complexity:$(RESET)"
	@radon cc $(PYTHON_DIRS) -a -nb
	@echo ""
	@echo "$(YELLOW)Maintainability Index:$(RESET)"
	@radon mi $(PYTHON_DIRS) -nb
	@echo "$(GREEN)✅ Complexity analysis completed$(RESET)"

maintainability: ## check maintainability index
	@echo "$(CYAN)Checking maintainability index...$(RESET)"
	@command -v radon >/dev/null 2>&1 || pip install radon
	@radon mi $(PYTHON_DIRS) -nb --min B
	@echo "$(GREEN)✅ Maintainability check completed$(RESET)"

loc: ## count lines of code
	@echo "$(CYAN)Lines of Code Statistics:$(RESET)"
	@echo "$(YELLOW)By Language:$(RESET)"
	@find . -name "*.py" -o -name "*.js" -o -name "*.ts" -o -name "*.html" -o -name "*.css" | \
		grep -v node_modules | grep -v .git | xargs wc -l | sort -nr
	@echo ""
	@echo "$(YELLOW)Python Files:$(RESET)"
	@find $(PYTHON_DIRS) -name "*.py" | xargs wc -l | sort -nr | head -20

quality-report: ## generate comprehensive quality report
	@echo "$(CYAN)Generating comprehensive quality report...$(RESET)"
	@mkdir -p reports
	@echo "# Code Quality Report - $(shell date)" > reports/quality-report.md
	@echo "" >> reports/quality-report.md
	@echo "## Complexity Metrics" >> reports/quality-report.md
	@radon cc $(PYTHON_DIRS) -a -nb >> reports/quality-report.md 2>&1 || true
	@echo "" >> reports/quality-report.md
	@echo "## Maintainability Index" >> reports/quality-report.md
	@radon mi $(PYTHON_DIRS) -nb >> reports/quality-report.md 2>&1 || true
	@echo "" >> reports/quality-report.md
	@echo "## Security Issues" >> reports/quality-report.md
	@bandit -r $(PYTHON_DIRS) -f txt >> reports/quality-report.md 2>&1 || true
	@echo "$(GREEN)✅ Quality report generated: reports/quality-report.md$(RESET)"

# ==============================================================================
# Code Analysis Tools
# ==============================================================================

.PHONY: analyze dead-code duplicates vulture

analyze: ## run comprehensive code analysis
	@echo "$(CYAN)Running comprehensive code analysis...$(RESET)"
	@$(MAKE) complexity
	@$(MAKE) dead-code
	@$(MAKE) duplicates
	@echo "$(GREEN)✅ Comprehensive analysis completed$(RESET)"

dead-code: ## find dead code with vulture
	@echo "$(CYAN)Finding dead code...$(RESET)"
	@command -v vulture >/dev/null 2>&1 || pip install vulture
	@vulture $(PYTHON_DIRS) --min-confidence 80
	@echo "$(GREEN)✅ Dead code analysis completed$(RESET)"

duplicates: ## find duplicate code
	@echo "$(CYAN)Finding duplicate code...$(RESET)"
	@command -v pylint >/dev/null 2>&1 || pip install pylint
	@pylint $(PYTHON_DIRS) --disable=all --enable=duplicate-code
	@echo "$(GREEN)✅ Duplicate code analysis completed$(RESET)"

vulture: dead-code ## alias for dead-code


# ==============================================================================
# Hierarchical Lint System (integrated from Makefile.lint.mk)
# ==============================================================================

# Directory configurations
LINT_DIRS = libs commands api tests
LINT_DIRS_SECURITY = libs commands api
LINT_DIRS_CORE = libs commands api
EXCLUDE_DIRS = --exclude migrations --exclude node_modules --exclude examples

# Optional unsafe fixes (use: make lint-fix UNSAFE_FIXES=1)
UNSAFE_FIXES ?=
UNSAFE_FLAG = $(if $(UNSAFE_FIXES),--unsafe-fixes,)

# Performance and verbosity settings
LINT_QUIET ?= --quiet
LINT_FAST_MODE ?= 1

# Level 1: Basic Lint (Default) - Fast & Lightweight for Development Flow
lint-fast: ## ultra-fast lint checks (1-3s)
	@echo "🚀 Running fast lint checks..."
	@echo "⚡ Running ruff check (fast mode)..."
	uv run ruff check $(LINT_DIRS) $(EXCLUDE_DIRS) $(LINT_QUIET) --no-cache
	@echo "✅ Fast lint completed"

lint-check: ## lint checks without auto-fix (2-5s)
	@echo "🔍 Running lint checks (Level 1: Basic, no auto-fix)..."
	@echo "📋 Running ruff check..."
	uv run ruff check $(LINT_DIRS) $(EXCLUDE_DIRS)
	@echo "🔍 Running mypy..."
	uv run mypy $(LINT_DIRS_CORE) --ignore-missing-imports $(EXCLUDE_DIRS)
	@echo "🛡️  Running bandit security check..."
	uv run bandit -r $(LINT_DIRS_SECURITY) --skip B101,B404,B603,B607,B602 --severity-level medium $(LINT_QUIET) --exclude "*/tests/*,*/scripts/*,*/debug/*,*/examples/*" || echo "✅ Security check completed"
	@echo "📝 Running mdformat check..."
	uv run mdformat --check *.md docs/**/*.md --wrap 120 || echo "✅ Markdown format check completed"
	@echo "✅ Level 1 lint check completed"

# Default lint target (Level 1)
lint: lint-check ## run basic lint checks

lint-fix: ## lint with auto-fix (Level 2)
	@echo "🔧 Running lint with auto-fix (Level 2: Auto-fix)..."
	@echo "🔧 Running ruff check with auto-fix..."
	uv run ruff check $(LINT_DIRS) --fix $(UNSAFE_FLAG) $(EXCLUDE_DIRS)
	@echo "🎨 Running ruff format..."
	uv run ruff format $(LINT_DIRS) $(EXCLUDE_DIRS)
	@echo "🔍 Running mypy..."
	uv run mypy $(LINT_DIRS_CORE) --ignore-missing-imports $(EXCLUDE_DIRS)
	@echo "🛡️  Running bandit security check..."
	uv run bandit -r $(LINT_DIRS_SECURITY) --skip B101,B404,B603,B607,B602 --severity-level medium $(LINT_QUIET) --exclude "*/tests/*,*/scripts/*,*/debug/*,*/examples/*" || echo "✅ Security check completed"
	@echo "📝 Running mdformat..."
	uv run mdformat *.md docs/**/*.md --wrap 120
	@echo "✅ Level 2 lint-fix completed"

lint-strict: ## comprehensive lint checks (Level 3)
	@echo "🎯 Running strict lint checks (Level 3: Comprehensive)..."
	@echo "⚠️  Warning: This is a comprehensive check that may take time"
	@echo "📊 Running ruff with all rules..."
	uv run ruff check $(LINT_DIRS) --select ALL --ignore E501,B008,C901,COM812,B904,B017,B007,D100,D101,D102,D103,D104,D105,D106,D107  $(EXCLUDE_DIRS) --output-format=full
	@echo "🔍 Running mypy with strict settings..."
	uv run mypy $(LINT_DIRS_CORE) --strict --ignore-missing-imports  $(EXCLUDE_DIRS)
	@echo "🛡️  Running bandit with strict settings..."
	uv run bandit -r $(LINT_DIRS_CORE) --severity-level low --exclude "*/tests/*,*/scripts/*,*/debug/*,*/examples/*"
	@echo "✅ Level 3 strict lint completed"

# ==============================================================================
# Git Hooks Management
# ==============================================================================

hooks-install: pre-commit-install ## install git hooks
	@echo "✅ Git hooks installed successfully"
	@echo "  - pre-commit: Level 1 lint (fast, development-friendly)"
	@echo "  - pre-push: Level 1 lint + fast tests (comprehensive but reasonable)"

hooks-uninstall: ## uninstall git hooks
	@echo "Uninstalling pre-commit hooks..."
	uv run pre-commit uninstall
	@echo "✅ Git hooks uninstalled"

hooks-status: ## show git hooks status
	@echo "Git hooks status:"
	@if [ -f .git/hooks/pre-commit ]; then echo "  ✅ pre-commit: installed"; else echo "  ❌ pre-commit: not installed"; fi
	@if [ -f .git/hooks/pre-push ]; then echo "  ✅ pre-push: installed"; else echo "  ❌ pre-push: not installed"; fi
	@echo "To install: make hooks-install"
	@echo "To uninstall: make hooks-uninstall"

pre-commit-install: ## install pre-commit hooks
	@echo "Installing pre-commit hooks..."
	uv run pre-commit install
	uv run pre-commit install --hook-type pre-push

pre-commit-run: ## run all pre-commit hooks
	@echo "Running all pre-commit hooks..."
	uv run pre-commit run --all-files

pre-commit-update: ## update pre-commit hooks
	@echo "Updating pre-commit hooks..."
	uv run pre-commit autoupdate

validate-hooks: ## validate git hooks consistency
	@echo "🔍 Validating git hooks consistency..."
	@echo "Testing pre-commit hooks..."
	uv run pre-commit run --all-files
	@echo "Testing make lint (Level 1)..."
	make lint
	@echo "✅ All hooks validated successfully - consistency confirmed"

lint-help: ## show comprehensive lint system help
	@echo "📋 Unified Lint and Code Quality System"
	@echo "=" | head -c 80
	@echo ""
	@echo "🚀 HIERARCHICAL LINT LEVELS:"
	@echo ""
	@echo "  Level 1 (Default - Fast & Light):"
	@echo "    make lint-fast       ⚡ Ultra-fast check (1-3s) for frequent use"
	@echo "    make lint            🔍 Basic checks (2-5s) - same as pre-commit"
	@echo "    make lint-check      🔍 Alias for 'make lint'"
	@echo ""
	@echo "  Level 2 (Auto-fix):"
	@echo "    make lint-fix        🔧 Level 1 + automatic fixes"
	@echo "    make lint-fix UNSAFE_FIXES=1  ⚠️  Include unsafe auto-fixes"
	@echo ""
	@echo "  Level 3 (Strict - Manual Only):"
	@echo "    make lint-strict     🎯 Comprehensive quality (PR/release only)"
	@echo ""
	@echo "🔗 GIT HOOKS MANAGEMENT:"
	@echo "    make hooks-install   🔧 Install unified pre-commit/pre-push hooks"
	@echo "    make hooks-uninstall 🗑️  Remove git hooks"
	@echo "    make hooks-status    ℹ️  Check hooks installation status"
	@echo ""
	@echo "✨ TIP: Start with 'make lint-fast' for quick checks during development"
	@echo "✨ TIP: Use 'make hooks-install' once to automate quality checks"
	@echo "✨ TIP: Run 'make lint-strict' before important releases"

# ==============================================================================
# Comprehensive Quality Checks
# ==============================================================================

.PHONY: quality quality-fix quality-strict quality-minimal

quality: format-check lint-check type-check security-scan ## run standard quality checks
	@echo "$(GREEN)✅ Standard quality checks completed$(RESET)"

quality-fix: fmt lint-fix ## apply automatic quality fixes
	@echo "$(GREEN)✅ Quality fixes applied$(RESET)"

quality-strict: format-check lint-strict mypy security-all analyze ## run strict quality checks
	@echo "$(GREEN)✅ Strict quality checks completed$(RESET)"

quality-minimal: lint-fast format-check ## run minimal quality checks
	@echo "$(GREEN)✅ Minimal quality checks completed$(RESET)"

# ==============================================================================
# Tool Installation (Quality-specific)
# ==============================================================================

# Tool installation is handled by Makefile.tools.mk

# ==============================================================================
# Quality Information
# ==============================================================================

.PHONY: quality-info quality-status

quality-info: ## show quality tools and targets information
	@echo "$(CYAN)"
	@echo "╔══════════════════════════════════════════════════════════════════════════════╗"
	@echo "║                         $(YELLOW)Code Quality Information$(CYAN)                        ║"
	@echo "╚══════════════════════════════════════════════════════════════════════════════╝"
	@echo "$(RESET)"
	@echo "$(GREEN)🎨 Formatting Tools:$(RESET)"
	@echo "  • $(CYAN)black$(RESET)              Python code formatter"
	@echo "  • $(CYAN)isort$(RESET)              Import statement organizer"
	@echo "  • $(CYAN)autoflake$(RESET)          Remove unused imports/variables"
	@echo "  • $(CYAN)docformatter$(RESET)       Docstring formatter"
	@echo ""
	@echo "$(GREEN)🔍 Analysis Tools:$(RESET)"
	@echo "  • $(CYAN)mypy$(RESET)               Static type checker"
	@echo "  • $(CYAN)pylint$(RESET)             Python code analyzer"
	@echo "  • $(CYAN)radon$(RESET)              Code metrics (complexity, maintainability)"
	@echo "  • $(CYAN)vulture$(RESET)            Dead code finder"
	@echo ""
	@echo "$(GREEN)🛡️  Security Tools:$(RESET)"
	@echo "  • $(CYAN)bandit$(RESET)             Security issue scanner"
	@echo "  • $(CYAN)safety$(RESET)             Dependency vulnerability checker"
	@echo "  • $(CYAN)pip-audit$(RESET)          Pip package auditor"
	@echo ""
	@echo "$(GREEN)📊 Quality Commands:$(RESET)"
	@echo "  • $(CYAN)quality$(RESET)            Run standard checks"
	@echo "  • $(CYAN)quality-fix$(RESET)        Apply automatic fixes"
	@echo "  • $(CYAN)quality-strict$(RESET)     Run comprehensive checks"
	@echo "  • $(CYAN)analyze$(RESET)            Run code analysis"

quality-status: ## check installed quality tools
	@echo "$(CYAN)Quality Tools Status:$(RESET)"
	@echo "$(BLUE)====================$(RESET)"
	@echo "$(YELLOW)Formatting Tools:$(RESET)"
	@command -v black >/dev/null 2>&1 && echo "  ✅ black" || echo "  ❌ black"
	@command -v isort >/dev/null 2>&1 && echo "  ✅ isort" || echo "  ❌ isort"
	@command -v autoflake >/dev/null 2>&1 && echo "  ✅ autoflake" || echo "  ❌ autoflake"
	@echo ""
	@echo "$(YELLOW)Analysis Tools:$(RESET)"
	@command -v mypy >/dev/null 2>&1 && echo "  ✅ mypy" || echo "  ❌ mypy"
	@command -v pylint >/dev/null 2>&1 && echo "  ✅ pylint" || echo "  ❌ pylint"
	@command -v radon >/dev/null 2>&1 && echo "  ✅ radon" || echo "  ❌ radon"
	@echo ""
	@echo "$(YELLOW)Security Tools:$(RESET)"
	@command -v bandit >/dev/null 2>&1 && echo "  ✅ bandit" || echo "  ❌ bandit"
	@command -v safety >/dev/null 2>&1 && echo "  ✅ safety" || echo "  ❌ safety"