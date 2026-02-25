# Makefile for CI/CD tasks

.PHONY: help install lint lint-check format test security docker validate

# Default target
help:
	@echo "Veritix Python - CI/CD Tasks"
	@echo "============================"
	@echo "Available commands:"
	@echo "  make install     - Install development dependencies"
	@echo "  make format      - Auto-format code with black and isort"
	@echo "  make lint-check  - Check formatting (non-zero exit if changes needed)"
	@echo "  make lint        - Run code formatting and linting"
	@echo "  make test        - Run tests with coverage"
	@echo "  make security    - Run security scans"
	@echo "  make docker      - Build and test Docker image"
	@echo "  make validate    - Run full CI validation"
	@echo "  make clean       - Clean build artifacts"

# Install development dependencies# Makefile for Veritix Python

.PHONY: help dev-setup run lint lint-check format test test-docker \
        security docker docker-up docker-down migrate validate clean check

# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------
help:
	@echo "Veritix Python — available targets"
	@echo "==================================="
	@echo "  make dev-setup    Copy .env.example → .env (if absent), create venv, install deps"
	@echo "  make run          Start the app with uvicorn (hot-reload)"
	@echo "  make format       Auto-format code with black and isort"
	@echo "  make lint-check   Check formatting — exits non-zero if changes are needed"
	@echo "  make lint         Run black, isort, and flake8 checks"
	@echo "  make test         Run pytest with coverage"
	@echo "  make test-docker  Run tests inside Docker with a live Postgres container"
	@echo "  make security     Run safety and bandit security scans"
	@echo "  make docker       Build Docker image and smoke-test it"
	@echo "  make docker-up    docker compose up -d"
	@echo "  make docker-down  docker compose down"
	@echo "  make migrate      Run alembic upgrade head"
	@echo "  make validate     Run the full CI validation script"
	@echo "  make clean        Remove build artefacts and caches"

# ---------------------------------------------------------------------------
# Local development setup (idempotent — safe to run more than once)
# ---------------------------------------------------------------------------
dev-setup:
	@echo "→ Copying .env.example to .env (skipped if .env already exists)..."
	@cp -n .env.example .env || true
	@echo "→ Creating virtual environment at .venv (skipped if already exists)..."
	@python3 -m venv .venv || true
	@echo "→ Installing dependencies into .venv..."
	@.venv/bin/pip install --upgrade pip
	@.venv/bin/pip install -r requirements.txt
	@echo ""
	@echo "✅ Dev environment ready."
	@echo "   Activate with:  source .venv/bin/activate"
	@echo "   Then run:       make run"

# ---------------------------------------------------------------------------
# Run the application
# ---------------------------------------------------------------------------
run:
	uvicorn src.main:app --reload

# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------
format:
	black src/ tests/
	isort src/ tests/

# Check-only — exits non-zero when files need changes (used in CI)
lint-check:
	black --check src/ tests/
	isort --check-only --diff src/ tests/

# ---------------------------------------------------------------------------
# Linting
# ---------------------------------------------------------------------------
lint:
	@echo "Running code formatting checks..."
	black --check .
	isort --check-only --diff .
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

# ---------------------------------------------------------------------------
# Testing
# ---------------------------------------------------------------------------
test:
	@echo "Running tests with coverage..."
	SKIP_MODEL_TRAINING=true pytest --cov=src --cov-report=term-missing --cov-fail-under=80

# Run tests in Docker with a live Postgres instance
test-docker:
	docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit

# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------
security:
	@echo "Running security scans..."
	safety check --full-report
	bandit -r src/ -f json -o bandit-report.json

# ---------------------------------------------------------------------------
# Docker
# ---------------------------------------------------------------------------
# Build image and smoke-test it
docker:
	@echo "Building Docker image..."
	docker build -t veritix-python-app:local .
	@echo "Smoke-testing Docker container..."
	docker run --rm veritix-python-app:local python -c "import src.main; print('✅ Application imports successfully')"

# Start the full stack (app + Postgres) in the background
docker-up:
	docker compose up -d

# Tear down the stack
docker-down:
	docker compose down

# ---------------------------------------------------------------------------
# Database migrations
# ---------------------------------------------------------------------------
migrate:
	alembic upgrade head

# ---------------------------------------------------------------------------
# CI / validation helpers
# ---------------------------------------------------------------------------
validate:
	@echo "Running full CI validation..."
	./scripts/validate-ci.sh

check: lint-check lint test security

# ---------------------------------------------------------------------------
# Clean
# ---------------------------------------------------------------------------
clean:
	@echo "Cleaning build artefacts..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -delete
	rm -f .coverage coverage.xml bandit-report.json
	rm -rf build/ dist/ *.egg-info/
	docker rmi veritix-python-app:local veritix-python-app:local-test 2>/dev/null || true
install:
	pip install -r requirements.txt

# Auto-format code (fix in place)
format:
	black src/ tests/
	isort src/ tests/

# Check formatting only — exits non-zero if files need changes
lint-check:
	black --check src/ tests/
	isort --check-only --diff src/ tests/

# Code formatting and linting
lint:
	@echo "Running code formatting checks..."
	black --check .
	isort --check-only --diff .
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

# Run tests
test:
	@echo "Running tests with coverage..."
	SKIP_MODEL_TRAINING=true pytest --cov=src --cov-report=term-missing --cov-fail-under=80

# Security scanning
security:
	@echo "Running security scans..."
	safety check --full-report
	bandit -r src/ -f json -o bandit-report.json

# Docker build and test
docker:
	@echo "Building Docker image..."
	docker build -t veritix-python-app:local .
	@echo "Testing Docker container..."
	docker run --rm veritix-python-app:local python -c "import src.main; print('✅ Application imports successfully')"

# Full CI validation
validate:
	@echo "Running full CI validation..."
	./scripts/validate-ci.sh

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -delete
	rm -f .coverage coverage.xml
	rm -f bandit-report.json
	rm -rf build/ dist/ *.egg-info/
	docker rmi veritix-python-app:local veritix-python-app:local-test 2>/dev/null || true

# Run tests in Docker with PostgreSQL
test-docker:
	docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit

# Run all checks
check: lint-check lint test security

# Development setup
dev-setup: install format lint test
	@echo "Development environment ready!"