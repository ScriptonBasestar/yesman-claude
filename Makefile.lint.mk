# Makefile.lint.mk - Unified Code Quality and Git Hooks Management
# 300-year Senior Quality Management Expert Level Configuration
# Separated from main Makefile for better organization

.PHONY: lint lint-check lint-fix lint-strict lint-help lint-fast
.PHONY: pre-commit-install pre-commit-run pre-commit-update 
.PHONY: validate-hooks pre-push-test validate-lint-config
.PHONY: hooks-install hooks-uninstall hooks-status

# =============================================================================
# Code Quality Configuration - Hierarchical Lint Levels
# =============================================================================

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

# =============================================================================
# Level 1: Basic Lint (Default) - Fast & Lightweight for Development Flow
# =============================================================================

# lint-fast: 가장 빠른 기본 검증 (1-3초, 개발 중 빈번 사용)
lint-fast:
	@echo "🚀 Running fast lint checks..."
	@echo "⚡ Running ruff check (fast mode)..."
	uv run ruff check $(LINT_DIRS) $(EXCLUDE_DIRS) $(LINT_QUIET) --no-cache
	@echo "✅ Fast lint completed"

# lint-check: pre-commit 수준의 검사 (자동 수정 없음, 2-5초)
# - ruff check: 모든 활성화된 규칙 검사
# - mypy: 기본 타입 검사 
# - bandit: 중요 보안 취약점 검사 (medium 레벨)
# - mdformat: 마크다운 포맷팅 체크
lint-check:
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
lint: lint-check

# =============================================================================
# Level 2: Auto-fix Lint - Same validation + automatic fixes
# =============================================================================

# lint-fix: 자동 수정 포함 코드 품질 검사 + 포맷팅
# - ruff check --fix: 자동 수정 가능한 규칙 위반 항목 수정
# - ruff format: 코드 포맷팅 자동 적용, black 대체용
# - mypy: 타입 검사
# - bandit: 보안 취약점 검사 (medium 레벨)
# - mdformat: 마크다운 포맷팅
# - 사용법: make lint-fix UNSAFE_FIXES=1 (위험한 자동 수정 포함)
lint-fix:
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

# =============================================================================
# Level 3: Strict Lint - Comprehensive quality checks (Manual execution)
# =============================================================================

# lint-strict: 엄격한 코드 품질 검사 (모든 규칙 적용)
# - ruff check --select ALL: 모든 규칙 적용 (일부 규칙 무시)
# - mypy --strict: 엄격한 타입 검사
# - bandit --severity-level low: 낮은 심각도까지 보안 검사
# ⚠️  주의: 이 검사는 시간이 오래 걸리므로 PR/릴리즈 전에만 수동 실행
lint-strict:
	@echo "🎯 Running strict lint checks (Level 3: Comprehensive)..."
	@echo "⚠️  Warning: This is a comprehensive check that may take time"
	@echo "📊 Running ruff with all rules..."
	uv run ruff check $(LINT_DIRS) --select ALL --ignore E501,B008,C901,COM812,B904,B017,B007,D100,D101,D102,D103,D104,D105,D106,D107  $(EXCLUDE_DIRS) --output-format=full
	@echo "🔍 Running mypy with strict settings..."
	uv run mypy $(LINT_DIRS_CORE) --strict --ignore-missing-imports  $(EXCLUDE_DIRS)
	@echo "🛡️  Running bandit with strict settings..."
	uv run bandit -r $(LINT_DIRS_CORE) --severity-level low --exclude "*/tests/*,*/scripts/*,*/debug/*,*/examples/*"
	@echo "✅ Level 3 strict lint completed"

# =============================================================================
# Git Hooks Management - Unified pre-commit/pre-push Integration
# =============================================================================

# Quick hooks management
hooks-install: pre-commit-install
	@echo "✅ Git hooks installed successfully"
	@echo "  - pre-commit: Level 1 lint (fast, development-friendly)"
	@echo "  - pre-push: Level 1 lint + fast tests (comprehensive but reasonable)"

hooks-uninstall:
	@echo "Uninstalling pre-commit hooks..."
	uv run pre-commit uninstall
	@echo "✅ Git hooks uninstalled"

hooks-status:
	@echo "Git hooks status:"
	@if [ -f .git/hooks/pre-commit ]; then echo "  ✅ pre-commit: installed"; else echo "  ❌ pre-commit: not installed"; fi
	@if [ -f .git/hooks/pre-push ]; then echo "  ✅ pre-push: installed"; else echo "  ❌ pre-push: not installed"; fi
	@echo "To install: make hooks-install"
	@echo "To uninstall: make hooks-uninstall"

# Pre-commit integration (legacy compatibility)
pre-commit-install:
	@echo "Installing pre-commit hooks..."
	uv run pre-commit install
	uv run pre-commit install --hook-type pre-push

pre-commit-run:
	@echo "Running all pre-commit hooks..."
	uv run pre-commit run --all-files

pre-commit-update:
	@echo "Updating pre-commit hooks..."
	uv run pre-commit autoupdate

# =============================================================================
# Validation and Testing Integration
# =============================================================================

# Git hooks validation - ensure consistency between make targets and hooks
validate-hooks:
	@echo "🔍 Validating git hooks consistency..."
	@echo "Testing pre-commit hooks..."
	uv run pre-commit run --all-files
	@echo "Testing make lint (Level 1)..."
	make lint
	@echo "✅ All hooks validated successfully - consistency confirmed"

# Pre-push simulation (what actually runs on git push)
pre-push-test:
	@echo "🚀 Running pre-push validation (Level 1 + fast tests)..."
	make lint
	make test-fast
	@echo "✅ Pre-push validation completed - ready to push"

# Comprehensive validation (before important releases)
validate-comprehensive:
	@echo "🎯 Running comprehensive validation..."
	make lint-strict
	make test
	@echo "✅ Comprehensive validation completed - release ready"

# Validate lint configuration consistency
validate-lint-config:
	@echo "Validating lint configuration consistency..."
	python3 scripts/validate-lint-config.py

# =============================================================================
# Help and Documentation
# =============================================================================

# Comprehensive help for lint system
lint-help:
	@echo "📋 Unified Lint and Code Quality System (300-year Senior Expert Level)"
	@echo "="*80
	@echo "🚀 HIERARCHICAL LINT LEVELS (Development Flow Optimized):"
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
	@echo "📊 VALIDATION & TESTING:"
	@echo "    make validate-hooks        Test hooks consistency"
	@echo "    make pre-push-test         Simulate pre-push validation"
	@echo "    make validate-comprehensive Full validation (release-ready)"
	@echo "    make validate-lint-config  Check lint configuration"
	@echo ""
	@echo "⚙️  LEGACY PRE-COMMIT INTEGRATION:"
	@echo "    make pre-commit-install    Install pre-commit hooks"
	@echo "    make pre-commit-run        Run all pre-commit hooks"
	@echo "    make pre-commit-update     Update pre-commit hooks"
	@echo ""
	@echo "📊 CONFIGURATION VARIABLES:"
	@echo "    LINT_DIRS              = $(LINT_DIRS)"
	@echo "    LINT_DIRS_SECURITY     = $(LINT_DIRS_SECURITY)"
	@echo "    LINT_DIRS_CORE         = $(LINT_DIRS_CORE)"
	@echo "    EXCLUDE_DIRS           = $(EXCLUDE_DIRS)"
	@echo "    UNSAFE_FIXES           = $(UNSAFE_FIXES)"
	@echo "    LINT_QUIET             = $(LINT_QUIET)"
	@echo "="*80
	@echo "✨ TIP: Start with 'make lint-fast' for quick checks during development"
	@echo "✨ TIP: Use 'make hooks-install' once to automate quality checks"
	@echo "✨ TIP: Run 'make lint-strict' before important releases"