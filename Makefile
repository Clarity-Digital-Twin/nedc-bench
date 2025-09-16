# NEDC-BENCH Makefile - 2025 Edition
# Banger commands for EEG benchmarking development

.PHONY: help install dev test lint format clean run benchmark docker docs

# Colors for terminal output
CYAN := \033[0;36m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(CYAN)╔════════════════════════════════════════╗$(NC)"
	@echo "$(CYAN)║     NEDC-BENCH Development Tools       ║$(NC)"
	@echo "$(CYAN)╚════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(GREEN)Available commands:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(CYAN)Quick Start:$(NC) make install dev"

# ==================== Installation ====================

install: ## Install production dependencies with UV
	@echo "$(GREEN)Installing production dependencies...$(NC)"
	uv pip install -e .
	@echo "$(GREEN)✓ Production environment ready!$(NC)"

dev: ## Set up complete development environment
	@echo "$(GREEN)Setting up development environment...$(NC)"
	uv pip install -e ".[dev]"
	pre-commit install
	@echo "$(GREEN)✓ Development environment ready!$(NC)"
	@echo "$(YELLOW)Run 'make test' to verify setup$(NC)"

update: ## Update all dependencies to latest versions
	@echo "$(GREEN)Updating dependencies...$(NC)"
	uv pip install --upgrade -e ".[dev]"
	pre-commit autoupdate
	@echo "$(GREEN)✓ Dependencies updated!$(NC)"

# ==================== Testing ====================

test: ## Run all tests with coverage (project only)
	@echo "$(GREEN)Running tests...$(NC)"
	pytest -v --cov=nedc_bench --cov-report=term-missing

test-fast: ## Run tests in parallel (fast)
	@echo "$(GREEN)Running tests in parallel...$(NC)"
	pytest -n auto -v --cov=nedc_bench --cov-report=term-missing

test-slow: ## Run all tests including slow ones
	@echo "$(GREEN)Running all tests (including slow)...$(NC)"
	pytest -v --cov=nedc_bench -m ""

test-watch: ## Run tests in watch mode
	@echo "$(GREEN)Starting test watcher...$(NC)"
	pytest-watch -- -v

benchmark: ## Run performance benchmarks
	@echo "$(GREEN)Running benchmarks...$(NC)"
	pytest benchmarks/ --benchmark-only --benchmark-autosave

# ==================== Code Quality ====================

lint: ## Run all linters (ruff + mypy)
	@echo "$(GREEN)Running linters...$(NC)"
	ruff check .
	mypy -p nedc_bench

lint-fix: ## Auto-fix linting issues
	@echo "$(GREEN)Auto-fixing code issues...$(NC)"
	ruff check --fix .
	ruff format .

format: ## Format code with Ruff
	@echo "$(GREEN)Formatting code...$(NC)"
	ruff format .

typecheck: ## Run type checking with mypy
	@echo "$(GREEN)Type checking...$(NC)"
	mypy -p nedc_bench --show-error-codes

pre-commit: ## Run pre-commit hooks on all files
	@echo "$(GREEN)Running pre-commit hooks...$(NC)"
	pre-commit run --all-files

# ==================== NEDC Tool ====================

run-nedc: ## Run original NEDC evaluation tool demo
	@echo "$(GREEN)Running NEDC evaluation demo...$(NC)"
	./run_nedc.sh nedc_eeg_eval/v6.0.0/data/lists/ref.list \
	              nedc_eeg_eval/v6.0.0/data/lists/hyp.list

nedc-help: ## Show NEDC tool help
	./run_nedc.sh --help

# ==================== Development ====================

shell: ## Start interactive Python shell with project loaded
	@echo "$(GREEN)Starting Python shell...$(NC)"
	uv run python

notebook: ## Start Jupyter notebook for exploration
	@echo "$(GREEN)Starting Jupyter notebook...$(NC)"
	uv run jupyter notebook

docs-serve: ## Serve documentation locally
	@echo "$(GREEN)Starting documentation server...$(NC)"
	mkdocs serve

docs-build: ## Build documentation
	@echo "$(GREEN)Building documentation...$(NC)"
	mkdocs build

# ==================== Docker ====================

docker-build: ## Build Docker image
	@echo "$(GREEN)Building Docker image...$(NC)"
	docker build -t nedc-bench:latest .

docker-run: ## Run Docker container
	@echo "$(GREEN)Running Docker container...$(NC)"
	docker run -it --rm -v $(PWD):/app nedc-bench:latest

docker-test: ## Run tests in Docker
	@echo "$(GREEN)Running tests in Docker...$(NC)"
	docker run --rm nedc-bench:latest pytest

# ==================== Cleanup ====================

clean: ## Clean build artifacts and caches
	@echo "$(RED)Cleaning build artifacts...$(NC)"
	rm -rf build/ dist/ *.egg-info
	rm -rf .pytest_cache .mypy_cache .ruff_cache
	rm -rf htmlcov/ .coverage coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "$(GREEN)✓ Clean!$(NC)"

clean-all: clean ## Deep clean including virtual environments
	@echo "$(RED)Deep cleaning...$(NC)"
	rm -rf .venv venv
	rm -rf node_modules
	rm -rf .tox
	@echo "$(GREEN)✓ Squeaky clean!$(NC)"

# ==================== CI/CD ====================

ci: ## Run full CI pipeline locally
	@echo "$(GREEN)Running CI pipeline...$(NC)"
	make lint
	make typecheck
	make test
	@echo "$(GREEN)✓ CI pipeline passed!$(NC)"

release: ## Prepare release (bump version, tag, etc.)
	@echo "$(YELLOW)Preparing release...$(NC)"
	@echo "Not implemented yet"

# ==================== Utilities ====================

tree: ## Show project structure (excluding vendor/cache)
	@tree -I 'nedc_eeg_eval|__pycache__|.git|.venv|*.egg-info|htmlcov|.mypy_cache|.pytest_cache'

loc: ## Count lines of code (excluding vendor)
	@echo "$(GREEN)Lines of code:$(NC)"
	@find . -name "*.py" -not -path "./nedc_eeg_eval/*" -not -path "./.venv/*" | xargs wc -l | tail -1

todo: ## Show all TODOs in codebase
	@echo "$(GREEN)TODOs in codebase:$(NC)"
	@grep -r "TODO\|FIXME\|HACK" --exclude-dir=nedc_eeg_eval --exclude-dir=.git --exclude-dir=.venv . || echo "No TODOs found!"

deps: ## Show dependency tree
	@echo "$(GREEN)Dependency tree:$(NC)"
	uv pip list

# Default target
.DEFAULT_GOAL := help
