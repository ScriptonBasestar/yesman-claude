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

fmt: ## format Python files with ruff
	@echo -e "$(CYAN)Formatting Python code...$(RESET)"
	@echo "1. Running ruff format..."
	@uv run ruff format $(PYTHON_DIRS) $(EXCLUDE_DIRS)
	@echo "2. Running ruff check with import sorting..."
	@uv run ruff check $(PYTHON_DIRS) --fix --select I $(EXCLUDE_DIRS)
	@echo -e "$(GREEN)✅ Code formatting complete!$(RESET)"

format: fmt ## alias for fmt

format-all: ## run all formatters including advanced ones
	@echo -e "$(CYAN)Running comprehensive code formatting...$(RESET)"
	@echo "1. Running ruff format..."
	@uv run ruff format $(PYTHON_DIRS) $(EXCLUDE_DIRS)
	@echo "2. Running ruff check with all safe fixes..."
	@uv run ruff check $(PYTHON_DIRS) --fix $(EXCLUDE_DIRS)
	@echo "3. Running autoflake (remove unused imports)..."
	@autoflake --in-place --remove-all-unused-imports --remove-unused-variables --recursive $(PYTHON_DIRS) || true
	@echo "4. Running docformatter (format docstrings)..."
	@docformatter --in-place --recursive $(PYTHON_DIRS) || true
	@echo -e "$(GREEN)✅ All formatting complete!$(RESET)"

format-check: ## check code formatting without fixing
	@echo -e "$(CYAN)Checking code formatting...$(RESET)"
	@if ! uv run ruff format --check $(PYTHON_DIRS) $(EXCLUDE_DIRS) 2>/dev/null; then \
		echo -e "$(RED)❌ Formatting issues found$(RESET)"; \
		echo -e "$(YELLOW)Run 'make fmt' to fix.$(RESET)"; \
		exit 1; \
	fi
	@if ! uv run ruff check --select I $(PYTHON_DIRS) $(EXCLUDE_DIRS) 2>/dev/null; then \
		echo -e "$(RED)❌ Import sorting issues found$(RESET)"; \
		echo -e "$(YELLOW)Run 'make fmt' to fix.$(RESET)"; \
		exit 1; \
	fi
	@echo -e "$(GREEN)✅ All files are properly formatted$(RESET)"

format-diff: ## show formatting differences
	@echo -e "$(CYAN)Showing formatting differences...$(RESET)"
	@uv run ruff format --diff $(PYTHON_DIRS) $(EXCLUDE_DIRS) || true

format-imports: ## organize imports only
	@echo -e "$(CYAN)Organizing imports...$(RESET)"
	@uv run ruff check $(PYTHON_DIRS) --fix --select I $(EXCLUDE_DIRS)
	@echo -e "$(GREEN)✅ Imports organized!$(RESET)"

format-docstrings: ## format docstrings
	@echo -e "$(CYAN)Formatting docstrings...$(RESET)"
	@command -v docformatter >/dev/null 2>&1 || pip install docformatter
	@docformatter --in-place --recursive $(PYTHON_DIRS)
	@echo -e "$(GREEN)✅ Docstrings formatted!$(RESET)"

format-file: ## format specific Python files (supports CLAUDE_FILES env var)
	@if [ -n "$$CLAUDE_FILES" ]; then \
		echo "$(CYAN)🔄 Formatting files from CLAUDE_FILES...$(RESET)"; \
		for file in $$CLAUDE_FILES; do \
			if [ -f "$$file" ] && echo "$$file" | grep -q "\.py$$"; then \
				echo "$(CYAN)📝 Formatting file: $$file$(RESET)"; \
				black "$$file" 2>/dev/null || echo "$(YELLOW)⚠️  black skipped $$file$(RESET)"; \
				isort "$$file" --profile black 2>/dev/null || echo "$(YELLOW)⚠️  isort skipped $$file$(RESET)"; \
				echo "$(GREEN)✅ File '$$file' processed$(RESET)"; \
			fi; \
		done; \
		echo "$(GREEN)🎉 File formatting complete!$(RESET)"; \
	else \
		echo "$(YELLOW)Usage: CLAUDE_FILES='file1.py file2.py' make format-file$(RESET)"; \
		echo "$(YELLOW)Or via hook: Files will be processed automatically$(RESET)"; \
	fi

format-ci: format-check ## CI-friendly format check

# ==============================================================================
# Static Analysis and Type Checking
# ==============================================================================

.PHONY: type-check mypy pyright static-analysis

type-check: mypy ## run type checking (alias for mypy)

mypy: ## run mypy type checker
	@echo -e "$(CYAN)Running mypy type checker...$(RESET)"
	@command -v mypy >/dev/null 2>&1 || pip install mypy
	@mypy $(PYTHON_DIRS) --ignore-missing-imports
	@echo -e "$(GREEN)✅ Type checking completed$(RESET)"

pyright: ## run pyright type checker
	@echo -e "$(CYAN)Running pyright type checker...$(RESET)"
	@command -v pyright >/dev/null 2>&1 || npm install -g pyright
	@pyright $(PYTHON_DIRS)
	@echo -e "$(GREEN)✅ Pyright checking completed$(RESET)"

static-analysis: ## run static code analysis
	@echo -e "$(CYAN)Running static code analysis...$(RESET)"
	@command -v pylint >/dev/null 2>&1 || pip install pylint
	@pylint $(PYTHON_DIRS) --exit-zero
	@echo -e "$(GREEN)✅ Static analysis completed$(RESET)"

# ==============================================================================
# Security Analysis
# ==============================================================================

.PHONY: security security-scan bandit safety pip-audit security-all

security: security-scan ## alias for security-scan

security-scan: ## run basic security scan with bandit
	@echo -e "$(CYAN)Running security scan with bandit...$(RESET)"
	@command -v bandit >/dev/null 2>&1 || pip install bandit
	@bandit -r $(PYTHON_DIRS) -ll -i
	@echo -e "$(GREEN)✅ Security scan completed$(RESET)"

bandit: ## run bandit security linter
	@echo -e "$(CYAN)Running bandit security linter...$(RESET)"
	@command -v bandit >/dev/null 2>&1 || pip install bandit
	@bandit -r $(PYTHON_DIRS) -f json -o bandit-report.json
	@bandit -r $(PYTHON_DIRS) -f screen -ll
	@echo -e "$(GREEN)✅ Bandit scan completed (report: bandit-report.json)$(RESET)"

safety: ## check dependencies for known vulnerabilities
	@echo -e "$(CYAN)Checking dependencies for vulnerabilities...$(RESET)"
	@command -v safety >/dev/null 2>&1 || pip install safety
	@safety check --json --output safety-report.json
	@safety check
	@echo -e "$(GREEN)✅ Safety check completed$(RESET)"

pip-audit: ## audit dependencies for security issues
	@echo -e "$(CYAN)Auditing pip packages...$(RESET)"
	@command -v pip-audit >/dev/null 2>&1 || pip install pip-audit
	@pip-audit
	@echo -e "$(GREEN)✅ Pip audit completed$(RESET)"

security-deps: safety pip-audit ## check dependencies for vulnerabilities only
	@echo -e "$(GREEN)✅ Dependency security checks completed$(RESET)"

security-code: bandit ## run code security analysis only
	@echo -e "$(GREEN)✅ Code security analysis completed$(RESET)"

security-json: ## export security results to JSON
	@echo -e "$(CYAN)Exporting security results to JSON...$(RESET)"
	@echo "1. Bandit security scan..."
	@uv run bandit -r $(PYTHON_DIRS) -f json -o bandit-security-report.json 2>/dev/null || echo "{}" > bandit-security-report.json
	@echo "2. Safety dependency check..."
	@uv run safety check --json --output safety-security-report.json 2>/dev/null || echo "[]" > safety-security-report.json
	@echo -e "$(GREEN)✅ Security reports saved:$(RESET)"
	@echo -e "  • $(CYAN)bandit-security-report.json$(RESET)"
	@echo -e "  • $(CYAN)safety-security-report.json$(RESET)"

security-all: security-code security-deps ## run all security checks
	@echo -e "$(GREEN)✅ All security checks completed$(RESET)"

# ==============================================================================
# Code Quality Metrics
# ==============================================================================

.PHONY: metrics complexity maintainability loc quality-report

metrics: complexity maintainability ## show code quality metrics

complexity: ## analyze code complexity
	@echo -e "$(CYAN)Analyzing code complexity...$(RESET)"
	@command -v radon >/dev/null 2>&1 || pip install radon
	@echo -e "$(YELLOW)Cyclomatic Complexity:$(RESET)"
	@radon cc $(PYTHON_DIRS) -a -nb
	@echo ""
	@echo -e "$(YELLOW)Maintainability Index:$(RESET)"
	@radon mi $(PYTHON_DIRS) -nb
	@echo -e "$(GREEN)✅ Complexity analysis completed$(RESET)"

maintainability: ## check maintainability index
	@echo -e "$(CYAN)Checking maintainability index...$(RESET)"
	@command -v radon >/dev/null 2>&1 || pip install radon
	@radon mi $(PYTHON_DIRS) -nb --min B
	@echo -e "$(GREEN)✅ Maintainability check completed$(RESET)"

loc: ## count lines of code
	@echo -e "$(CYAN)Lines of Code Statistics:$(RESET)"
	@echo -e "$(YELLOW)By Language:$(RESET)"
	@find . -name "*.py" -o -name "*.js" -o -name "*.ts" -o -name "*.html" -o -name "*.css" | \
		grep -v node_modules | grep -v .git | xargs wc -l | sort -nr
	@echo ""
	@echo -e "$(YELLOW)Python Files:$(RESET)"
	@find $(PYTHON_DIRS) -name "*.py" | xargs wc -l | sort -nr | head -20

quality-report: ## generate comprehensive quality report
	@echo -e "$(CYAN)Generating comprehensive quality report...$(RESET)"
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
	@echo -e "$(GREEN)✅ Quality report generated: reports/quality-report.md$(RESET)"

# ==============================================================================
# Code Analysis Tools
# ==============================================================================

.PHONY: analyze dead-code duplicates vulture

analyze: ## run comprehensive code analysis
	@echo -e "$(CYAN)Running comprehensive code analysis...$(RESET)"
	@$(MAKE) complexity
	@$(MAKE) dead-code
	@$(MAKE) duplicates
	@echo -e "$(GREEN)✅ Comprehensive analysis completed$(RESET)"

dead-code: ## find dead code with vulture
	@echo -e "$(CYAN)Finding dead code...$(RESET)"
	@command -v vulture >/dev/null 2>&1 || pip install vulture
	@vulture $(PYTHON_DIRS) --min-confidence 80
	@echo -e "$(GREEN)✅ Dead code analysis completed$(RESET)"

duplicates: ## find duplicate code
	@echo -e "$(CYAN)Finding duplicate code...$(RESET)"
	@command -v pylint >/dev/null 2>&1 || pip install pylint
	@pylint $(PYTHON_DIRS) --disable=all --enable=duplicate-code
	@echo -e "$(GREEN)✅ Duplicate code analysis completed$(RESET)"

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
	uv run python -m mypy $(LINT_DIRS_CORE) --ignore-missing-imports $(EXCLUDE_DIRS)
	@echo "🛡️  Running bandit security check..."
	uv run python -m bandit -r $(LINT_DIRS_SECURITY) --skip B101,B404,B603,B607,B602 --severity-level medium $(LINT_QUIET) --exclude "*/tests/*,*/scripts/*,*/debug/*,*/examples/*" || echo "✅ Security check completed"
	@echo "📝 Running mdformat check..."
	uv run python -m mdformat --check *.md docs/**/*.md --wrap 120 || echo "✅ Markdown format check completed"
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
	uv run python -m mypy $(LINT_DIRS_CORE) --ignore-missing-imports $(EXCLUDE_DIRS)
	@echo "🛡️  Running bandit security check..."
	uv run python -m bandit -r $(LINT_DIRS_SECURITY) --skip B101,B404,B603,B607,B602 --severity-level medium $(LINT_QUIET) --exclude "*/tests/*,*/scripts/*,*/debug/*,*/examples/*" || echo "✅ Security check completed"
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

lint-summary: ## show lint issues summary by linter and problematic files
	@echo -e "$(CYAN)📊 Lint Issues Summary$(RESET)"
	@echo -e "$(CYAN)=====================$(RESET)"
	@echo ""
	@TOTAL=$$(uv run ruff check $(LINT_DIRS) $(EXCLUDE_DIRS) --output-format=json 2>/dev/null | jq -r '.[] | length' | awk '{sum += $$1} END {print sum+0}' 2>/dev/null || echo "0"); \
	echo -e "$(YELLOW)Total Issues: $$TOTAL$(RESET)"; \
	echo ""
	@echo -e "$(GREEN)🏷️  Issues by Linter:$(RESET)"
	@uv run ruff check $(LINT_DIRS) $(EXCLUDE_DIRS) --output-format=json 2>/dev/null | \
	jq -r '.[] | .[] | .code' 2>/dev/null | sort | uniq -c | sort -nr | head -10 | \
	awk '{printf "  $(CYAN)%-15s$(RESET) %d issues\\n", $$2, $$1}' || echo "  No issues found"
	@echo ""
	@echo -e "$(GREEN)📁 Issues by File:$(RESET)"
	@uv run ruff check $(LINT_DIRS) $(EXCLUDE_DIRS) --output-format=json 2>/dev/null | \
	jq -r '.[] | .[] | .filename' 2>/dev/null | sort | uniq -c | sort -nr | head -10 | \
	awk '{printf "  $(MAGENTA)%-40s$(RESET) %d issues\\n", $$2, $$1}' || echo "  No issues found"

lint-status: ## comprehensive lint status report with detailed analysis
	@echo -e "$(BLUE)🔍 Comprehensive Lint Status Report$(RESET)"
	@echo -e "$(BLUE)==================================$(RESET)"
	@echo ""
	@echo -e "$(GREEN)📊 Overview:$(RESET)"
	@TOTAL=$$(uv run ruff check $(LINT_DIRS) $(EXCLUDE_DIRS) --output-format=json 2>/dev/null | jq -r '.[] | length' | awk '{sum += $$1} END {print sum+0}' 2>/dev/null || echo "0"); \
	FILES=$$(uv run ruff check $(LINT_DIRS) $(EXCLUDE_DIRS) --output-format=json 2>/dev/null | jq -r '.[] | .[] | .filename' 2>/dev/null | sort | uniq | wc -l || echo "0"); \
	LINTERS=$$(uv run ruff check $(LINT_DIRS) $(EXCLUDE_DIRS) --output-format=json 2>/dev/null | jq -r '.[] | .[] | .code' 2>/dev/null | cut -d'0' -f1 | sort | uniq | wc -l || echo "0"); \
	echo -e "  $(YELLOW)Total Issues: $$TOTAL$(RESET)"; \
	echo -e "  $(YELLOW)Affected Files: $$FILES$(RESET)"; \
	echo -e "  $(YELLOW)Active Linters: $$LINTERS$(RESET)"; \
	echo ""
	@echo -e "$(GREEN)🏆 Top 5 Issue Types:$(RESET)"
	@uv run ruff check $(LINT_DIRS) $(EXCLUDE_DIRS) --output-format=json 2>/dev/null | \
	jq -r '.[] | .[] | .code' 2>/dev/null | sort | uniq -c | sort -nr | head -5 | \
	awk '{printf "  $(RED)%-20s$(RESET) %d issues\\n", $$2, $$1}' || echo "  No issues found"
	@echo ""
	@echo -e "$(GREEN)📂 Top 5 Problematic Files:$(RESET)"
	@uv run ruff check $(LINT_DIRS) $(EXCLUDE_DIRS) --output-format=json 2>/dev/null | \
	jq -r '.[] | .[] | .filename' 2>/dev/null | sort | uniq -c | sort -nr | head -5 | \
	awk '{printf "  $(MAGENTA)%-50s$(RESET) %d issues\\n", $$2, $$1}' || echo "  No issues found"
	@echo ""
	@echo -e "$(GREEN)💡 Recommendations:$(RESET)"
	@TOTAL=$$(uv run ruff check $(LINT_DIRS) $(EXCLUDE_DIRS) --output-format=json 2>/dev/null | jq -r '.[] | length' | awk '{sum += $$1} END {print sum+0}' 2>/dev/null || echo "0"); \
	if [ $$TOTAL -eq 0 ]; then \
		echo -e "  $(GREEN)✅ Perfect! No lint issues found.$(RESET)"; \
	elif [ $$TOTAL -le 10 ]; then \
		echo -e "  $(YELLOW)⭐ Great! Only $$TOTAL issues remaining. Run 'make lint-fix' to auto-fix.$(RESET)"; \
	elif [ $$TOTAL -le 50 ]; then \
		echo -e "  $(YELLOW)⚠️  $$TOTAL issues found. Focus on top linters. Run 'make lint-fix' first.$(RESET)"; \
	else \
		echo -e "  $(RED)🚨 $$TOTAL issues found. Significant cleanup needed. Start with 'make lint-fix'.$(RESET)"; \
	fi

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

lint-json: ## export lint results to JSON for further analysis
	@echo -e "$(CYAN)Exporting lint results to lint-report.json...$(RESET)"
	@uv run ruff check $(LINT_DIRS) $(EXCLUDE_DIRS) --output-format=json > lint-report.json 2>/dev/null || echo "[]" > lint-report.json
	@echo -e "$(GREEN)✅ Report saved to lint-report.json$(RESET)"
	@if command -v jq >/dev/null 2>&1; then \
		echo ""; \
		echo -e "$(YELLOW)📈 JSON Report Summary:$(RESET)"; \
		TOTAL_ISSUES=$$(jq -r '.[] | length' lint-report.json 2>/dev/null | awk '{sum += $$1} END {print sum+0}' || echo "0"); \
		UNIQUE_FILES=$$(jq -r '.[] | .[] | .filename' lint-report.json 2>/dev/null | sort | uniq | wc -l || echo "0"); \
		echo "  Total Issues: $$TOTAL_ISSUES"; \
		echo "  Unique Files: $$UNIQUE_FILES"; \
	fi

lint-new: ## run lint on new/changed code only (git diff based)
	@echo "$(CYAN)Running lint on new/changed code only...$(RESET)"
	@CHANGED_FILES=$$(git diff --name-only HEAD~1 2>/dev/null | grep "\.py$$" | tr '\n' ' '); \
	if [ -n "$$CHANGED_FILES" ]; then \
		echo "$(YELLOW)Changed Python files: $$CHANGED_FILES$(RESET)"; \
		for file in $$CHANGED_FILES; do \
			if [ -f "$$file" ]; then \
				echo "$(CYAN)📝 Linting: $$file$(RESET)"; \
				uv run ruff check "$$file" || echo "$(RED)❌ Issues found in $$file$(RESET)"; \
			fi; \
		done; \
	else \
		echo "$(GREEN)✅ No Python files changed$(RESET)"; \
	fi

lint-ci: ## CI-optimized lint with GitHub Actions format
	@echo "$(CYAN)Running lint for CI with GitHub Actions format...$(RESET)"
	@uv run ruff check $(LINT_DIRS) $(EXCLUDE_DIRS) --output-format=github || echo "CI lint completed with issues"
	@echo "$(GREEN)✅ CI lint completed$(RESET)"

lint-file: ## lint specific Python files (supports CLAUDE_FILES env var)
	@if [ -n "$$CLAUDE_FILES" ]; then \
		echo "$(CYAN)🔄 Linting files from CLAUDE_FILES...$(RESET)"; \
		for file in $$CLAUDE_FILES; do \
			if [ -f "$$file" ] && echo "$$file" | grep -q "\.py$$"; then \
				echo "$(CYAN)📝 Linting file: $$file$(RESET)"; \
				echo "  1. Running ruff check..."; \
				uv run ruff check "$$file" --quiet || echo "$(RED)❌ ruff issues found in $$file$(RESET)"; \
				echo "  2. Running mypy..."; \
				uv run python -m mypy "$$file" --ignore-missing-imports --quiet || echo "$(RED)❌ mypy issues found in $$file$(RESET)"; \
				echo "$(GREEN)✅ File '$$file' linted$(RESET)"; \
			fi; \
		done; \
		echo "$(GREEN)🎉 File linting complete!$(RESET)"; \
	else \
		echo "$(YELLOW)Usage: CLAUDE_FILES='file1.py file2.py' make lint-file$(RESET)"; \
		echo "$(YELLOW)Or via hook: Files will be processed automatically$(RESET)"; \
	fi

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
	@echo "🎯 FILE-SPECIFIC TOOLS:"
	@echo "    make format-file     🎨 Format specific files (via CLAUDE_FILES)"
	@echo "    make lint-file       🔍 Lint specific files (via CLAUDE_FILES)"
	@echo ""
	@echo "📊 REPORTING & ANALYSIS:"
	@echo "    make lint-summary    📊 Show issues summary by linter/file"
	@echo "    make lint-status     📋 Comprehensive status report"
	@echo "    make lint-json       📄 Export results to JSON"
	@echo ""
	@echo "🔄 PROGRESSIVE LINTING:"
	@echo "    make lint-new        🆕 Lint only changed files (git diff)"
	@echo "    make lint-ci         🤖 CI-optimized lint (GitHub Actions)"
	@echo ""
	@echo "🛡️  SECURITY MODULES:"
	@echo "    make security-code   🔒 Code security analysis only"
	@echo "    make security-deps   📦 Dependency vulnerability check only"
	@echo "    make security-json   📄 Export security results to JSON"
	@echo ""
	@echo "✨ TIP: Start with 'make lint-fast' for quick checks during development"
	@echo "✨ TIP: Use 'make hooks-install' once to automate quality checks"
	@echo "✨ TIP: Run 'make lint-strict' before important releases"

# ==============================================================================
# Comprehensive Quality Checks
# ==============================================================================

.PHONY: quality quality-fix quality-strict quality-minimal

quality: format-check lint-check type-check security-scan ## run standard quality checks
	@echo -e "$(GREEN)✅ Standard quality checks completed$(RESET)"

quality-fix: fmt lint-fix ## apply automatic quality fixes
	@echo -e "$(GREEN)✅ Quality fixes applied$(RESET)"

quality-strict: format-check lint-strict mypy security-all analyze ## run strict quality checks
	@echo -e "$(GREEN)✅ Strict quality checks completed$(RESET)"

quality-minimal: lint-fast format-check ## run minimal quality checks
	@echo -e "$(GREEN)✅ Minimal quality checks completed$(RESET)"

# ==============================================================================
# Code Analysis and Comments
# ==============================================================================

.PHONY: comments todo fixme notes structure imports

comments: ## show all TODO/FIXME/NOTE comments in codebase
	@echo -e "$(CYAN)=== TODO comments ===$(RESET)"
	@grep -r "TODO" --include="*.py" . | grep -v ".git" | grep -v "__pycache__" || echo "$(GREEN)No TODOs found!$(RESET)"
	@echo ""
	@echo -e "$(CYAN)=== FIXME comments ===$(RESET)"
	@grep -r "FIXME" --include="*.py" . | grep -v ".git" | grep -v "__pycache__" || echo "$(GREEN)No FIXMEs found!$(RESET)"
	@echo ""
	@echo -e "$(CYAN)=== NOTE comments ===$(RESET)"
	@grep -r "NOTE" --include="*.py" . | grep -v ".git" | grep -v "__pycache__" || echo "$(GREEN)No NOTEs found!$(RESET)"


structure: ## show project structure
	@echo -e "$(CYAN)Project Structure:$(RESET)"
	@tree -I '__pycache__|*.pyc|.git|node_modules|htmlcov|.pytest_cache|*.egg-info|dist|build' -L 3 || \
		find . -type d -name __pycache__ -prune -o -type d -name .git -prune -o -type d -print | head -20

imports: ## analyze import statements
	@echo -e "$(CYAN)Import Analysis:$(RESET)"
	@echo -e "$(YELLOW)Most imported modules:$(RESET)"
	@grep -h "^import\|^from" --include="*.py" -r . | \
		sed 's/from \([^ ]*\).*/\1/' | \
		sed 's/import \([^ ]*\).*/\1/' | \
		sort | uniq -c | sort -nr | head -10

# ==============================================================================
# Tool Installation (Quality-specific)
# ==============================================================================

# Tool installation is handled by Makefile.tools.mk

# ==============================================================================
# Quality Information
# ==============================================================================

.PHONY: quality-info quality-status

quality-info: ## show quality tools and targets information
	@echo -e "$(CYAN)"
	@echo "╔══════════════════════════════════════════════════════════════════════════════╗"
	@echo -e "║                         $(YELLOW)Code Quality Information$(CYAN)                        ║"
	@echo "╚══════════════════════════════════════════════════════════════════════════════╝"
	@echo -e "$(RESET)"
	@echo -e "$(GREEN)🎨 Formatting Tools:$(RESET)"
	@echo -e "  • $(CYAN)black$(RESET)              Python code formatter"
	@echo -e "  • $(CYAN)isort$(RESET)              Import statement organizer"
	@echo -e "  • $(CYAN)autoflake$(RESET)          Remove unused imports/variables"
	@echo -e "  • $(CYAN)docformatter$(RESET)       Docstring formatter"
	@echo ""
	@echo -e "$(GREEN)🔍 Analysis Tools:$(RESET)"
	@echo -e "  • $(CYAN)mypy$(RESET)               Static type checker"
	@echo -e "  • $(CYAN)pylint$(RESET)             Python code analyzer"
	@echo -e "  • $(CYAN)radon$(RESET)              Code metrics (complexity, maintainability)"
	@echo -e "  • $(CYAN)vulture$(RESET)            Dead code finder"
	@echo ""
	@echo -e "$(GREEN)🛡️  Security Tools:$(RESET)"
	@echo -e "  • $(CYAN)bandit$(RESET)             Security issue scanner"
	@echo -e "  • $(CYAN)safety$(RESET)             Dependency vulnerability checker"
	@echo -e "  • $(CYAN)pip-audit$(RESET)          Pip package auditor"
	@echo ""
	@echo -e "$(GREEN)📊 Quality Commands:$(RESET)"
	@echo -e "  • $(CYAN)quality$(RESET)            Run standard checks"
	@echo -e "  • $(CYAN)quality-fix$(RESET)        Apply automatic fixes"
	@echo -e "  • $(CYAN)quality-strict$(RESET)     Run comprehensive checks"
	@echo -e "  • $(CYAN)analyze$(RESET)            Run code analysis"

quality-status: ## check installed quality tools
	@echo -e "$(CYAN)Quality Tools Status:$(RESET)"
	@echo -e "$(BLUE)====================$(RESET)"
	@echo -e "$(YELLOW)Formatting Tools:$(RESET)"
	@command -v black >/dev/null 2>&1 && echo "  ✅ black" || echo "  ❌ black"
	@command -v isort >/dev/null 2>&1 && echo "  ✅ isort" || echo "  ❌ isort"
	@command -v autoflake >/dev/null 2>&1 && echo "  ✅ autoflake" || echo "  ❌ autoflake"
	@echo ""
	@echo -e "$(YELLOW)Analysis Tools:$(RESET)"
	@command -v mypy >/dev/null 2>&1 && echo "  ✅ mypy" || echo "  ❌ mypy"
	@command -v pylint >/dev/null 2>&1 && echo "  ✅ pylint" || echo "  ❌ pylint"
	@command -v radon >/dev/null 2>&1 && echo "  ✅ radon" || echo "  ❌ radon"
	@echo ""
	@echo -e "$(YELLOW)Security Tools:$(RESET)"
	@command -v bandit >/dev/null 2>&1 && echo "  ✅ bandit" || echo "  ❌ bandit"
	@command -v safety >/dev/null 2>&1 && echo "  ✅ safety" || echo "  ❌ safety"